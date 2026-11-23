"""One function that returns a chat model: Anthropic, OpenAI or Groq, same interface."""
from app import config


def get_llm(model=None):
    model = model or config.MODEL
    if config.PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        # max_tokens caps the answer length (and so the worst-case cost); answers here are short
        return ChatAnthropic(model=model, api_key=config.ANTHROPIC_API_KEY, max_tokens=2048,
                             max_retries=3, timeout=120)
    if config.PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, api_key=config.OPENAI_API_KEY)
    if config.PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=config.GROQ_API_KEY)
    raise ValueError(f"Unknown LLM_PROVIDER: {config.PROVIDER}")
