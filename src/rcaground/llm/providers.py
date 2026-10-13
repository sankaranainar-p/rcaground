"""
OpenAI-compatible chat provider configuration shared by LLM baselines.

Provider priority:
  1. Groq   (cloud) when GROQ_API_KEY is set
  2. Ollama (local) when OLLAMA_BASE_URL is set
  3. None   callers must degrade gracefully (for example, return an empty
            ranking) so the test suite and benchmarks run fully offline.

Environment variables:
    GROQ_API_KEY      Groq API key (activates Groq provider)
    GROQ_MODEL        Groq model tag (default: llama3-8b-8192)
    OLLAMA_BASE_URL   Base URL of the local Ollama server
    OLLAMA_MODEL      Ollama model tag (default: llama3.1)
"""

from __future__ import annotations

import os


def _groq_api_key() -> str:
    return os.getenv("GROQ_API_KEY", "")

def _groq_configured() -> bool:
    return bool(_groq_api_key())

def _groq_url() -> str:
    return "https://api.groq.com/openai/v1/chat/completions"

def _groq_model() -> str:
    return os.getenv("GROQ_MODEL", "llama3-8b-8192")

def _ollama_configured() -> bool:
    return bool(os.getenv("OLLAMA_BASE_URL"))

def _ollama_url() -> str:
    base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    return f"{base}/v1/chat/completions"

def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "llama3.1")
