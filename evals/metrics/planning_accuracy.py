"""Planning Accuracy: did the agent pick the right plan before acting?

Checks per task (score = checks passed / checks made):
  1. right route (data question -> analyst, chart request -> chart agent, small talk -> chat)
  2. looked at the schema before the first query (or already knew it from earlier in the thread)
  3. looked up the metric definition when the question names a metric
"""


def case_score(r):
    used, expected = r["tools_used"], r["expected_tools"]
    want = {"chat": "chat", "chart": "chart"}.get(r["type"], "data")
    checks = [r["route"] == want or r["type"] in ("unsafe", "recall")]
    query = next((t for t in used if t in ("run_sql", "make_chart")), None)
    if query and "get_schema" in expected:
        checks.append("get_schema" in used and used.index("get_schema") < used.index(query))
    if "lookup_metric" in expected:
        checks.append("lookup_metric" in used)
    return sum(checks) / len(checks)


def score(records):
    return sum(case_score(r) for r in records) / len(records)
