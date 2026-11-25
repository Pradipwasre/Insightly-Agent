# GenAI Interview Questions

## 1. LLM Cost & Tokens

**Q. How is the cost of an LLM API call calculated?**

## 2. Output Tokens & Cost Control

**Q. Why are output tokens more expensive than input tokens, and what does that mean for cost control?**

## 3. Cost Per Task / Workflow

**Q. At what level should you track LLM cost: per model call or per task/workflow?**

## 4. Real LLM Billing

**Q. Beyond input and output tokens, what else affects the real LLM bill?**

## 5. Hallucination Detection & Reduction

**Q. How do you detect and reduce hallucinations in an LLM application?**

## 6. Hallucination Rate vs Groundedness

**Q. How do you measure the hallucination rate of an LLM application, and why track it separately from a groundedness (faithfulness) score?**

## 7. Human Intervention & Agent Autonomy

**Q. How do you measure how autonomous an AI agent is, and when should an agent escalate to a human?**

## 8. LLM Latency

**Q. Why do we report p50 and p95 latency for an LLM application instead of just the average, and how would you reduce latency?**

## 9. Planning Accuracy

**Q. How do you evaluate the planning and tool-selection ability of an AI agent? For example, how would you check that an agent routes a request to the right agent or tool, and uses its tools in the right order, before it takes any action?**

## 10. Success Rate

**Q. What is the difference between task completion and task success rate for an AI agent, and how do you measure whether the final answer is actually correct when the tasks are of different types (data questions, chat, charts, unsafe requests, and "no data" cases)?**

## 11. Task Completion Rate

**Q. How do you make an LLM agent reliable in production, so that it doesn't crash, time out, or return an empty answer? Explain how you would handle failures such as tool errors, timeouts and API errors (retries, fallbacks, graceful degradation), and how you would measure the share of tasks that finish successfully.**

## 12. Tool Call Accuracy

**Q. What is tool hallucination in LLM function calling (for example, calling a tool that doesn't exist, passing wrong or missing arguments, or calling a tool at the wrong time)? How do you measure tool call accuracy, and how do you validate and recover from invalid tool calls in production?**

## 13. Trajectory Accuracy

**Q. What is trajectory evaluation for an AI agent, and how is it different from evaluating only the final answer? Explain the common ways to compare an agent's actual sequence of tool calls with an ideal one (exact match, in-order match, any-order match, precision and recall), and when you would use each.**

## 14. Number Grounding & Normalization

**Q. How would you verify the numbers an LLM states in its answer against the source data, given that the model may write the same value in different formats (for example "1,234,567", "1.2M", "$1.23 million" or "12%") and may round it? How do you extract and normalize numbers from text, decide when two numbers count as a match (exact match vs rounding vs tolerance), and avoid false alarms from harmless numbers like "top 3"?**
