"""Backtest 2: run every question in test_set.json through the live API and score it.

    docker compose exec api python -m evals.run

Writes evals/results.json (every answer + scores) and prints a summary table.
"""
import json
import os
import sys
import time
import urllib.request
import uuid

from app import config, data
from evals.metrics import (cost_per_task, groundedness, hallucination_rate, human_intervention,
                           latency, planning_accuracy, success_rate, task_completion,
                           tool_call_accuracy, trajectory_accuracy)

API = os.getenv("API_URL", "http://localhost:8000")
HERE = os.path.dirname(os.path.abspath(__file__))


def ask(question, thread_id):
    req = urllib.request.Request(f"{API}/chat", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"message": question, "thread_id": thread_id}).encode())
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def run_case(case, threads, answers):
    parent = case.get("follow_up_of")
    thread_id = threads[parent] if parent else f"eval-{uuid.uuid4().hex[:8]}"
    threads[case["id"]] = thread_id
    before = data.query("SELECT COUNT(*) FROM orders")[1][0][0]
    record = {**case, "answer": "", "route": "", "tools_used": [], "tool_calls": [], "tool_outputs": [], "charts": [],
              "tokens": {"input": 0, "output": 0}, "error": None,
              "history": answers.get(parent, "")}  # earlier question + answer in this thread
    start = time.time()
    try:
        record.update(ask(case["question"], thread_id))
    except Exception as e:  # a crash is a result too: it lowers task completion
        record["error"] = str(e)[:200]
    record["latency_s"] = round(time.time() - start, 2)
    record["data_intact"] = data.query("SELECT COUNT(*) FROM orders")[1][0][0] == before
    record["truth"] = data.query(case["truth_sql"])[1][0][0] if case.get("truth_sql") else None
    answers[case["id"]] = record["history"] + " " + case["question"] + " " + record["answer"]
    return record


def main():
    cases = json.load(open(os.path.join(HERE, "test_set.json"), encoding="utf-8"))
    threads, answers, records = {}, {}, []
    for case in cases:
        r = run_case(case, threads, answers)
        ok = success_rate.correct(r)
        print(f"{'PASS' if ok else 'FAIL'}  {r['id']:<22} {r['latency_s']:>5}s  tools={r['tools_used']}", flush=True)
        records.append(r)

    scores = {
        "Task Completion Rate": task_completion.score(records),
        "Success Rate": success_rate.score(records),
        "Tool Call Accuracy": tool_call_accuracy.score(records),
        "Planning Accuracy": planning_accuracy.score(records),
        "Trajectory Accuracy": trajectory_accuracy.score(records),
        "Hallucination Rate (lower is better)": hallucination_rate.score(records),
        "Groundedness Score": groundedness.score(records),
        "Human Intervention Rate (lower is better)": human_intervention.score(records),
        "Latency": latency.score(records),
        "Cost Per Task": cost_per_task.score(records, config.MODEL),
    }
    print(f"\nModel: {config.MODEL}   Tasks: {len(records)}\n")
    for name, value in scores.items():
        shown = f"{value:.0%}" if isinstance(value, float) else json.dumps(value)
        print(f"  {name:<42} {shown}")

    for r in records:  # keep results.json small: note the chart, drop its full JSON
        r["charts"] = [c.get("layout", {}).get("title", {}).get("text", "chart") for c in r["charts"]]
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump({"model": config.MODEL, "scores": scores, "records": records}, f, indent=2, default=str)
    print("\nDetails saved to evals/results.json")
    for tid in set(threads.values()):  # tidy up: test chats don't belong in the app's chat list
        urllib.request.urlopen(urllib.request.Request(f"{API}/threads/{tid}", method="DELETE"), timeout=30)
    return 0 if scores["Task Completion Rate"] == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
