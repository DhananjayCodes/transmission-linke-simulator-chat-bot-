"""Offline language-model bridge for the engineering assistant.

The bridge talks only to a local Ollama server.  It deliberately has no cloud
fallback: if Ollama or the selected model is unavailable, callers receive
``None`` and can use the deterministic engineering engine instead.
"""

import json
import os
import urllib.error
import urllib.request


class LocalLLM:
    """Small adapter around an optionally installed, local Ollama model."""

    def __init__(self):
        self.enabled = os.environ.get("POWER_ASSISTANT_LOCAL_LLM", "1") != "0"
        self.model = os.environ.get("POWER_ASSISTANT_MODEL", "qwen2.5:3b")
        self.url = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        self._unavailable = False

    def answer(self, question, system_context=""):
        """Return an answer from a local model, or None when it is unavailable."""
        if not self.enabled or self._unavailable:
            return None

        prompt = (
            "You are an offline power-transmission engineering assistant. "
            "Answer the user's question directly and concisely. Use the supplied "
            "system context when relevant. Do not invent calculated values, standards, "
            "or sources. Say when information is insufficient.\n\n"
            f"System context:\n{system_context or 'No active simulation values.'}\n\n"
            f"User question: {question}"
        )
        body = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 300},
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
                answer = data.get("response", "").strip()
                return answer or None
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            # Do not repeatedly delay the GUI when the local runtime is absent.
            self._unavailable = True
            return None
