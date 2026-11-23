"""FastAPI app: the HTTP door to the agents. Open /docs to try it."""
import sqlite3
import time
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from app import config, data

data.build_db()  # create shop.db from "data files/" on first start

from app.graph import build_graph  # noqa: E402  (needs shop.db to exist)

graph = build_graph()
app = FastAPI(title="Insightly Lite")


class ChatIn(BaseModel):
    message: str
    thread_id: str | None = None  # send the same id again to continue a conversation


def turns(messages):
    """Group the saved messages into one record per question: answer, steps, charts, cost."""
    out = []
    for m in messages:
        if m.type == "human":
            out.append({"question": m.content, "answer": "", "tool_calls": [], "tool_outputs": [],
                        "charts": [], "tokens": {"input": 0, "output": 0}})
        elif out and m.type == "ai":
            t, usage = out[-1], m.usage_metadata or {}
            t["tool_calls"] += [{"name": c["name"], "args": c["args"]} for c in m.tool_calls]
            t["tokens"]["input"] += usage.get("input_tokens", 0)
            t["tokens"]["output"] += usage.get("output_tokens", 0)
            if not m.tool_calls:
                t["answer"] = str(m.text)  # plain text, even if the provider returns content blocks
        elif out and m.type == "tool":
            out[-1]["tool_outputs"].append(m.content)
            if m.artifact:
                out[-1]["charts"].append(m.artifact)
    for t in out:
        t["tools_used"] = [c["name"] for c in t["tool_calls"]]
        t["route"] = "chart" if t["charts"] else ("data" if t["tool_calls"] else "chat")
        t["cost_usd"] = round(config.cost_usd(t["tokens"]), 6)
    return out


def state_of(thread_id):
    return graph.get_state({"configurable": {"thread_id": thread_id}}).values


@app.get("/health")
def health():
    tables = data.query("SELECT name FROM sqlite_master WHERE type='table'")[1]
    return {"status": "ok", "provider": config.PROVIDER, "model": config.MODEL,
            "tables": [t[0] for t in tables]}


@app.post("/chat")
def chat(body: ChatIn):
    thread_id = body.thread_id or str(uuid.uuid4())
    run = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}
    start = time.time()
    result = graph.invoke({"messages": [("user", body.message)]}, run)
    return {"thread_id": thread_id, "route": result["route"], "model": config.MODEL,
            "latency_s": round(time.time() - start, 2), **turns(result["messages"])[-1]}


@app.get("/history/{thread_id}")
def history(thread_id: str):
    state = state_of(thread_id)
    return {"thread_id": thread_id, "summary": state.get("summary", ""),
            "turns": turns(state.get("messages", []))}


@app.get("/threads")
def threads(limit: int = 30):
    """Recent conversations, newest first, with a title and their total cost."""
    con = sqlite3.connect(config.MEMORY_DB)
    try:
        ids = [r[0] for r in con.execute(
            "SELECT thread_id FROM checkpoints GROUP BY thread_id ORDER BY MAX(checkpoint_id) DESC LIMIT ?", (limit,))]
    finally:
        con.close()
    out = []
    for tid in ids:
        ts = turns(state_of(tid).get("messages", []))
        if ts:
            out.append({"thread_id": tid, "title": ts[0]["question"][:60], "questions": len(ts),
                        "cost_usd": round(sum(t["cost_usd"] for t in ts), 6)})
    return out


@app.delete("/threads/{thread_id}")
def delete_thread(thread_id: str):
    graph.checkpointer.delete_thread(thread_id)
    return {"deleted": thread_id}
