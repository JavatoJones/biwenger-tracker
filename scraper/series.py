"""Patrimonio de cada mánager día a día, reconstruido desde el reparto inicial.

No basta con guardar una foto diaria: el histórico se recalcula entero en cada ejecución
replicando quién era dueño de cada jugador cada día y cuánto valía ese día. Así la serie
existe desde el primer día de liga, no desde que se montó el tracker, y se corrige sola si
algún día se afina el modelo.
"""
from datetime import date, datetime, timedelta, timezone

from .balances import money_flows
from .initial import initial_squads


def dia_num(d: date) -> int:
    """La fecha en el formato aaammdd que usa Biwenger en su histórico de precios."""
    return (d.year % 100) * 10000 + d.month * 100 + d.day


def rango_dias(desde_ts: int, hasta_ts: int) -> list[date]:
    ini = datetime.fromtimestamp(desde_ts, tz=timezone.utc).date()
    fin = datetime.fromtimestamp(hasta_ts, tz=timezone.utc).date()
    return [ini + timedelta(days=i) for i in range((fin - ini).days + 1)]


def _fin_del_dia(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc).timestamp())


def _agenda(season_events, init, altas, reset_ts):
    """Reparto inicial de cada uno en su fecha de alta, mezclado con los eventos."""
    items = [(altas.get(uid, reset_ts), 0, ("reparto", uid, sorted(pids))) for uid, pids in init.items()]
    items += [(e["date"], 1, ("evento", e, None)) for e in season_events]
    items.sort(key=lambda it: (it[0], it[1]))
    return items


def serie_diaria(season_events, squads, reset_ts, altas, saldo_inicial, precio_dia, hasta_ts):
    """Devuelve [{fecha, usuarios:[{id, saldo, valor_equipo, patrimonio}]}] para cada día.

    `saldo_inicial` es {uid: saldo de partida}; `precio_dia(pid, aaammdd)` da el precio.
    """
    init = initial_squads(season_events, squads, reset_ts)
    agenda = _agenda(season_events, init, altas, reset_ts)
    dias = rango_dias(reset_ts, hasta_ts)

    dueno: dict[int, int] = {}
    i, salida = 0, []

    for d in dias:
        corte = _fin_del_dia(d)
        while i < len(agenda) and agenda[i][0] <= corte:
            _, _, (clase, a, b) = agenda[i]
            i += 1
            if clase == "reparto":
                for pid in b:
                    dueno[pid] = a
                continue
            t, c = a["type"], a["content"]
            if t in ("transfer", "market"):
                for x in c:
                    if x.get("from") and dueno.get(x["player"]) == x["from"]["id"]:
                        dueno.pop(x["player"], None)
                    if x.get("to"):
                        dueno[x["player"]] = x["to"]["id"]
            elif t == "adminTransfer":
                for x in c:
                    dueno[x["player"]] = x["to"]["id"]
            elif t == "exchange":
                for pid in c["offeredPlayers"]:
                    dueno[pid] = c["to"]["id"]
                for pid in c["requestedPlayers"]:
                    dueno[pid] = c["from"]["id"]

        num = dia_num(d)
        valor: dict[int, int] = {}
        for pid, uid in dueno.items():
            valor[uid] = valor.get(uid, 0) + precio_dia(pid, num)

        flujos = money_flows([e for e in season_events if e["date"] <= corte])
        usuarios = []
        for uid, base in saldo_inicial.items():
            if altas.get(uid, reset_ts) > corte:
                continue  # todavía no se había incorporado
            saldo = base + flujos.get(uid, 0)
            equipo = valor.get(uid, 0)
            usuarios.append({"id": uid, "saldo": saldo, "valor_equipo": equipo,
                             "patrimonio": saldo + equipo})
        salida.append({"fecha": d.isoformat(), "usuarios": usuarios})

    return salida
