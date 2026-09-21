"""Rentabilidad por operación: coste de entrada y valor de salida de cada jugador.

Una posición se abre cuando un jugador entra en un equipo (reparto inicial, fichaje o
cambio) y se cierra cuando sale. La ganancia realizada es la diferencia; las posiciones
todavía abiertas se valoran a precio de mercado de hoy (ganancia latente).

Los jugadores del reparto inicial se valoran al precio del día del reset, que es el mismo
criterio con el que Biwenger fijó el saldo de partida, así que ambas cuentas son coherentes.
"""
from .initial import initial_squads, yymmdd


def _open(positions, uid, pid, cost, date, how):
    positions[pid] = {"user": uid, "player": pid, "cost": cost, "date_in": date, "how_in": how}


def _reparte(positions, uid, pids, total, when, mkt):
    """Reparte un coste conjunto entre varios jugadores, en proporción a su precio."""
    if not pids:
        return
    pesos = [mkt(p) for p in pids]
    suma = sum(pesos) or len(pids)
    if not sum(pesos):
        pesos = [1] * len(pids)
    repartido = 0
    for i, pid in enumerate(pids):
        cost = total - repartido if i == len(pids) - 1 else total * pesos[i] // suma
        repartido += cost
        _open(positions, uid, pid, cost, when, "cambio")


def compute_positions(season_events, squads, reset_ts, precio, altas=None):
    """Devuelve (operaciones cerradas, posiciones abiertas)."""
    init = initial_squads(season_events, squads, reset_ts)
    altas = altas or {}

    positions: dict[int, dict] = {}
    closed: list[dict] = []

    # El lote inicial de cada usuario se abre en SU fecha de alta, no todos a la vez: un mismo
    # jugador puede tocarle primero a uno en el reparto y luego a otro que entra más tarde.
    agenda = [(altas.get(uid, reset_ts), 0, ("reparto", uid, sorted(pids))) for uid, pids in init.items()]
    agenda += [(e["date"], 1, ("evento", e, None)) for e in season_events]
    agenda.sort(key=lambda it: (it[0], it[1]))

    def close(uid, pid, date, revenue, how):
        p = positions.pop(pid, None)
        if p is None or p["user"] != uid:
            # El jugador no estaba donde creíamos: registramos la venta sin coste conocido.
            p = {"user": uid, "player": pid, "cost": None, "date_in": None, "how_in": "desconocido"}
        closed.append({**p, "date_out": date, "revenue": revenue, "how_out": how,
                       "profit": None if p["cost"] is None else revenue - p["cost"]})

    for when, _, (clase, a, b) in agenda:
        if clase == "reparto":
            for pid in b:
                _open(positions, a, pid, precio(pid, yymmdd(when)), when, "reparto")
            continue
        e = a
        t, c = e["type"], e["content"]
        if t in ("transfer", "market"):
            for x in c:
                kind = x.get("type") or t
                if x.get("from"):
                    close(x["from"]["id"], x["player"], when, x["amount"], kind)
                if x.get("to"):
                    _open(positions, x["to"]["id"], x["player"], x["amount"], when, kind)
        elif t == "adminTransfer":
            for x in c:
                if x.get("from"):
                    close(x["from"]["id"], x["player"], when, x["amount"], "admin")
                _open(positions, x["to"]["id"], x["player"], x["amount"], when, "admin")
        elif t == "exchange":
            # Un cambio se valora a precio de mercado del día: cierra las posiciones que salen
            # y abre las que entran. El dinero que cambia de manos se reparte entre los
            # jugadores recibidos, de modo que quien paga carga ese coste en su nueva posición.
            day = yymmdd(when)
            mkt = lambda pid: precio(pid, day)
            src, dst = c["from"]["id"], c["to"]["id"]
            neto = c["amount"] - c["requestedAmount"]  # efectivo que va de `src` a `dst`
            salen = {src: c["offeredPlayers"], dst: c["requestedPlayers"]}
            for uid, pids in salen.items():
                for pid in pids:
                    close(uid, pid, when, mkt(pid), "cambio")
            # Lo que cuesta cada jugador que llega es lo que su nuevo dueño entregó por él:
            # el valor de los jugadores que dio más el efectivo que puso.
            for uid, llegan, caja in ((src, c["requestedPlayers"], neto), (dst, c["offeredPlayers"], -neto)):
                total = sum(mkt(p) for p in salen[uid]) + caja
                _reparte(positions, uid, llegan, total, when, mkt)

    return closed, list(positions.values())


def summarize(closed, open_positions, current_price):
    """Agrega por usuario: realizado, latente y total."""
    by_user: dict[int, dict] = {}

    def row(uid):
        return by_user.setdefault(uid, {"realizado": 0, "latente": 0, "n_cerradas": 0,
                                        "n_abiertas": 0, "aciertos": 0, "sin_coste": 0})

    for t in closed:
        r = row(t["user"])
        r["n_cerradas"] += 1
        if t["profit"] is None:
            r["sin_coste"] += 1
        else:
            r["realizado"] += t["profit"]
            r["aciertos"] += t["profit"] > 0
    for p in open_positions:
        r = row(p["user"])
        r["n_abiertas"] += 1
        r["latente"] += (current_price(p["player"]) or 0) - p["cost"]
    for r in by_user.values():
        r["total"] = r["realizado"] + r["latente"]
    return by_user
