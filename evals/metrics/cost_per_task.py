"""Cost Per Task: tokens used x model price, in US dollars.

Prices live in app/config.py (PRICES), shared with the API and the web app.
"""
from app import config


def score(records, model=config.MODEL):
    costs = [config.cost_usd(r["tokens"], model) for r in records]
    return {"mean_usd": round(sum(costs) / len(costs), 5), "total_usd": round(sum(costs), 4),
            "mean_tokens": round(sum(r["tokens"]["input"] + r["tokens"]["output"] for r in records) / len(records))}
