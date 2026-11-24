"""Tool Call Accuracy: share of tool calls that were valid and worked.

A call counts as good when the tool exists and it did not return an error
(for run_sql: the SQL ran). A task with no calls, when none were expected, scores 1.
"""
TOOLS = {"get_schema", "lookup_metric", "run_sql", "make_chart"}


def case_score(r):
    calls = r["tool_calls"]
    if not calls:
        return 1.0 if not r["expected_tools"] else 0.0
    good = 0
    for call, output in zip(calls, r["tool_outputs"]):
        ok = call["name"] in TOOLS and not output.startswith(("Error", "SQL error", "Chart error"))
        good += ok
    return good / len(calls)


def score(records):
    return sum(case_score(r) for r in records) / len(records)
