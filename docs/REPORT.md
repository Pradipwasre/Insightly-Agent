# Insightly Lite: test report

## Version 3: Anthropic Claude (Nov 2026)

Date: 23 Nov 2026 · Model: Anthropic `claude-haiku-5-5`

### What was added

- **Anthropic provider** (`app/llm.py`, `app/config.py`, `langchain-anthropic` in
  `requirements.txt`). Set `ANTHROPIC_API_KEY` in `.env`. OpenAI and Groq still work
  exactly as before; with no `LLM_PROVIDER`, the Anthropic key wins.
- **Cost-efficient model choice.** Default `claude-haiku-5-5` for every agent. If
  `LLM_MODEL` is raised to Sonnet, the router and memory summary stay on Haiku
  (`LLM_FAST_MODEL`). Claude prices added to `PRICES`, so the app and evals show real cost.
- **Provider safety fixes.** The router now always starts its context with a user
  message (Claude requires this), and answers are read as plain text even if the
  provider returns content blocks.

### Model choice

| Model | Price per 1M tokens (in / out) | Fit for this app |
|---|---|---|
| **claude-haiku-5-5** | **$0.10 / $0.50** | **Default.** Passed every test, fastest |
| claude-sonnet-5-5 | $2 / $10 | Upgrade for harder multi-step analysis |
| claude-opus-5-5 | $4 / $20 | Overkill for SQL + short answers |
| gpt-5.4-mini (before) | $0.75 / $4.50 | Same quality on our tests, ~8x the cost |

### Backtest results (run before finalising)

The backtests ran on the real CSVs, minus the 385 MB `events` file, so the one
conversion-rate case (and its row-count check) was left out.

| Test | Result |
|---|---|
| Backtest 1 (data, tools, charts, guardrails, memory window) | **28 / 28 passed** (events check skipped) |
| Backtest 2, run 1 | 15 / 16 passed, hallucination 12% |
| Backtest 2, final | **16 / 16 passed** |
| 9-turn memory test | The name from turn 1 was recalled at turn 9, from the summary |
| Server log | No errors or tracebacks |

| Metric | gpt-5.4-mini (v2) | claude-haiku-5-5 (v3) |
|---|---|---|
| Task Completion / Success / Tool Call Accuracy | 100% / 100% / 100% | 100% / 100% / 100% |
| Planning / Trajectory Accuracy | 96% / 94% | 96% / 94% |
| Hallucination Rate / Groundedness | 0% / 100% | 0% / 100% |
| Latency (mean / median / p95) | 7.1 / 4.9 / 27.0 s | **3.1 / 3.0 / 5.7 s** |
| Cost per task | $0.0019 | **$0.0005** |

| Route | Avg input tokens | Avg output tokens | Avg cost | Avg time |
|---|---|---|---|---|
| Analyst (numbers) | 3,714 | 258 | $0.0005 | 3.0 s |
| Chart | 5,635 | 706 | $0.0009 | 4.8 s |
| Chat | 667 | 98 | $0.0001 | 1.6 s |

At 1,000 questions a day this is about **$0.60 a day, or about $18 a month** (was about $60).
All the live testing together cost under 3 cents.

### What the backtest caught

1. **Derived numbers.** Haiku computed its own "89% growth" and a "remaining 18.61%"
   share. These were correct arithmetic, but not in the data, so the hallucination
   rate was 12%. Two rules were added to the analyst and chart prompts for Claude
   only (`CLAUDE_RULES` in `app/graph.py`): don't calculate new numbers unless asked,
   and don't show your reasoning. After that the rate was 0%. The OpenAI prompts are unchanged.
2. **Scorer too strict.** For 2030, the answer "There is no net revenue data for 2030"
   was right, but it didn't match the scorer's word list. Added "no net revenue",
   "no gross profit" and "can't report" to `evals/metrics/success_rate.py`.
3. **Memory timing (all providers).** A fact that drops out of the 6-turn window
   reaches the summary right *after* that turn's answer. So for one turn (turn 7) it
   is in neither the window nor the summary. From turn 8 on, it is recalled. This is
   how the existing design works, and the code is left as it is.

---

## Version 2: web app, chart agent, summary memory

Date: 14 Nov 2026 · Model: OpenAI `gpt-5.4-mini` · Runtime: Docker Desktop (Windows 11)

### What was added

- **Streamlit web app** (`ui/app.py`). It has a conversation sidebar, per-chat
  stats (questions, API cost, tokens, average response time), interactive charts,
  and per-answer cost and time. A "How I got this answer" panel shows every step and SQL query.
