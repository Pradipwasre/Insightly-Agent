# Insightly Lite

Your AI data analyst for an online clothing shop. Ask in plain English, get real
numbers and analyst-style Plotly charts, in a clean web app that shows the API cost
and the SQL behind every answer. It remembers the conversation, so follow-ups like
"and in 2022?" or "now as a bar chart" just work.

Built with **FastAPI**, **LangGraph**, **LangChain**, **Streamlit**, **Plotly** and
**Docker**. Uses Anthropic `claude-haiku-5-5` by default (an OpenAI or Groq key also works). Comes with backtests and an
`evals/` folder that scores the agents on 10 industry metrics.

Open `docs/architecture.html` and `docs/agentic-ai.html` in a browser for the
visual guide.

## How it works

```
 Streamlit app (:8501) ──► FastAPI (:8000) ──► LangGraph
                                                 │
   START ─► router ─┬─ data ──► Analyst agent ◄──► tools: get_schema
                    ├─ chart ─► Chart agent   ◄──►        lookup_metric (RAG)
                    └─ chat ──► Assistant              run_sql (read-only)
                                    │                   make_chart (Plotly)
                       LLM: Anthropic claude-haiku-5-5 (or OpenAI / Groq)
                                 memory ─► END
                                    │
        data/memory.db  every message per conversation + running summary
        data/shop.db    built from the CSVs in "data files/"
```

| Concept | Where |
|---|---|
| Load your CSV files into SQLite | `app/data.py` |
| Tools (function calling) | `app/tools.py` |
| Plotly charts, analyst styling | `app/charts.py` |
| Agents, router, tool loop, memory | `app/graph.py` |
| RAG (official metric definitions) | `app/knowledge.py` |
| Guardrails (read-only SQL, 60 s query limit) | `app/tools.py`, `app/data.py` |
| Model choice and prices | `app/llm.py`, `app/config.py` |
| HTTP API | `app/main.py` |
| Web app | `ui/app.py` |
| Backtest 1 (no API key needed) | `tests/backtest.py` |
| Backtest 2: agent evals (10 metrics) | `evals/` |

### Memory

- Every message is saved per conversation (`thread_id`) in `data/memory.db`, so
  chats survive restarts and show up in the app's sidebar.
- The LLM sees the last 6 turns word for word, plus a running summary of everything
  older. Long chats stay fast and cheap without forgetting names, numbers or preferences.

## The data

Put your CSV files in the `data files/` folder (file name = table name). This
project uses an e-commerce dataset with 7 tables and about 3.3 million rows
(2019 to 2024).

On the **first** start the app builds `data/shop.db` from these files. That takes
a few minutes once; after that it starts in seconds.

**New data:** update the CSVs, keeping the same file names, then delete
`data/shop.db` and start again.

## Run it

You need **Docker Desktop** (running) and an API key from
https://platform.claude.com/settings/keys (an OpenAI or Groq key also works).

### Windows (PowerShell)

```powershell
cd D:\insightly-lite
if (!(Test-Path .env)) { copy .env.example .env }   # only the first time
notepad .env                 # paste your key after ANTHROPIC_API_KEY=
docker compose up --build
```

### Mac (Terminal)

```bash
cd ~/insightly-lite
[ -f .env ] || cp .env.example .env   # only the first time
open -e .env                 # paste your key after ANTHROPIC_API_KEY=
docker compose up --build
```

Then open:

- **http://localhost:8501**: the web app
- **http://localhost:8000/docs**: the API

Stop with `Ctrl+C`, or with `docker compose down`.

**Ports already in use?** Pick others.

Windows:

```powershell
$env:API_PORT=8100; $env:UI_PORT=8601; docker compose up
```

Mac:

```bash
API_PORT=8100 UI_PORT=8601 docker compose up
```

Your key stays in `.env`. That file is git-ignored and never copied into the
Docker image.

### Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `Could not find a version that satisfies the requirement fastapi==... (from versions: none)` | pip inside Docker can't reach PyPI (network/DNS), not a wrong version | Check your internet, turn off VPN/proxy for a moment, **restart Docker Desktop**, then `docker compose build --no-cache` and `docker compose up`. Still failing: Docker Desktop, Settings, Docker Engine, add `"dns": ["8.8.8.8", "1.1.1.1"]`, Apply & restart |
| `No API key found for LLM_PROVIDER=...` | `.env` has no key (for example after `cp .env.example .env` overwrote it) | Open `.env`, paste your key after `ANTHROPIC_API_KEY=`, then `docker compose up -d` |
| `port is already allocated` | Another app uses 8000 or 8501 | See "Ports already in use?" above |
| UI shows "API offline" for a few minutes on first start | `shop.db` is being built from the CSVs | Wait; follow along with `docker compose logs -f api` |

