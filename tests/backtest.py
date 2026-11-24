"""Backtest 1: quick checks that need no API key.

Run inside the container:   docker compose exec api python tests/backtest.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import config, data          # noqa: E402
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # noqa: E402

from app import charts  # noqa: E402
from app.tools import get_schema, lookup_metric, make_chart, run_sql  # noqa: E402

passed = failed = 0


def check(name, ok):
    global passed, failed
    passed, failed = passed + ok, failed + (not ok)
    print(("PASS " if ok else "FAIL ") + name)


# 1. Every CSV in "data files/" became a table with the same number of rows
for f in sorted(os.listdir(config.CSV_DIR)):
    path = os.path.join(config.CSV_DIR, f)
    if not f.endswith(".csv") or os.path.getsize(path) == 0:
        continue
    table = f[:-4]
    with open(path, newline="", encoding="utf-8") as fh:
        expected = sum(1 for _ in csv.reader(fh)) - 1
    got = data.query(f"SELECT COUNT(*) FROM {table}")[1][0][0]
    check(f"{table}: {got:,} rows (csv has {expected:,})", got == expected)

# 2. Cleaning: dates work with SQLite, postal codes keep leading zeros, empty = NULL
check("dates have no ' UTC'", data.query("SELECT COUNT(*) FROM orders WHERE created_at LIKE '%UTC'")[1][0][0] == 0)
check("strftime year works", data.query("SELECT strftime('%Y', MIN(created_at)) FROM orders")[1][0][0] == "2019")
check("postal codes stay text", data.query("SELECT typeof(postal_code) FROM users LIMIT 1")[1][0][0] == "text")
check("empty values are NULL", data.query("SELECT COUNT(*) FROM orders WHERE returned_at = ''")[1][0][0] == 0)

# 3. Tools
check("get_schema lists 7 tables", get_schema.invoke({}).count("(") >= 7)
check("lookup_metric finds net revenue", "Net revenue" in lookup_metric.invoke({"question": "revenue in 2023"}))
check("run_sql answers a SELECT", "rows: [(" in run_sql.invoke({"sql": "SELECT COUNT(*) FROM orders"}))
check("run_sql returns SQL errors to the LLM", "SQL error" in run_sql.invoke({"sql": "SELECT nope FROM orders"}))

# 4. SQL safety: the agent can never change data
for bad in ["DELETE FROM orders", "DROP TABLE users", "UPDATE orders SET status='x'",
            "WITH x AS (SELECT 1) DELETE FROM orders", "SELECT 1; DROP TABLE orders"]:
    out = run_sql.invoke({"sql": bad})
    check(f"blocked: {bad}", out.startswith(("Error", "SQL error")))
check("orders table still intact", data.query("SELECT COUNT(*) FROM orders")[1][0][0] > 100_000)

# 5. Charts: every chart type builds from real data, bad input comes back as a clear error
monthly = data.query("SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS orders FROM orders "
                     "WHERE created_at LIKE '2023%' GROUP BY month")
by_cat = data.query("SELECT category, COUNT(*) AS products FROM products GROUP BY category")
top5 = (by_cat[0], by_cat[1][:5])
for kind, (cols, rows), x, y in [("line", monthly, "month", "orders"), ("area", monthly, "month", "orders"),
                                 ("bar", by_cat, "category", "products"), ("pie", top5, "category", "products"),
                                 ("scatter", monthly, "month", "orders")]:
    fig, summary = charts.build(cols, rows, kind, x, y, f"Test {kind}")
    check(f"{kind} chart builds ({len(rows)} points)", bool(fig["data"]) and "Highest" in summary)
check("chart with a wrong column explains the columns", "Columns are" in make_chart.invoke(
    {"sql": "SELECT category FROM products", "chart_type": "bar", "x": "nope", "y": "category", "title": "t"}))
check("chart tool blocks DELETE", make_chart.invoke(
    {"sql": "DELETE FROM orders", "chart_type": "bar", "x": "a", "y": "b", "title": "t"}).startswith("Error"))

# 6. Memory window never cuts a tool call off from its result
from app.graph import RECENT_TURNS, recent_start  # noqa: E402
msgs = []
for i in range(RECENT_TURNS + 3):
    msgs += [HumanMessage(f"q{i}"), AIMessage("", tool_calls=[{"name": "run_sql", "args": {}, "id": f"c{i}"}]),
             ToolMessage("rows", tool_call_id=f"c{i}"), AIMessage(f"a{i}")]
cut = recent_start(msgs)
check(f"memory keeps the last {RECENT_TURNS} turns, starting at a question",
      msgs[cut].type == "human" and sum(m.type == "human" for m in msgs[cut:]) == RECENT_TURNS)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
