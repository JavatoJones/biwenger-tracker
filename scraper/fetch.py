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


def load_daily_prices(c: BiwengerClient, player_ids, desde: int, hoy: int, precios_hoy: dict,
                      criticos=()) -> dict:
    """Precio diario de cada jugador desde el reset, en {id: {aaammdd: precio}}.

    El histórico completo de un jugador solo se pide la primera vez que aparece; a partir de
    ahí el precio de hoy sale del listado de La Liga, que ya se descarga en una sola llamada.

    `criticos` son los jugadores del reparto inicial: necesitan sí o sí un precio en la fecha
    de inicio, así que se comprueba que lo tengan y se repescan si no.
    """
    path = RAW.parent / "precios_diarios.json"
    cache = json.loads(path.read_text()) if path.exists() else {}
    primer_dia = lambda pid: min((int(k) for k in cache.get(str(pid), {})), default=None)

    def guardar(pid: int) -> None:
        hist = c.get(f"/players/la-liga/{pid}", fields="*,prices")["data"].get("prices", [])
        # Se conserva el último dato anterior al reset: sin él no hay precio que arrastrar
        # al primer día, y el jugador quedaría valorado en cero.
        previos = [x for x in hist if x[0] < desde]
        dias = {str(d): v for d, v in hist if d >= desde}
        if previos:
            d, v = previos[-1]
            dias[str(d)] = v
        cache[str(pid)] = dias

    nuevos = [p for p in player_ids if str(p) not in cache] if c else []
    repescar = [p for p in criticos
                if str(p) in cache and (primer_dia(p) or 0) > desde] if c else []
    for pid in nuevos + repescar:
        guardar(pid)

    # Si ni con el histórico completo hay dato previo, se fija su primer precio conocido en
    # la fecha de inicio: es la mejor estimación posible y evita volver a pedirlo cada día.
    sellados = 0
    for pid in criticos:
        d0 = primer_dia(pid)
        if d0 is not None and d0 > desde:
            cache[str(pid)][str(desde)] = cache[str(pid)][str(d0)]
            sellados += 1

    cambia = bool(nuevos or repescar or sellados)
    for pid, precio in precios_hoy.items():
        dias = cache.get(str(pid))
        if dias is not None and dias.get(str(hoy)) != precio:
            dias[str(hoy)] = precio
            cambia = True
    if cambia:
        path.write_text(json.dumps(cache, sort_keys=True, separators=(",", ":")))
    return cache


def precio_lookup(cache: dict):
    """Devuelve precio(id, aaammdd) con arrastre: el último precio conocido hasta esa fecha."""
    import bisect

    idx = {}
    for pid, dias in cache.items():
        claves = sorted(int(k) for k in dias)
        idx[int(pid)] = (claves, [dias[str(k)] for k in claves])

    def precio(pid: int, day: int) -> int:
        entrada = idx.get(int(pid))
        if not entrada:
            return 0
        claves, valores = entrada
        i = bisect.bisect_right(claves, day)
        return valores[i - 1] if i else 0

    return precio
