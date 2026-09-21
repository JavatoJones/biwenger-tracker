"""Descarga el estado actual de la liga a data/raw/."""
import json
from pathlib import Path

from .client import BiwengerClient

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def _write(name: str, payload) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def fetch_all(c: BiwengerClient) -> dict:
    league = c.get("/league", include="all,-lastAccess", fields="*,standings")["data"]
    _write("league", {"data": league})

    board, offset = [], 0
    while True:
        page = c.get(f"/league/{c.league_id}/board", limit=100, offset=offset)["data"]
        if not page:
            break
        board += page
        offset += len(page)
    _write("board_full", board)

    squads = {}
    for s in league["standings"]:
        squads[s["id"]] = c.get(f"/user/{s['id']}", fields="*,players(id,owner)")["data"].get("players", [])
    _write("squads", squads)

    competition = c.get("/competitions/la-liga/data", lang="es", score=c.score_id)["data"]
    _write("players_laliga", {"data": competition})

    balance = c.get("/account")["data"]["leagues"]
    balance = next(l for l in balance if l["id"] == c.league_id)["user"]["balance"]
    return {"league": league, "board": board, "squads": squads, "players": competition["players"], "my_balance": balance}


def load_cached() -> dict:
    """Relee la última descarga de data/raw, sin tocar la API."""
    leer = lambda n: json.loads((RAW / f"{n}.json").read_text(encoding="utf-8-sig"))
    league = leer("league")["data"]
    return {
        "league": league, "board": leer("board_full"),
        "squads": {int(k): v for k, v in leer("squads").items()},
        "players": leer("players_laliga")["data"]["players"],
        "my_balance": None,
    }


def load_price_points(c: BiwengerClient, pares) -> dict:
    """Precio de un jugador en una fecha concreta, para `pares` de (id, aaammdd).

    Solo guardamos los puntos que hacen falta (el día del reparto y el de cada intercambio),
    no el histórico entero: son fechas fijas, así que a partir de la segunda ejecución no
    hace falta pedir ningún precio.
    """
    from .initial import price_at

    path = RAW.parent / "precios.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    if c is None:
        return cache
    faltan: dict[int, set] = {}
    for pid, day in pares:
        if f"{pid}:{day}" not in cache:
            faltan.setdefault(pid, set()).add(day)
    for pid, days in faltan.items():
        hist = c.get(f"/players/la-liga/{pid}", fields="*,prices")["data"].get("prices", [])
        for day in days:
            cache[f"{pid}:{day}"] = price_at(hist, day) or 0
    if faltan:
        path.write_text(json.dumps(cache, sort_keys=True))
    return cache
