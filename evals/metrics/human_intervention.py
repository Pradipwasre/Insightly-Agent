"""Human Intervention Rate: share of tasks where a person would have to step in.

That is: the agent crashed or gave no answer, asked the user to clarify,
or hit too many SQL errors (3+) before answering. Lower is better.
"""
from evals.metrics.task_completion import completed

ASKS = ("could you clarify", "can you clarify", "do you mean", "please specify", "which one do you")


def needs_human(r):
    if not completed(r):
        return True
    sql_errors = sum(o.startswith(("Error", "SQL error")) for o in r["tool_outputs"])
    return sql_errors >= 3 or any(a in r["answer"].lower() for a in ASKS)


def score(records):
    return sum(needs_human(r) for r in records) / len(records)
