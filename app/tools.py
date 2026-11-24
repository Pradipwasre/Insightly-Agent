"""Tools the agents can call. The docstring is what the LLM reads to decide."""
from typing import Literal

from langchain_core.tools import tool

from app import charts, data, knowledge


def is_select(sql):
    return sql.strip().lower().startswith(("select", "with"))


@tool
def get_schema() -> str:
    """List every table and its columns in the shop database."""
    return data.schema()


@tool
def lookup_metric(question: str) -> str:
    """Find the official definition of a business metric (revenue, profit, return rate...)."""
    hits = knowledge.search(question)
    if not hits:
        return "No official metric found. Use your best judgement."
    return "\n".join(f"{m['name']}: {m['sql']}" for m in hits)


@tool
def run_sql(sql: str) -> str:
    """Run one read-only SQLite SELECT query and return the rows."""
    if not is_select(sql):
        return "Error: only SELECT queries are allowed."
    try:
        cols, rows = data.query(sql)
    except Exception as e:  # the error goes back to the LLM so it can fix its SQL
        return f"SQL error: {e}"
    return f"columns: {cols}\nrows: {rows}"


@tool(response_format="content_and_artifact")
def make_chart(sql: str, chart_type: Literal["bar", "line", "area", "pie", "scatter"],
               x: str, y: str, title: str, color: str = ""):
    """Draw a Plotly chart from ONE read-only SELECT query.
    x, y (and optional color, for a second grouping) must be column names in the query result.
    bar = compare categories, line = trend over time, area = volume over time,
    pie = share of a total (8 slices or fewer), scatter = relation between two numbers.
    Aggregate in SQL first (e.g. by month or category) and keep it to about 30 rows."""
    if not is_select(sql):
        return "Error: only SELECT queries are allowed.", None
    try:
        cols, rows = data.query(sql, max_rows=500)
        figure, summary = charts.build(cols, rows, chart_type, x, y, title, color)
    except Exception as e:  # back to the LLM so it can fix the query or the column names
        return f"Chart error: {e}", None
    return summary, figure


TOOLS = [get_schema, lookup_metric, run_sql]   # the analyst agent
CHART_TOOLS = TOOLS + [make_chart]             # the chart agent