## The web app

- Chat with the agents, and start, reopen or delete conversations from the sidebar.
- Charts are interactive: hover, zoom, or download them as PNG.
- Each chat shows its question count, **API cost**, tokens and average response time.
- Each answer shows which agent handled it, its cost and time, and a
  **"How I got this answer"** panel with every step and SQL query.

Try "Show monthly net revenue for 2023 as a line chart", and then "Now compare
that by product category as a bar chart".

## Use the API directly

### Windows (PowerShell)

```powershell
$body = @{ message = "What was net revenue in 2023?"; thread_id = "demo" } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/chat -Method Post -ContentType application/json -Body $body
```

### Mac (Terminal)

```bash
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message": "What was net revenue in 2023?", "thread_id": "demo"}'
```

| Endpoint | What it does |
|---|---|
| `POST /chat` | Ask a question. Returns the answer, charts, steps, tokens, cost and time. |
| `GET /history/{thread_id}` | Every turn of a conversation, plus its memory summary |
| `GET /threads` | Recent conversations with their titles and cost |
| `DELETE /threads/{thread_id}` | Delete a conversation |
| `GET /health` | Status, model and tables |

## Test it

Run these in a second window while the app is running. They are the same on Windows and Mac.

```bash
docker compose exec api python tests/backtest.py
```

```bash
docker compose exec api python -m evals.run
```

- **Backtest 1** (29 checks, free): the data load, all 4 tools, every chart type,
  the SQL guardrails and the memory window.
- **Backtest 2** (17 tasks, under 1 cent on Claude Haiku 5.5): real questions, follow-ups, memory
  recall, charts, small talk, a year with no data, and an unsafe request. Each
  answer is scored on 10 metrics.

## Agent evals

There is one short file per metric in `evals/metrics/`. The test set is
`evals/test_set.json`, and the right answers are computed live from the database.

| Metric | Question it answers | Latest |
|---|---|---|
| Task Completion Rate | Did it finish with an answer? | 100% |
| Success Rate | Was the answer (or chart) right? | 100% |
| Tool Call Accuracy | Did its tool calls work? | 100% |
| Planning Accuracy | Right agent, right steps first? | 96% |
| Trajectory Accuracy | How close to the ideal tool sequence? | 94% |
| Hallucination Rate | Answers with an unsupported number (lower is better) | 0% |
| Groundedness Score | Share of numbers backed by tool output | 100% |
| Human Intervention Rate | Tasks needing a person (lower is better) | 0% |
| Latency | Seconds per task | 3.0 s median |
| Cost Per Task | US dollars per question | $0.0005 |

Latest scores are for `claude-haiku-5-5` (Nov 2026).

See `REPORT.md` for the details.

## Models and cost

The provider is picked from whichever key is in `.env` (Anthropic first, then
OpenAI, then Groq), or set `LLM_PROVIDER=` to choose.

| Provider | Default | Price per 1M tokens (in / out) | Change with |
|---|---|---|---|
| **Anthropic** | **`claude-haiku-5-5`** | **$0.10 / $0.50** | `LLM_MODEL=` in `.env` |
| OpenAI | `gpt-5.4-mini` | $0.75 / $4.50 | `LLM_MODEL=` in `.env` |
| Groq | `openai/gpt-oss-120b` | see Groq pricing | `LLM_MODEL=` in `.env` |

**Why Haiku 5.5 is the default.** The work here is tool calling plus short,
number-quoting answers, and the database does the heavy lifting. Haiku 5.5 passed
every backtest at about **$0.0005 per question**, roughly 8x cheaper than
`gpt-5.4-mini` and faster too (3.0 s median vs 4.9 s).

**Need more reasoning?** Set `LLM_MODEL=claude-sonnet-5-5` ($2 / $10). The router
and the memory summary keep running on Haiku (`LLM_FAST_MODEL`), so you only pay
Sonnet prices where the analysis happens. Opus is not needed for this workload.
