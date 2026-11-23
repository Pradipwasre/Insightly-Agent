"""All settings in one place. Values come from environment variables (.env)."""
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# "anthropic", "openai" or "groq". Empty = pick whichever key is set.
PROVIDER = os.getenv("LLM_PROVIDER", "") or (
    "anthropic" if ANTHROPIC_API_KEY else "openai" if OPENAI_API_KEY else "groq")

DEFAULT_MODELS = {"anthropic": "claude-haiku-5-5", "openai": "gpt-5.4-mini", "groq": "openai/gpt-oss-120b"}
MODEL = os.getenv("LLM_MODEL", "") or DEFAULT_MODELS[PROVIDER]

# Model for the small background jobs (routing a question, summarising old turns).
# On Anthropic it is always the cheapest model, so upgrading LLM_MODEL to Sonnet
# only pays the higher price where the reasoning happens. Elsewhere: same as MODEL.
FAST_MODELS = {"anthropic": "claude-haiku-5-5"}
FAST_MODEL = os.getenv("LLM_FAST_MODEL", "") or FAST_MODELS.get(PROVIDER, MODEL)

CSV_DIR = os.getenv("CSV_DIR", "data files")     # your CSV files (file name = table name)
DATA_DIR = os.getenv("DATA_DIR", "data")         # files the app creates
SHOP_DB = os.path.join(DATA_DIR, "shop.db")      # the business data (read-only for the agent)
MEMORY_DB = os.path.join(DATA_DIR, "memory.db")  # LangGraph checkpoints (chat memory)

# Price per 1M tokens in US dollars (standard tier, checked Nov 2026)
PRICES = {"gpt-5.4-mini": {"input": 0.75, "output": 4.50},
          "gpt-5.4-nano": {"input": 0.20, "output": 1.25},
          "gpt-5.4": {"input": 2.50, "output": 15.00},
          # Anthropic: Haiku price is for prompts up to 100K tokens (ours are ~2-3K)
          "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
          "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
          "claude-opus-5-5": {"input": 4.00, "output": 20.00}}


def cost_usd(tokens, model=MODEL):
    p = PRICES.get(model, PRICES["gpt-5.4-mini"])
    return (tokens["input"] * p["input"] + tokens["output"] * p["output"]) / 1_000_000
