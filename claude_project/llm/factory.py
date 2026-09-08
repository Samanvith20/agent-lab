"""Create LangChain models from the project configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv
from claude_project.config.config import config
from claude_project.observability.logger import get_logger

logger = get_logger(__name__)


def get_llm():
    """Return the configured chat model."""
    provider = config["llm"]["provider"]
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    key_name = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}.get(provider)
    if key_name and not os.getenv(key_name, "").strip():
        raise ValueError(f"Set {key_name} in the project .env file.")
    model = config["llm"]["model"]
    logger.info("Using LLM provider: %s, model: %s", provider, model)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model)
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, timeout=60, max_retries=1)
    raise ValueError(f"Unsupported LLM provider: {provider}")


def get_embedder():
    """Return the configured embedding model."""
    provider = config["embeddings"]["provider"]
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    if provider == "openai" and not os.getenv("OPENAI_API_KEY", "").strip():
        raise ValueError("Set OPENAI_API_KEY in the project .env file.")
    model = config["embeddings"]["model"]
    logger.info("Using embeddings provider: %s, model: %s", provider, model)
    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=model)
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=model, request_timeout=60, max_retries=1)
    raise ValueError(f"Unsupported embeddings provider: {provider}")
