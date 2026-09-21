"""Plantillas iniciales tras el reset de liga y su valor a fecha de reset.

El reparto inicial no aparece en el board, así que se deduce: un jugador era de inicio de X si
X lo tiene hoy con fecha de propiedad igual al reset, o si X lo vende/cede sin haberlo
adquirido antes en la temporada.
"""
from collections import defaultdict
from datetime import datetime, timezone


def start_dates(season_events: list[dict], reset_ts: int) -> dict[int, int]:
    """Fecha en la que cada usuario empieza: el reset, o su alta si entró más tarde."""
    joins = {}
    for e in season_events:
        if e["type"] == "userJoin":
            for x in e["content"]:
                joins[x["id"]] = max(e["date"], reset_ts)
    return joins


def initial_squads(season_events: list[dict], current_squads: dict[int, list[dict]], reset_ts: int) -> dict[int, set[int]]:
    initial: dict[int, set[int]] = defaultdict(set)
    owner: dict[int, int | None] = {}

    for uid, players in current_squads.items():
        for p in players:
            if p["owner"]["date"] <= reset_ts + 60:
                initial[uid].add(p["id"])
                owner[p["id"]] = uid

    def release(uid: int, pid: int) -> None:
        # Si quien lo suelta no es quien lo fichó, lo tenía de salida: o del reparto inicial,
        # o del lote que recibe un usuario al incorporarse a una liga ya empezada.
        if owner.get(pid) != uid:
            initial[uid].add(pid)
        owner[pid] = None

    def acquire(uid: int, pid: int) -> None:
        owner[pid] = uid

    for e in season_events:
        t, c = e["type"], e["content"]
        if t in ("transfer", "market"):
            for x in c:
                if x.get("from"):
                    release(x["from"]["id"], x["player"])
                if x.get("to"):
                    acquire(x["to"]["id"], x["player"])
        elif t == "adminTransfer":
            for x in c:
                if x.get("from"):
                    release(x["from"]["id"], x["player"])
                acquire(x["to"]["id"], x["player"])
        elif t == "exchange":
            src, dst = c["from"]["id"], c["to"]["id"]
            for pid in c["offeredPlayers"]:
                release(src, pid)
                acquire(dst, pid)
            for pid in c["requestedPlayers"]:
                release(dst, pid)
                acquire(src, pid)
    return dict(initial)


def yymmdd(ts: int) -> int:
    d = datetime.fromtimestamp(ts, tz=timezone.utc)
    return (d.year % 100) * 10000 + d.month * 100 + d.day


def price_at(prices: list[list[int]], day: int) -> int | None:
    """Precio vigente en `day` (yymmdd): el último registro con fecha <= day."""
    best = None
    for d, price in prices:
        if d <= day:
            best = price
        else:
            break
    return best
