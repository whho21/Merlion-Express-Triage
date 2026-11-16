"""Extraction cache (Developer A, task 6): never pay twice for the same image, prompt and model.

Key = sha256(image) + prompt_version + model. A changed image, prompt or model is a new key, so it is re-read
deliberately; anything else is served from output/unstructured/cache/ (git-ignored — answers hold personal data).
Only successful answers are cached, so failed reads are retried on the next run.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


def cache_key(image_sha256: str, prompt_version: str, model: str) -> str:
    return hashlib.sha256(f"{image_sha256}|{prompt_version}|{model}".encode("utf-8")).hexdigest()[:32]


class ExtractionCache:
    def __init__(self, directory: Path):
        self.directory = directory

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        path = self._path(key)
        if not path.is_file():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return None  # a damaged cache file is treated as a miss and overwritten

    def put(self, key: str, value: Dict[str, Any]) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        tmp = self._path(key).with_suffix(".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(self._path(key))
