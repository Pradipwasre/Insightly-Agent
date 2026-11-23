"""Task Completion Rate (TCR): did the agent finish and return an answer, with no crash or timeout?"""


def completed(r):
    return not r["error"] and bool((r["answer"] or "").strip())


def score(records):
    return sum(completed(r) for r in records) / len(records)
