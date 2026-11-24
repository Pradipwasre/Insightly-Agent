"""The agents, as one LangGraph graph.

    START -> router --data---> analyst      <--> tools --+
                   +--chart--> chart_maker  <--> tools --+--> memory -> END
                   +--chat---> chat ---------------------+

Memory has two layers:
  * every message is saved per thread_id in memory.db (the checkpointer), and
  * the LLM sees only the last few turns plus a running summary of older ones,
    so long chats stay cheap and fast without forgetting what was said.
"""
import sqlite3
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel

from app import config
from app.llm import get_llm
from app.tools import CHART_TOOLS, TOOLS

RECENT_TURNS = 6  # turns the LLM sees word for word; older ones live in the summary

ANALYST_PROMPT = """You are Insightly, a senior data analyst for an online clothing shop.
Answer with real numbers from the database:
1. call get_schema to see the tables,
2. call lookup_metric when the question names a business metric,
3. call run_sql (SQLite) and fix the query if it returns an error.
Keep SQL simple: product category and brand are in products (join order_items.product_id = products.id);
use inventory_items only for stock questions.
You can only read data: if asked to change or delete anything, say you can't, without calling run_sql.
If a query finds no rows for a period, say there is no data for it (don't report it as 0).
Lead with the answer in bold, then at most 2 short sentences of context.
Use $ for money and thousands separators. Don't paste the SQL; the app shows it."""

CHART_PROMPT = """You are Insightly, a senior data analyst who explains data with charts.
1. call get_schema, and lookup_metric when the question names a business metric,
2. call make_chart with a SELECT that aggregates the data (by month, category...),
   picking the chart type that fits: line for trends, bar to compare, pie for shares.
   If it returns an error, fix the SQL or column names and try again.
3. Then write 2-3 short bullet points of insight (highest, lowest, trend), quoting ONLY
   numbers exactly as they appear in the chart summary. Don't add up or calculate new numbers.
   Use $ for money. Don't paste the SQL or the chart JSON.
Keep SQL simple: product category and brand are in products (join order_items.product_id = products.id);
use inventory_items only for stock questions.
You can only read data: never change or delete anything."""

CHAT_PROMPT = """You are Insightly, a friendly assistant for an online clothing shop's data.
You can answer questions about sales, orders, customers, products, inventory and
website events, and draw charts. Reply briefly."""

SUMMARY_PROMPT = """Update the running summary of a conversation between a user and a
data assistant. Keep every number, year, metric and preference the user mentioned.
At most 8 short bullet points. Return only the summary."""


# Extra rules for Claude models (added after the backtest on claude-haiku-5-5, which
# sometimes computed its own growth % or remainders and once reasoned out loud).
# OpenAI/Groq prompts are unchanged.
CLAUDE_RULES = """
Output rules: write only the final answer, never your reasoning or self-corrections.
Quote numbers exactly as the tools returned them. Don't calculate new numbers
(differences, growth %, remainders, sums of shares) unless the user asks for one."""
if config.PROVIDER == "anthropic":
    ANALYST_PROMPT += CLAUDE_RULES
    CHART_PROMPT += CLAUDE_RULES


class Route(BaseModel):
    """Pick "chart" when the user asks to see, plot, chart, graph or visualise data.
    Pick "data" for ANY other question about the shop's sales, orders, customers, products,
    inventory or website events (even for dates that may not exist in the data; the
    database will tell). Pick "chat" only for greetings and questions about you."""
    route: Literal["data", "chart", "chat"]


class State(MessagesState):
    route: str
    summary: str
    summarized_upto: int  # messages before this index are covered by the summary


llm = get_llm()
fast_llm = llm if config.FAST_MODEL == config.MODEL else get_llm(config.FAST_MODEL)
router_llm = fast_llm.with_structured_output(Route)
analyst_llm = llm.bind_tools(TOOLS)
chart_llm = llm.bind_tools(CHART_TOOLS)


def recent_start(messages):
    """Index where the last RECENT_TURNS turns begin. Always a user message,
    so a tool call is never cut off from its result."""
    starts = [i for i, m in enumerate(messages) if m.type == "human"]
    return starts[-RECENT_TURNS] if len(starts) >= RECENT_TURNS else 0


def context(state, prompt):
    if state.get("summary"):
        prompt += f"\n\nSummary of the earlier conversation:\n{state['summary']}"
    return [SystemMessage(prompt)] + state["messages"][recent_start(state["messages"]):]


def router(state: State):
    # Only the plain conversation (questions + final answers), never half a tool exchange
    talk = [m for m in state["messages"] if m.type == "human" or (m.type == "ai" and not m.tool_calls)][-6:]
    while talk and talk[0].type != "human":  # some providers (Anthropic) need the user to speak first
        talk = talk[1:]
    return {"route": router_llm.invoke([SystemMessage(Route.__doc__)] + talk).route}


def analyst(state: State):
    return {"messages": [analyst_llm.invoke(context(state, ANALYST_PROMPT))]}


def chart_maker(state: State):
    return {"messages": [chart_llm.invoke(context(state, CHART_PROMPT))]}


def chat(state: State):
    return {"messages": [llm.invoke(context(state, CHAT_PROMPT))]}


def memory(state: State):
    """Fold turns that dropped out of the recent window into the summary."""
    messages, done = state["messages"], state.get("summarized_upto", 0)
    cut = recent_start(messages)
    if cut <= done:
        return {}
    old = [m for m in messages[done:cut] if m.type == "human" or (m.type == "ai" and not m.tool_calls)]
    lines = "\n".join(f"{'User' if m.type == 'human' else 'Assistant'}: {m.text}" for m in old)
    summary = fast_llm.invoke([SystemMessage(SUMMARY_PROMPT),
                          HumanMessage(f"Current summary:\n{state.get('summary') or '(none)'}\n\nNew lines:\n{lines}")])
    return {"summary": str(summary.text), "summarized_upto": cut}


def build_graph():
    g = StateGraph(State)
    g.add_node("router", router)
    g.add_node("analyst", analyst)
    g.add_node("chart_maker", chart_maker)
    g.add_node("tools", ToolNode(CHART_TOOLS))
    g.add_node("chat", chat)
    g.add_node("memory", memory)

    g.add_edge(START, "router")
    g.add_conditional_edges("router", lambda s: s["route"],
                            {"data": "analyst", "chart": "chart_maker", "chat": "chat"})
    for agent in ("analyst", "chart_maker"):
        g.add_conditional_edges(agent, tools_condition, {"tools": "tools", END: "memory"})
    g.add_conditional_edges("tools", lambda s: "chart_maker" if s["route"] == "chart" else "analyst")
    g.add_edge("chat", "memory")
    g.add_edge("memory", END)

    # Every step is saved per thread_id in memory.db, so chats survive restarts
    saver = SqliteSaver(sqlite3.connect(config.MEMORY_DB, check_same_thread=False))
    saver.setup()  # create the tables now, so /threads works on a fresh install before the first chat
    return g.compile(checkpointer=saver)
