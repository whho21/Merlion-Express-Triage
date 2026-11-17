"""Minimal client for the class OpenAI-compatible endpoint (standard library only).

Key:      OPENAI_API_KEY from the environment, else from the TEAM repo's own .env (repo root only). Parent folders
          are never searched, so a course/class key sitting in a parent folder is never spent by accident.
Base URL: OPENAI_BASE_URL (default https://api.openai.com/v1).
Model:    A_VISION_MODEL (default gpt-4o-mini).
Retries:  bounded (3 attempts, 2 s then 4 s backoff), only on 429 / 5xx / network errors.
Telemetry: one JSON line per call in output/unstructured/telemetry.jsonl — ids, tokens, latency, status.
          Never the prompt, the image or the model's answer (they can hold personal data).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"
RETRYABLE_HTTP = {408, 409, 429, 500, 502, 503, 504}
TEAM_BUDGET_USD = 50.0  # team key sheet, 16 Nov: hard budget for the whole project, monitored weekly

# US$ per 1M tokens (input, output), OpenAI list prices; image tokens are already inside prompt_tokens.
# Estimates only: the provider's usage page is the source of truth. Unknown model -> cost None.
PRICES_USD_PER_MTOK = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
    "text-embedding-3-small": (0.02, 0.0),
    "text-embedding-3-large": (0.13, 0.0),
    "text-embedding-ada-002": (0.10, 0.0),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    price = PRICES_USD_PER_MTOK.get(model)
    if price is None:
        return None
    return round((prompt_tokens * price[0] + completion_tokens * price[1]) / 1_000_000, 6)

# transport(url, headers, body, timeout) -> (http_status, response_body). Injected in tests; no network there.
Transport = Callable[[str, Dict[str, str], bytes, float], Tuple[int, bytes]]


class LLMError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False):
        super().__init__(message)
        self.code, self.retryable = code, retryable

    def as_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": str(self), "retryable": self.retryable}


def read_dotenv(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def settings(repo_root: Path) -> Dict[str, Optional[str]]:
    env_file = read_dotenv(repo_root / ".env")
    pick = lambda name, default=None: os.environ.get(name) or env_file.get(name) or default  # noqa: E731
    return {"api_key": pick("OPENAI_API_KEY"), "base_url": pick("OPENAI_BASE_URL", DEFAULT_BASE_URL),
            "model": pick("A_VISION_MODEL", DEFAULT_MODEL), "embed_model": pick("A_EMBED_MODEL", DEFAULT_EMBED_MODEL)}


def _urllib_transport(url: str, headers: Dict[str, str], body: bytes, timeout: float) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def log_telemetry(path: Optional[Path], **fields: Any) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **fields}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(fields) + "\n")


def _post_with_retries(url: str, api_key: str, body: bytes, transport: Transport, timeout: float, max_attempts: int,
                       sleep: Callable[[float], None]) -> Tuple[Optional[bytes], int, int, Optional[LLMError]]:
    """POST JSON with bounded retries (429 / 5xx / network only). Returns (body, attempts, latency_ms, error)."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    started = time.monotonic()
    attempt, error, raw = 0, None, None
    while attempt < max_attempts:
        attempt += 1
        try:
            status, raw = transport(url, headers, body, timeout)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            error = LLMError("NETWORK", f"{type(exc).__name__}: {exc}", retryable=True)
        else:
            if status == 200:
                error = None
                break
            error = LLMError(f"HTTP_{status}", f"endpoint returned HTTP {status}", retryable=status in RETRYABLE_HTTP)
        if not error.retryable or attempt >= max_attempts:
            break
        sleep(2 ** attempt)
    return raw, attempt, int((time.monotonic() - started) * 1000), error


