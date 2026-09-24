"""Actualización diaria: descarga, calcula y guarda el estado de la liga.

Uso: python -m scraper.daily
"""
import json
from datetime import date, datetime
from pathlib import Path

from .balances import current_season_events, money_flows
from .client import BiwengerClient
from .fetch import RAW, fetch_all, load_cached, load_daily_prices, precio_lookup
from .initial import initial_squads, start_dates, yymmdd
from .series import serie_diaria
from .trades import compute_positions, summarize

DATA = RAW.parent
CAPITAL_INICIAL = 20_000_000  # patrimonio de partida fijado por la liga tras el reset


def _load(path: Path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")


def run(offline: bool = False) -> dict:
    """Con `offline` se recalcula todo sobre la última descarga, sin llamar a la API."""
    c = None if offline else BiwengerClient.from_env()
    d = load_cached() if offline else fetch_all(c)
    if offline:  # recuperamos quiénes somos y nuestro saldo real de la última ejecución
        previo = _load(DATA / "liga.json", {})
        mi_id, mi_saldo = previo.get("usuario_propio"), previo.get("saldo_real_propio")
    else:
        mi_id, mi_saldo = c.user_id, d["my_balance"]
    board, squads = d["board"], {int(k): v for k, v in d["squads"].items()}
    players = d["players"]

    reset_ts = max(e["date"] for e in board if e["type"] == "leagueReset")
    season = current_season_events(board)
    init = initial_squads(season, squads, reset_ts)
    altas = start_dates(season, reset_ts)

    # Todo jugador que haya pasado por alguna plantilla: hace falta su precio de cada día
    # para poder valorar los equipos hacia atrás.
    relevantes = {p for s in init.values() for p in s}
    relevantes |= {p["id"] for sq in squads.values() for p in sq}
    for e in season:
        if e["type"] in ("transfer", "market", "adminTransfer"):
            relevantes |= {x["player"] for x in e["content"]}
        elif e["type"] == "exchange":
            relevantes |= set(e["content"]["offeredPlayers"] + e["content"]["requestedPlayers"])

    hoy = yymmdd(int(datetime.now().timestamp()))
    precios_hoy = {p: players[str(p)]["price"] for p in relevantes if str(p) in players}
    criticos = {p for s in init.values() for p in s}
    precio = precio_lookup(load_daily_prices(c, relevantes, yymmdd(reset_ts), hoy,
                                             precios_hoy, criticos))

    def current_price(pid):
        ficha = players.get(str(pid))
        return ficha["price"] if ficha else precio(pid, hoy)

    flow = money_flows(season)
    # Dinero que no viene de comprar y vender: primas y bonus de jornada.
    premios = money_flows([e for e in season if e["type"] in ("bonus", "roundFinished")])
    # Solo lo cobrado por rendimiento en las jornadas. Se mira aparte porque la prima inicial
    # es igual para todos y compararla no dice nada.
    jornadas = money_flows([e for e in season if e["type"] == "roundFinished"])
    # Gasto en blindar jugadores subiendo su cláusula: sale del saldo y no es una operación.
    clausulas = money_flows([e for e in season if e["type"] == "clauseIncrement"])
    day0 = yymmdd(reset_ts)
    # Un jugador del reparto valorado en cero significa que falta su precio: falsearía el
    # saldo de partida de su dueño, así que se avisa en vez de dejarlo pasar.
    sin_precio = [(uid, p) for uid, ps in init.items()
                  for p in ps if precio(p, yymmdd(altas.get(uid, reset_ts))) == 0]

    closed, openpos = compute_positions(season, squads, reset_ts, precio, altas)
    perf = summarize(closed, openpos, current_price)

    today = date.today().isoformat()
    users = []
    for s in d["league"]["standings"]:
        uid = s["id"]
        dia = yymmdd(altas.get(uid, reset_ts))
        v0 = sum(precio(p, dia) for p in init.get(uid, ()))
        balance = CAPITAL_INICIAL - v0 + flow.get(uid, 0)
        p = perf.get(uid, {})
        users.append({
            "id": uid, "nombre": s["name"], "saldo": balance, "valor_equipo": s["teamValue"],
            "patrimonio": balance + s["teamValue"], "variacion_dia": s["teamValueInc"],
            "puntos": s["points"], "posicion": s["position"], "jugadores": s["teamSize"],
            "valor_equipo_inicial": v0, "saldo_inicial": CAPITAL_INICIAL - v0,
            "realizado": p.get("realizado", 0), "latente": p.get("latente", 0),
            "beneficio_total": p.get("total", 0), "operaciones_cerradas": p.get("n_cerradas", 0),
            "premios": premios.get(uid, 0), "gasto_clausulas": clausulas.get(uid, 0),
            "bonus_jornadas": jornadas.get(uid, 0),
            "saldo_verificado": uid == mi_id and balance == mi_saldo,
            # El patrimonio debe salir de: capital inicial + premios - cláusulas + lo ganado operando.
            "descuadre": (balance + s["teamValue"]) - (CAPITAL_INICIAL + premios.get(uid, 0)
                                                       + clausulas.get(uid, 0) + p.get("total", 0)),
        })
    users.sort(key=lambda u: -u["patrimonio"])

    nombres = {s["id"]: s["nombre"] for s in users}
    nom_jug = lambda pid: players.get(str(pid), {}).get("name", f"#{pid}")
    _save(DATA / "liga.json", {
        "actualizado": today, "liga": d["league"]["name"], "reset": reset_ts,
        "saldo_real_propio": mi_saldo, "usuario_propio": mi_id, "usuarios": users,
    })
    _save(DATA / "operaciones.json", {
        "cerradas": [{**t, "usuario": nombres.get(t["user"], t["user"]), "jugador": nom_jug(t["player"])} for t in closed],
        "abiertas": [{**p, "usuario": nombres.get(p["user"], p["user"]), "jugador": nom_jug(p["player"]),
                      "valor_hoy": current_price(p["player"]),
                      "latente": current_price(p["player"]) - p["cost"]} for p in openpos],
    })

    # El histórico se recalcula entero cada vez, así que cubre desde el primer día de liga
    # y se corrige solo si algún día se afina el modelo.
    hist = serie_diaria(season, squads, reset_ts, altas,
                        {u["id"]: u["saldo_inicial"] for u in users},
                        precio, int(datetime.now().timestamp()))
    _save(DATA / "historico.json", hist)

    return {"users": users, "closed": closed, "open": openpos, "dias": len(hist),
            "my_balance": mi_saldo, "my_id": mi_id, "sin_precio": sin_precio}


if __name__ == "__main__":
    import sys

    r = run(offline="--offline" in sys.argv)
    ok = next((u for u in r["users"] if u["id"] == r["my_id"]), None)
    print(f"Saldo propio calculado {'COINCIDE' if ok and ok['saldo_verificado'] else 'NO COINCIDE'} con el real ({r['my_balance']:,})")
    print(f"{'usuario':30} {'saldo':>12} {'equipo':>12} {'patrimonio':>12} {'premios':>11} {'realizado':>12} {'latente':>12} {'descuadre':>10}")
    for u in r["users"]:
        print(f"{u['nombre'][:30]:30} {u['saldo']:>12,} {u['valor_equipo']:>12,} {u['patrimonio']:>12,} {u['premios']:>11,} {u['realizado']:>12,} {u['latente']:>12,} {u['descuadre']:>10,}")
    print(f"\noperaciones cerradas: {len(r['closed'])} | posiciones abiertas: {len(r['open'])} | dias en historico: {r['dias']}")
    if r["sin_precio"]:
        print(f"AVISO: {len(r['sin_precio'])} jugadores del reparto sin precio -> {r['sin_precio'][:6]}")
    else:
        print("Todos los jugadores del reparto tienen precio en su fecha de inicio")