- **Chart agent** with a Plotly tool (`app/charts.py`, `make_chart` in
  `app/tools.py`). It draws line, bar, area, pie and scatter charts in an analyst
  style: sorted bars, data labels, the peak called out on trends, and one colour
  palette. The agent gets a numeric summary of each chart, so its insights quote real numbers.
- **Router with 3 routes:** analyst, chart, and chat.
- **Two-layer memory.** Every message is saved per conversation. The LLM sees the
  last 6 turns plus a running summary of older ones.
- **API additions:** cost per answer, `GET /threads`, `DELETE /threads/{id}`, and
  a richer `/history`.
- **Docker:** the API and the UI run as two services, with a health check. The ports
  can be changed with `API_PORT` and `UI_PORT`.

### Results

| Test | Result |
|---|---|
| Backtest 1 (data, tools, 5 chart types, guardrails, memory window) | **29 / 29 passed** |
| Backtest 2 (17 tasks incl. 3 charts + memory recall) | **17 / 17 passed** |
| Live UI test in the browser | Line chart, then the follow-up "now compare that by category as a bar chart" understood from memory |
| 9-turn memory test | Turns 1-3 were summarised. The agent still recalled the user's name, their favourite category and the 2021 revenue |

| Metric | Final |
|---|---|
| Task Completion / Success / Tool Call Accuracy | 100% / 100% / 100% |
| Planning / Trajectory Accuracy | 96% / 94% |
| Hallucination Rate / Groundedness | 0% / 100% |
| Human Intervention Rate | 0% |
| Latency (mean / median / p95) | 7.1 s / 4.9 s / 27.0 s |

### Cost by type of question

| Route | Avg input tokens | Avg output tokens | Avg cost | Avg time |
|---|---|---|---|---|
| Analyst (numbers) | 2,085 | 109 | $0.0021 | 8.8 s |
| Chart | 2,472 | 192 | $0.0027 | 5.3 s |
| Chat | 359 | 67 | $0.0006 | 2.4 s |

At 1,000 questions a day this is roughly **$2 a day, or about $60 a month**.

### What the evals caught in version 2

1. **Derived numbers.** The chart agent added two pie shares together (correct
   arithmetic, but not in the data), so the hallucination check flagged it. The
   prompt now says to quote numbers exactly as given and not to calculate new ones,
   and the hallucination rate went from 6% to 0%.
2. **Misleading shares.** Pie shares are of the slices shown, not of all users. The
   chart summary now says so, and the agent's wording followed.
3. **Over-complex SQL.** The agent once joined 3 tables for a category question, hit
   the 60 s limit and retried (105 s in total). A "keep SQL simple" hint fixed it (now 7 s).
4. **Eval clean-up.** Test chats appeared in the app's sidebar, so the eval runner
   now deletes its own conversations.

### Known limits

- Questions that scan all 2.4M website events (conversion rate) take about 25 s.
- The memory summary costs one extra small LLM call once a chat passes 6 turns.
  That call is not included in the per-answer cost.

---

# Version 1

## Summary

The agent answers questions over the full e-commerce dataset (7 tables, 3.3 million
rows). It passed all 21 checks in backtest 1, a live end-to-end run with memory
follow-ups, and **13 of 13 tasks in backtest 2**, with 0% hallucination. It costs
about **$0.002 per question**.

## 1. Data wiring

The CSVs in `data files/` are loaded into `data/shop.db` on first start (157 s, one time only).

| Table | Rows |
|---|---|
| events | 2,427,931 |
| inventory_items | 491,098 |
| order_items | 181,891 |
| orders | 125,530 |
| users | 100,000 |
| products | 29,120 |
| distribution_centers | 10 |

The loader cleans the data on the way in:
- `" UTC"` is dropped from timestamps, so SQLite date functions work.
- Empty cells become NULL.
- Postal codes and SKUs stay text, so leading zeros are kept.
- Key columns are indexed.
- The database is built under a temporary name first, so a crash never leaves half a database behind.

The data folder is mounted read-only. It is git-ignored and kept out of the Docker image.

## 2. Model choice

I checked OpenAI's live model list with the key. `gpt-5.4-mini` is the newest "mini"
model. Mini is the tier most teams use in production because it balances quality
and price: $0.75 per 1M input tokens and $4.50 per 1M output tokens.

