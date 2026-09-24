"""Dinero que se mueve entre mánagers: quién paga a quién y por qué jugadores.

Solo cuentan las operaciones entre dos miembros de la liga. Comprar en el mercado o vender
al mercado mueve dinero fuera de la liga y no dibuja ninguna relación entre vosotros.
"""
from collections import defaultdict


def flujos(season_events: list[dict]) -> list[dict]:
    """[{pagador, cobrador, euros, operaciones, jugadores:[{jugador, euros, fecha, via}]}].

    La dirección es siempre la del dinero: `pagador` es quien suelta los euros.
    """
    pares: dict[tuple[int, int], dict] = defaultdict(lambda: {"euros": 0, "jugadores": []})

    def anota(pagador, cobrador, euros, jugador, fecha, via):
        if pagador == cobrador or not euros:
            return
        p = pares[(pagador, cobrador)]
        p["euros"] += euros
        p["jugadores"].append({"jugador": jugador, "euros": euros, "fecha": fecha, "via": via})

    for e in season_events:
        t, c, cuando = e["type"], e["content"], e["date"]
        if t in ("transfer", "market"):
            for x in c:
                if x.get("from") and x.get("to"):  # el comprador paga al vendedor
                    anota(x["to"]["id"], x["from"]["id"], x["amount"], x["player"], cuando,
                          x.get("type") or "traspaso")
        elif t == "adminTransfer":
            for x in c:
                if x.get("from"):
                    anota(x["to"]["id"], x["from"]["id"], x["amount"], x["player"], cuando, "admin")
        elif t == "exchange":
            neto = c["amount"] - c["requestedAmount"]
            if neto:
                paga, cobra = (c["from"]["id"], c["to"]["id"]) if neto > 0 else (c["to"]["id"], c["from"]["id"])
                piezas = c["offeredPlayers"] + c["requestedPlayers"]
                anota(paga, cobra, abs(neto), piezas[0] if piezas else None, cuando, "cambio")

    salida = []
    for (pagador, cobrador), p in pares.items():
        p["jugadores"].sort(key=lambda j: -j["euros"])
        salida.append({"pagador": pagador, "cobrador": cobrador, "euros": p["euros"],
                       "operaciones": len(p["jugadores"]), "jugadores": p["jugadores"]})
    salida.sort(key=lambda f: -f["euros"])
    return salida


def resumen_por_manager(flujos_lista: list[dict]) -> dict[int, dict]:
    """Cuánto ha pagado y cobrado cada uno dentro de la liga."""
    r: dict[int, dict] = defaultdict(lambda: {"pagado": 0, "cobrado": 0, "socios": set(), "operaciones": 0})
    for f in flujos_lista:
        r[f["pagador"]]["pagado"] += f["euros"]
        r[f["cobrador"]]["cobrado"] += f["euros"]
        r[f["pagador"]]["socios"].add(f["cobrador"])
        r[f["cobrador"]]["socios"].add(f["pagador"])
        r[f["pagador"]]["operaciones"] += f["operaciones"]
        r[f["cobrador"]]["operaciones"] += f["operaciones"]
    return {uid: {"pagado": v["pagado"], "cobrado": v["cobrado"],
                  "neto": v["cobrado"] - v["pagado"], "socios": len(v["socios"]),
                  "operaciones": v["operaciones"]} for uid, v in r.items()}
