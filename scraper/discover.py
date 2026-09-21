"""Vuelca respuestas crudas de la API a data/raw/ para ver qué campos hay realmente.

Uso: python -m scraper.discover
"""
import json
from pathlib import Path

from .client import BiwengerClient

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def dump(name: str, payload: dict) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ok  {name}")


def attempt(name: str, fn) -> None:
    try:
        dump(name, fn())
    except Exception as e:  # el objetivo es explorar, seguimos aunque falle un endpoint
        print(f"ERR {name}: {e}")


def main() -> None:
    c = BiwengerClient.from_env()
    attempt("account", lambda: c.get("/account"))
    attempt("league", lambda: c.get("/league", include="all,-lastAccess", fields="*,standings,tournaments,group,settings(description)"))
    attempt("board", lambda: c.get(f"/league/{c.league_id}/board", type="transfer,market,exchange,loan,loanReturn,adminTransfer,clauseIncrement", limit=100))
    attempt("me", lambda: c.get(f"/user/{c.user_id}", fields="*,lineup(type,playersID,reservesID,captain,striker,coach),players(id,owner),market,offers,-trophies"))

    # Un rival cualquiera, para comprobar qué se ve del resto de usuarios
    try:
        standings = json.loads((RAW / "league.json").read_text(encoding="utf-8"))["data"]["standings"]
        rival = next(s for s in standings if s["id"] != c.user_id)
        attempt("rival", lambda: c.get(f"/user/{rival['id']}", fields="*,lineup(type,playersID,reservesID,captain,striker,coach),players(id,owner),-trophies"))
    except Exception as e:
        print(f"ERR rival: {e}")

    attempt("players_laliga", lambda: c.get("/competitions/la-liga/data", lang="es", score="5"))


if __name__ == "__main__":
    main()
