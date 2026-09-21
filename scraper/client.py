"""Cliente mínimo para la API no oficial de Biwenger."""
import os
import time

import requests
import truststore

# Usa el almacén de certificados del sistema (necesario tras proxies corporativos con inspección TLS)
truststore.inject_into_ssl()

BASE = "https://biwenger.as.com/api/v2"


class BiwengerClient:
    def __init__(self, email: str, password: str, league_id: int | None = None):
        self.session = requests.Session()
        self.session.headers.update({"X-Lang": "es", "Accept": "application/json"})
        self._login(email, password)
        self._select_league(league_id)

    @classmethod
    def from_env(cls) -> "BiwengerClient":
        league = os.environ.get("BIWENGER_LEAGUE_ID")
        return cls(
            os.environ["BIWENGER_EMAIL"],
            os.environ["BIWENGER_PASSWORD"],
            int(league) if league else None,
        )

    def _login(self, email: str, password: str) -> None:
        r = self.session.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=30)
        r.raise_for_status()
        token = r.json()["token"]
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _select_league(self, league_id: int | None) -> None:
        account = self.get("/account")["data"]
        leagues = account["leagues"]
        if league_id is None:
            if len(leagues) != 1:
                names = ", ".join(f"{l['id']}={l['name']}" for l in leagues)
                raise SystemExit(f"Hay varias ligas, define BIWENGER_LEAGUE_ID. Disponibles: {names}")
            league = leagues[0]
        else:
            league = next(l for l in leagues if l["id"] == league_id)
        self.league_id = league["id"]
        self.user_id = league["user"]["id"]
        self.score_id = league.get("scoreID", 1)
        self.session.headers["X-League"] = str(self.league_id)
        self.session.headers["X-User"] = str(self.user_id)

    def get(self, path: str, **params) -> dict:
        # Biwenger corta con 429 si se le pide demasiado seguido: esperamos y reintentamos.
        for intento in range(6):
            r = self.session.get(f"{BASE}{path}", params=params or None, timeout=30)
            if r.status_code != 429:
                break
            espera = r.headers.get("Retry-After")
            time.sleep(min(float(espera) if espera and espera.isdigit() else 4 * 2 ** intento, 90))
        r.raise_for_status()
        time.sleep(0.25)  # ritmo cortés entre llamadas
        return r.json()
