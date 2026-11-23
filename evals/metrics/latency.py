"""Latency: seconds from sending the question to getting the answer (mean, median, p95)."""
import math
import statistics


def score(records):
    s = sorted(r["latency_s"] for r in records)
    p95 = s[math.ceil(0.95 * len(s)) - 1]
    return {"mean_s": round(statistics.mean(s), 2), "p50_s": round(statistics.median(s), 2), "p95_s": round(p95, 2)}