def embed_texts(texts: List[str], *, api_key: Optional[str], model: str = DEFAULT_EMBED_MODEL,
                base_url: str = DEFAULT_BASE_URL, tool: str, telemetry_path: Optional[Path] = None,
                transport: Optional[Transport] = None, timeout: float = 60.0, max_attempts: int = 3,
                sleep: Callable[[float], None] = time.sleep, batch_size: int = 96
                ) -> Tuple[List[List[float]], Dict[str, int]]:
    """Embed texts with the class endpoint, in batches. Returns (vectors in input order, token usage).

    Callers must mask personal data first: whatever is passed here leaves the machine.
    Telemetry records counts, tokens and cost only, never the texts.
    """
    if not api_key:
        raise LLMError("NO_API_KEY", "OPENAI_API_KEY is not set in the environment or the team repo .env")
    transport = transport or _urllib_transport
    url = base_url.rstrip("/") + "/embeddings"
    vectors: List[List[float]] = []
    total = 0
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        body = json.dumps({"model": model, "input": batch}).encode("utf-8")
        raw, attempt, latency_ms, error = _post_with_retries(url, api_key, body, transport, timeout, max_attempts, sleep)
        common = dict(tool=tool, model=model, items=len(batch), attempts=attempt, latency_ms=latency_ms, cache="miss")
        if error is not None:
            log_telemetry(telemetry_path, status="failed", error=error.code, prompt_tokens=0, **common)
            raise error
        try:
            payload = json.loads(raw)
            rows = sorted(payload["data"], key=lambda d: d["index"])
            batch_vectors = [[float(x) for x in row["embedding"]] for row in rows]
            if len(batch_vectors) != len(batch):
                raise ValueError(f"{len(batch_vectors)} vectors for {len(batch)} texts")
        except (ValueError, KeyError, TypeError) as exc:
            log_telemetry(telemetry_path, status="failed", error="BAD_RESPONSE", prompt_tokens=0, **common)
            raise LLMError("BAD_RESPONSE", f"could not read the embedding response: {exc}") from exc
        tokens = int((payload.get("usage") or {}).get("prompt_tokens", 0))
        total += tokens
        vectors.extend(batch_vectors)
        log_telemetry(telemetry_path, status="ok", prompt_tokens=tokens, cost_usd=estimate_cost(model, tokens, 0), **common)
    return vectors, {"prompt_tokens": total, "completion_tokens": 0}


def vision_json(image: bytes, mime: str, prompt: str, *, api_key: Optional[str], model: str,
                base_url: str = DEFAULT_BASE_URL, tool: str, source_id: str, prompt_version: str,
                telemetry_path: Optional[Path] = None, transport: Optional[Transport] = None,
                timeout: float = 60.0, max_attempts: int = 3, sleep: Callable[[float], None] = time.sleep
                ) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Send one image + prompt, return (parsed JSON answer, token usage). Raises LLMError on failure."""
    if not api_key:
        raise LLMError("NO_API_KEY", "OPENAI_API_KEY is not set in the environment or the team repo .env")
    transport = transport or _urllib_transport
    data_url = f"data:{mime};base64,{base64.b64encode(image).decode('ascii')}"
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
        ]}],
    }).encode("utf-8")
    url = base_url.rstrip("/") + "/chat/completions"
    raw, attempt, latency_ms, error = _post_with_retries(url, api_key, body, transport, timeout, max_attempts, sleep)
    common = dict(tool=tool, source_id=source_id, model=model, prompt_version=prompt_version, attempts=attempt,
                  latency_ms=latency_ms, cache="miss")
    if error is not None:
        log_telemetry(telemetry_path, status="failed", error=error.code, prompt_tokens=0, completion_tokens=0,
                      **common)
        raise error

    try:
        payload = json.loads(raw)
        content = payload["choices"][0]["message"]["content"]
        answer = json.loads(content)
        if not isinstance(answer, dict):
            raise ValueError("answer is not a JSON object")
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        log_telemetry(telemetry_path, status="failed", error="BAD_RESPONSE", prompt_tokens=0, completion_tokens=0,
                      **common)
        raise LLMError("BAD_RESPONSE", f"could not read the model's JSON answer: {exc}") from exc
    usage = payload.get("usage") or {}
    tokens = {"prompt_tokens": int(usage.get("prompt_tokens", 0)),
              "completion_tokens": int(usage.get("completion_tokens", 0))}
    log_telemetry(telemetry_path, status="ok", **tokens,
                  cost_usd=estimate_cost(model, tokens["prompt_tokens"], tokens["completion_tokens"]), **common)
    return answer, tokens
