import os
from typing import Protocol
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt.
            system: Optional system message.

        Returns:
            The generated text response.
        """
        pass


class OllamaClient(LLMClient):
    """Client for local Ollama inference."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        """Initialize the Ollama client.

        Args:
            base_url: Base URL for Ollama API.
            model: Model name to use.
        """
        self.base_url = base_url
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate a response using Ollama.

        Args:
            prompt: The user prompt.
            system: Optional system message.

        Returns:
            The generated text response.
        """
        import requests

        # Construct full prompt with system message if provided
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                },
                timeout=300,
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")


class GroqClient(LLMClient):
    """Client for Groq API."""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        """Initialize the Groq client.

        Args:
            api_key: Groq API key.
            model: Model name to use.
        """
        from groq import Groq

        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        """Generate a response using Groq.

        Args:
            prompt: The user prompt.
            system: Optional system message.

        Returns:
            The generated text response.
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=1,
                max_tokens=1024,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")


def get_llm_client() -> LLMClient:
    """Get an LLM client based on environment configuration.

    Reads LLM_PROVIDER environment variable (default: "ollama").
    - "ollama": Returns OllamaClient, configured via OLLAMA_BASE_URL env var.
    - "groq": Returns GroqClient, configured via GROQ_API_KEY env var.

    Returns:
        An LLMClient instance.

    Raises:
        ValueError: If LLM_PROVIDER is invalid or required env vars are missing.
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaClient(base_url=base_url)
    elif provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable must be set when using Groq provider")
        return GroqClient(api_key=api_key)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Must be 'ollama' or 'groq'")