## 3. Backtest 1: build, health, tools, SQL safety

`docker compose exec api python tests/backtest.py`: **21 passed, 0 failed**.

- All 7 tables have exactly the same row count as their CSV.
- Date handling works, postal codes stay text, and empty cells are NULL.
- All three tools work, and SQL errors go back to the LLM so it can fix its query.
- `DELETE`, `DROP`, `UPDATE`, `WITH … DELETE` and `SELECT 1; DROP …` are all blocked, and the data is unchanged afterwards.
- The `/health` endpoint reports the provider, the model and all 7 tables.

## 4. End-to-end run with memory (Docker Desktop)

| # | Question (same `thread_id`) | Tools | Answer | Time |
|---|---|---|---|---|
| 1 | What was net revenue in 2023? | get_schema, lookup_metric, run_sql | $3,356,336.16 | 6 s |
| 2 | And in 2022? | run_sql | $1,772,494.37 | 4 s |
| 3 | Which of the two years was higher, and by how much? | none (from memory) | 2023, by $1,583,841.79 | 2 s |

The history was still there after `docker compose restart`. Memory is stored in
`data/memory.db`, so it survives restarts.

**Bug found and fixed:** at first, every follow-up crashed with an OpenAI 400 error.
The router took the last 6 messages, and that slice could cut a tool result off from
the tool call it belonged to. The router now reads only questions and final answers
(`app/graph.py`).

## 5. Backtest 2: agent evals

`docker compose exec api python -m evals.run` runs the 13 tasks in
`evals/test_set.json`:
- 10 data questions, including one memory follow-up
- 1 small-talk message
- 1 question about a year with no data (2030)
- 1 unsafe request ("delete all cancelled orders")

The right answer for each question is computed live from the database.

### How the scores changed

| Metric | Run 1 | Run 2 | Final |
|---|---|---|---|
| Task Completion Rate | 100% | 100% | **100%** |
| Success Rate | 85% | 92% | **100%** |
| Tool Call Accuracy | 92% | 96% | **100%** |
| Planning Accuracy | 90% | 97% | **97%** |
| Trajectory Accuracy | 82% | 90% | **97%** |
| Hallucination Rate (lower is better) | 0% | 0% | **0%** |
| Groundedness Score | 100% | 100% | **100%** |
| Human Intervention Rate (lower is better) | 0% | 0% | **0%** |
| Latency mean / p50 / p95 | 5.8 / 4.6 / 6.8 s* | 6.2 / 5.2 / 23.7 s | **6.1 / 4.8 / 25.6 s** |
| Cost per task | $0.0018 | $0.0018 | **$0.0019** (13 tasks = $0.024) |

\* Run 1's p95 was understated because of a rounding bug in `latency.py`. It is fixed.

### What the evals caught and what changed

1. **Wrong route (run 1).** "Net revenue in 2030?" was sent to small talk, and the
   agent asked the user to share a report. I made the router's instructions explicit:
   any shop question goes to the data path.
2. **Misleading zero (run 2).** For 2030 the agent said "net revenue was 0", which
   reads as if 2030 had zero sales. The agent prompt now says to report "no data"
   for an empty period.
3. **Tried to run a DELETE (run 2).** The read-only guardrail blocked it, so no data
   changed. The prompt now says to refuse changes without calling `run_sql` at all.
4. **Query timeout.** The conversion-rate query scans all 2.4M events and takes
   about 20 s, which hit the old 20 s limit and forced a retry. An index did not
   help (18 s), so the limit is now 60 s.
5. **Bugs in my own scoring.** The refusal check did not handle curly apostrophes
   (’), and p95 latency rounded down. Both are fixed.

### Known limits

- Numbers are matched to tool output with code, not with an LLM judge. That makes it
  cheap and repeatable, but it can miss a claim that is wrong without being a number.
- 13 tasks is a smoke test, not a benchmark. Add cases to `test_set.json` to grow it.
- Only the conversion-rate question is slow, because it reads the whole `events`
  table. A pre-aggregated sessions table would fix that.
- Planning is 97% because the agent skips the metric lookup for "how many orders",
  a count it can write without the glossary.
- One refusal contained a stray non-English token. This is model output noise, and
  the meaning was intact.

## 6. Security

- The API key exists only in `.env`. I searched the project and the built image for
  it, and it is in neither.
- `.env` is listed in both `.gitignore` and `.dockerignore`.
- The agent's database connection is read-only (`mode=ro`), and every query has a time limit.
