"""Hallucination Rate: share of answers that state at least one number with no evidence behind it.

Lower is better. Uses the same evidence check as groundedness.py.
"""
from evals.metrics.groundedness import unsupported


def score(records):
    return sum(bool(unsupported(r)[0]) for r in records) / len(records)
