"""Cliente mínimo para la API no oficial de Biwenger."""
import os
import time
from pathlib import Path

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

    @staticmethod
    def _cargar_env() -> None:
        """Lee .env si existe. En GitHub Actions las variables ya vienen del entorno y manda este."""
        ruta = Path(__file__).resolve().parent.parent / ".env"
        if not ruta.exists():
            return
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                os.environ.setdefault(clave.strip(), valor.strip())

    @classmethod
    def from_env(cls) -> "BiwengerClient":
        cls._cargar_env()
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
