"""Local embeddings with numpy only: no API, no download, no cost (team decision 17 Nov, API out of credit).

Each text becomes a TF-IDF vector over hashed features:
  - word unigrams and bigrams          ("thrown", "over gate")
  - character 3- to 5-grams per word   ("thr", "thro", "hrow" ...) -> robust to typos and word forms
                                         ("parcle" ~ "parcel", "threw/thrown/throw" share "thr")
Sublinear term frequency, IDF fitted on the indexed corpus, L2-normalised, so FAISS inner product = cosine.

What it is NOT: a language model. It does not know that "smashed" means "damaged" unless the words or their
pieces overlap. The OpenAI embedding backend (llm.embed_texts) does; switch with A_EMBED_MODEL when credit returns.
The fitted IDF is saved next to the index (local_embed.npz) so queries use exactly the same transform.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

MODEL_NAME = "local-tfidf-chargram-v1"
DIM = 2 ** 14
WORD_RE = re.compile(r"[a-z0-9]+")
NPZ_NAME = "local_embed.npz"


def _features(text: str) -> List[str]:
    words = WORD_RE.findall((text or "").lower())
    feats = [f"w:{w}" for w in words]
    feats += [f"b:{a}_{b}" for a, b in zip(words, words[1:])]
    for w in words:
        padded = f"<{w}>"
        for n in (3, 4, 5):
            feats += [f"c:{padded[i:i + n]}" for i in range(max(0, len(padded) - n + 1))]
    return feats


def _bucket(feature: str) -> int:
    return int.from_bytes(hashlib.blake2b(feature.encode("utf-8"), digest_size=4).digest(), "little") % DIM


def _counts(texts: List[str]) -> np.ndarray:
    m = np.zeros((len(texts), DIM), dtype="float32")
    for i, text in enumerate(texts):
        for f in _features(text):
            m[i, _bucket(f)] += 1.0
    np.log1p(m, out=m)  # sublinear tf
    return m


class LocalEmbedder:
    model = MODEL_NAME

    def __init__(self, idf: np.ndarray):
        self.idf = idf.astype("float32")

    @classmethod
    def fit(cls, corpus: List[str]) -> "LocalEmbedder":
        df = (_counts(corpus) > 0).sum(axis=0)
        n = max(1, len(corpus))
        return cls(np.log((1 + n) / (1 + df)) + 1.0)

    def __call__(self, texts: List[str]) -> Tuple[List[List[float]], Dict[str, int]]:
        m = _counts(texts) * self.idf
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (m / norms).tolist(), {"prompt_tokens": 0, "completion_tokens": 0}

    def save(self, folder: Path) -> None:
        np.savez_compressed(folder / NPZ_NAME, idf=self.idf, dim=np.array([DIM]))

    @classmethod
    def load(cls, folder: Path) -> "LocalEmbedder":
        data = np.load(folder / NPZ_NAME)
        if int(data["dim"][0]) != DIM:
            raise ValueError("local embedder was saved with a different dimension; rebuild the index")
        return cls(data["idf"])
