"""Groundedness Score: share of numbers in the answer that come from the evidence.

Evidence = tool outputs of this turn + the question + earlier answers in the same thread.
An answer with no numbers in it scores 1 (nothing to ground).
"""
from evals.numbers import close, numbers, source_values


def unsupported(r):
    evidence = source_values(" ".join(r["tool_outputs"]) + " " + r["question"] + " " + r["history"])
    claims = numbers(r["answer"])
    return [v for v, tol in claims if not any(close(v, tol, e) for e in evidence)], len(claims)


def case_score(r):
    bad, total = unsupported(r)
    return 1.0 if total == 0 else (total - len(bad)) / total


def score(records):
    return sum(case_score(r) for r in records) / len(records)
