"""Reconstrucción de saldos a partir del board de la liga.

Biwenger solo expone el saldo del propio usuario, así que el de los rivales se estima
sumando los flujos de dinero desde el último `leagueReset` y aplicando un desfase común
calibrado con el saldo real del usuario autenticado.
"""
from collections import defaultdict


def current_season_events(events: list[dict]) -> list[dict]:
    """Eventos desde el último reset de liga, en orden cronológico."""
    resets = [e["date"] for e in events if e["type"] == "leagueReset"]
    t0 = max(resets) if resets else 0
    return sorted((e for e in events if e["date"] >= t0), key=lambda e: e["date"])


def money_flows(events: list[dict]) -> dict[int, int]:
    """Suma de ingresos y gastos por usuario (id -> euros) para los eventos dados."""
    flow: dict[int, int] = defaultdict(int)
    paid: dict[tuple[str, int], int] = {}  # (jornada, usuario) -> bonus ya abonado
    for e in events:
        t, c = e["type"], e["content"]
        if t == "bonus":
            for x in c:
                flow[x["user"]["id"]] += x["amount"]
        elif t == "roundFinished":
            # Una jornada aplazada se liquida dos veces: la segunda (part 2) paga el bonus
            # recalculado completo y retira el que se abonó en la primera.
            key = c["round"]["name"].replace(" (aplazada)", "").strip()
            for x in c["results"]:
                uid, bonus = x["user"]["id"], x.get("bonus", 0)
                if c["round"].get("part") == 2 and (key, uid) in paid:
                    flow[uid] -= paid[(key, uid)]
                flow[uid] += bonus
                paid[(key, uid)] = bonus
        elif t in ("transfer", "market"):
            for x in c:
                if x.get("from"):
                    flow[x["from"]["id"]] += x["amount"]
                if x.get("to"):
                    flow[x["to"]["id"]] -= x["amount"]
        elif t == "adminTransfer":
            for x in c:
                flow[x["to"]["id"]] -= x["amount"]
                if x.get("from"):
                    flow[x["from"]["id"]] += x["amount"]
        elif t == "clauseIncrement":
            for x in c:
                flow[x["user"]["id"]] -= x["amount"]
        # Los retos ("challenge") no se cuentan: se liquidan al cerrar la jornada y ya van
        # incluidos en el `bonus` de roundFinished.
        elif t == "exchange":
            net = c["amount"] - c["requestedAmount"]
            flow[c["from"]["id"]] -= net
            flow[c["to"]["id"]] += net
    return dict(flow)


def estimate_balances(events: list[dict], my_id: int, my_real_balance: int) -> tuple[dict[int, int], int]:
    """Devuelve ({user_id: saldo estimado}, desfase aplicado)."""
    flow = money_flows(current_season_events(events))
    offset = my_real_balance - flow.get(my_id, 0)
    return {uid: f + offset for uid, f in flow.items()}, offset
