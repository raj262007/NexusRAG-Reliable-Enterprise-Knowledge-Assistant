import logging
from typing import List, Dict, Any, Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OLLAMA_SETUP_GUIDE = """
Ollama is not reachable at {base_url}.
To run NexusRAG locally with Ollama:
1. Install Ollama:
   - Windows: Run `winget install Ollama.Ollama` or download from https://ollama.com/download
2. Start the Ollama server:
   - Run `ollama serve`
3. Pull a lightweight model (recommended for 16GB RAM / 4GB VRAM):
   - `ollama pull qwen2.5:3b` (or `llama3.2:3b` / `mistral:7b`)
4. Verify by running `ollama list`
"""


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def is_available(self) -> bool:
        """Check if local Ollama server is responding."""
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """List models installed locally in Ollama."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", []) if "name" in m]
                    return models
                return []
        except Exception as e:
            logger.debug("Failed to list Ollama models: %s", e)
            return []

    def check_status(self) -> Dict[str, Any]:
        """Return diagnostic status information for Ollama."""
        installed = self.is_available()
        models = self.list_models() if installed else []
        model_ready = self.default_model in models or any(
            m.startswith(self.default_model) for m in models
        )

        return {
            "available": installed,
            "base_url": self.base_url,
            "configured_model": self.default_model,
            "installed_models": models,
            "model_ready": model_ready,
            "instructions": None if installed else OLLAMA_SETUP_GUIDE.format(base_url=self.base_url)
        }

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1
    ) -> str:
        """
        Send a generation request to the local Ollama HTTP API.
        Never falls back silently to cloud LLMs.
        """
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            }
        }
        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )

                if response.status_code == 404:
                    available = self.list_models()
                    raise RuntimeError(
                        f"Ollama model '{target_model}' not found on local instance. "
                        f"Installed models: {available}. "
                        f"Run `ollama pull {target_model}` to download it."
                    )

                response.raise_for_status()
                data = response.json()
                answer = data.get("response", "").strip()
                return answer

        except httpx.ConnectError as exc:
            msg = (
                f"Cannot connect to local Ollama runtime at {self.base_url}. "
                f"Make sure Ollama is installed and running (`ollama serve`).\n"
                f"{OLLAMA_SETUP_GUIDE.format(base_url=self.base_url)}"
            )
            logger.error(msg)
            raise ConnectionError(msg) from exc

        except httpx.TimeoutException as exc:
            msg = f"Ollama generation timed out after {self.timeout} seconds for model '{target_model}'."
            logger.error(msg)
            raise TimeoutError(msg) from exc

        except Exception as exc:
            if isinstance(exc, (RuntimeError, ConnectionError, TimeoutError)):
                raise
            logger.error("Ollama API error: %s", exc)
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc
