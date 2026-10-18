import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_GRAPH = os.getenv("FALKORDB_GRAPH", "ImpactGraph")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)

# Google Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Multi-Provider LLM Configuration: OpenRouter, OpenAI, Groq, Local Ollama
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", None)
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# In-memory dynamic override for live UI demo
_dynamic_settings = {}


def get_llm_config() -> dict:
    """Resolve active LLM provider configuration (Dynamic > Gemini > OpenRouter > OpenAI)."""
    # Check dynamic UI settings first
    if _dynamic_settings.get("api_key"):
        provider = _dynamic_settings.get("provider", "openrouter")
        return {
            "api_key": _dynamic_settings["api_key"],
            "base_url": _dynamic_settings.get("base_url") or OPENROUTER_BASE_URL,
            "model": _dynamic_settings.get("model") or OPENROUTER_MODEL,
            "provider": provider,
        }

    # Gemini (Google)
    if GEMINI_API_KEY:
        return {
            "api_key": GEMINI_API_KEY,
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model": GEMINI_MODEL,
            "provider": "gemini",
        }

    # OpenRouter
    if OPENROUTER_API_KEY:
        return {
            "api_key": OPENROUTER_API_KEY,
            "base_url": OPENROUTER_BASE_URL,
            "model": OPENROUTER_MODEL,
            "provider": "openrouter",
        }

    # OpenAI
    if OPENAI_API_KEY:
        return {
            "api_key": OPENAI_API_KEY,
            "base_url": OPENAI_BASE_URL,
            "model": OPENAI_MODEL,
            "provider": "openai",
        }

    return {
        "api_key": None,
        "base_url": None,
        "model": None,
        "provider": "none",
    }


def set_dynamic_llm_config(api_key: str, model: str | None = None, provider: str = "gemini", is_openrouter: bool = False):
    """Set dynamic LLM credentials at runtime from the UI settings modal."""
    _dynamic_settings["api_key"] = api_key
    _dynamic_settings["provider"] = provider
    if provider == "gemini":
        _dynamic_settings["base_url"] = "https://generativelanguage.googleapis.com/v1beta"
        _dynamic_settings["model"] = model or GEMINI_MODEL
    elif provider == "openrouter" or is_openrouter:
        _dynamic_settings["provider"] = "openrouter"
        _dynamic_settings["base_url"] = OPENROUTER_BASE_URL
        _dynamic_settings["model"] = model or OPENROUTER_MODEL
    else:
        _dynamic_settings["provider"] = "openai"
        _dynamic_settings["base_url"] = OPENAI_BASE_URL
        _dynamic_settings["model"] = model or OPENAI_MODEL


MAX_FILES_TO_SELECT = int(os.getenv("MAX_FILES_TO_SELECT", "30"))
MAX_FILES_TO_FETCH = int(os.getenv("MAX_FILES_TO_FETCH", "12"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "200000"))
