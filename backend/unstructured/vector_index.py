"""Vector index for A's text sources: SQLite (chunks, metadata, embedding cache) + FAISS (vectors).

Team decision 17 Nov 2026: add embeddings + FAISS + SQLite to A's retrieval. Keyword search stays as the fallback.

Chunks (one per natural unit; no splitting or overlap needed — the longest is ~310 characters):
  email  = one complaint email (subject + body)       key = email source_id
  policy = one Resolution Guide rule row or note     key = "<ref>|<locator>"
Stored in SQLite with their source, exact locator, category, date, order numbers and guide version, so every
vector hit maps back to a verifiable citation. FAISS holds only the vectors, keyed by the SQLite row id.

PDPA: the text sent to the embedding endpoint is MASKED first (masking.mask_text: emails, phones, NRIC, unit,
postal, block). The unmasked text stays only in the local SQLite file under output/ (git-ignored).

Cost control: vectors are cached in SQLite by sha256(model + masked text), so a rebuild only embeds new or changed
chunks. The index records the sha256 of its source files; if they change, search reports INDEX_STALE and the caller
falls back to keyword search until `python -m backend.unstructured.build_index` is rerun.

Needs `faiss-cpu` and `numpy` (backend/unstructured/requirements.txt). Without them, search reports NO_FAISS and
keyword search is used.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .masking import mask_text

try:  # optional dependency: everything else in A works without it
    import faiss  # type: ignore
    import numpy as np  # type: ignore
    HAVE_FAISS = True
except ImportError:  # pragma: no cover - exercised by patching HAVE_FAISS in tests
    faiss = None
    np = None
    HAVE_FAISS = False

INDEX_VERSION = "a-vec-1"
DB_NAME = "a_index.sqlite"
FAISS_NAME = "a_index.faiss"
SOURCE_FILES = ("emails.jsonl", "policy_chunks.jsonl")
MIN_SIMILARITY = 0.30  # cosine, API embeddings: below this a hit is "not relevant". PROVISIONAL until the first
                       # API build (the team key had no credit on 17 Nov).
LOCAL_MIN_SIMILARITY = 0.10  # cosine, local TF-IDF embeddings; calibrated 17 Nov on real data (see handoff)

Embedder = Callable[[List[str]], Tuple[List[List[float]], Dict[str, int]]]

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY,
  chunk_key TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL,
  source_id TEXT NOT NULL,
  ref TEXT,
  locator TEXT,
  heading TEXT,
  category TEXT,
  received_at TEXT,
  order_numbers TEXT,
  guide_version TEXT,
  text TEXT NOT NULL,
  embed_text TEXT NOT NULL,
  embed_key TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS embedding_cache (key TEXT PRIMARY KEY, model TEXT NOT NULL, dim INTEGER NOT NULL,
                                            vector BLOB NOT NULL);
"""


class VectorUnavailable(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def index_dir(out_dir: Path) -> Path:
    return out_dir / "index"


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _sources_sha(out_dir: Path) -> str:
    h = hashlib.sha256()
    for name in SOURCE_FILES:
        path = out_dir / name
        h.update(name.encode())
        h.update(path.read_bytes() if path.is_file() else b"")
    return h.hexdigest()


def email_key(record: Dict[str, Any]) -> str:
    return record["source_id"]


def policy_key(chunk: Dict[str, Any]) -> str:
    return f"{chunk['ref']}|{chunk['locator']}"


def collect_chunks(out_dir: Path) -> List[Dict[str, Any]]:
    """Read the ingest outputs and return index rows in a stable order."""
    rows: List[Dict[str, Any]] = []
    emails_path, policy_path = out_dir / "emails.jsonl", out_dir / "policy_chunks.jsonl"
    if not emails_path.is_file():
        raise VectorUnavailable("INDEX_MISSING", "emails.jsonl not found; run python -m backend.unstructured.ingest")
    for r in _load_jsonl(emails_path):
        if r.get("status") == "failed" or not (r.get("body") or "").strip():
            continue
        body = r["body"]
        start, end = len(body) - len(body.lstrip()), len(body.rstrip())
        rows.append({"chunk_key": email_key(r), "kind": "email", "source_id": r["source_id"], "ref": r["ref"],
                     "locator": f"body:char:{start}-{end}", "heading": r.get("subject"), "category": r.get("category"),
                     "received_at": r.get("received_at"), "order_numbers": json.dumps(r.get("order_numbers") or []),
                     "guide_version": None, "text": body,
                     "embed_text": mask_text(f"{r.get('subject') or ''}. {body.strip()}")[0]})
    for c in _load_jsonl(policy_path) if policy_path.is_file() else []:
        rows.append({"chunk_key": policy_key(c), "kind": "policy", "source_id": c["source_id"], "ref": c["ref"],
                     "locator": c["locator"], "heading": c.get("heading"),
                     "category": json.dumps(c.get("email_categories") or []), "received_at": None,
                     "order_numbers": "[]", "guide_version": c.get("guide_version"), "text": c["text"],
                     "embed_text": mask_text(f"{c.get('heading') or ''}. {c['text']}")[0]})
    rows.sort(key=lambda r: (r["kind"], r["chunk_key"]))
    return rows


def _embed_key(model: str, text: str) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode("utf-8")).hexdigest()


def _normalise(matrix: "np.ndarray") -> "np.ndarray":
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (matrix / norms).astype("float32")


def is_local(model: str) -> bool:
    return (model or "").startswith("local-")


def build(out_dir: Path, *, model: str, embedder: Optional[Embedder] = None) -> Dict[str, Any]:
    """(Re)build SQLite + FAISS from the ingest outputs.

    model "local-…": numpy TF-IDF embeddings fitted on this corpus (free, offline; embedder ignored).
    any other model: the given embedder (API); only new/changed chunks are sent, the rest come from the cache.
    """
    if not HAVE_FAISS:
        raise VectorUnavailable("NO_FAISS", "faiss-cpu / numpy not installed (pip install -r backend/unstructured/requirements.txt)")
    rows = collect_chunks(out_dir)
    folder = index_dir(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    if is_local(model):
        from .local_embed import LocalEmbedder
        fitted = LocalEmbedder.fit([r["embed_text"] for r in rows])
        fitted.save(folder)
        embedder = fitted
    elif embedder is None:
        raise VectorUnavailable("NO_EMBEDDER", f"no embedder for model {model!r}")
    con = sqlite3.connect(folder / DB_NAME)
    try:
        con.executescript(SCHEMA)
        if is_local(model):  # vectors depend on the fitted IDF, so never reuse cached local vectors
            con.execute("DELETE FROM embedding_cache WHERE model = ?", (model,))
        for row in rows:
            row["embed_key"] = _embed_key(model, row["embed_text"])
        cached = {k for (k,) in con.execute("SELECT key FROM embedding_cache WHERE model = ?", (model,))}
        todo = list({r["embed_key"]: r["embed_text"] for r in rows if r["embed_key"] not in cached}.items())
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if todo:
            vectors, usage = embedder([text for _, text in todo])
            for (key, _), vec in zip(todo, vectors):
                arr = np.asarray(vec, dtype="float32")
                con.execute("INSERT OR REPLACE INTO embedding_cache (key, model, dim, vector) VALUES (?, ?, ?, ?)",
                            (key, model, int(arr.shape[0]), arr.tobytes()))
        con.execute("DELETE FROM chunks")
        cols = ["chunk_key", "kind", "source_id", "ref", "locator", "heading", "category", "received_at",
                "order_numbers", "guide_version", "text", "embed_text", "embed_key"]
        for i, row in enumerate(rows, start=1):
            con.execute(f"INSERT INTO chunks (id, {', '.join(cols)}) VALUES (?, {', '.join('?' * len(cols))})",
                        [i] + [row[c] for c in cols])
        vecs = []
        for row in rows:
            blob, dim = con.execute("SELECT vector, dim FROM embedding_cache WHERE key = ?", (row["embed_key"],)).fetchone()
            vecs.append(np.frombuffer(blob, dtype="float32", count=dim))
        dim = int(vecs[0].shape[0]) if vecs else 0
        index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
        if vecs:
            index.add_with_ids(_normalise(np.vstack(vecs)), np.arange(1, len(rows) + 1, dtype="int64"))
        faiss.write_index(index, str(folder / FAISS_NAME))
        meta = {"index_version": INDEX_VERSION, "embed_model": model, "dim": str(dim),
                "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "chunks": str(len(rows)), "emails": str(sum(r["kind"] == "email" for r in rows)),
                "policy": str(sum(r["kind"] == "policy" for r in rows)), "sources_sha256": _sources_sha(out_dir),
                "min_similarity": str(LOCAL_MIN_SIMILARITY if is_local(model) else MIN_SIMILARITY)}
        con.execute("DELETE FROM meta")
        con.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", meta.items())
        con.commit()
    finally:
        con.close()
    _CACHE.clear()
    return {**meta, "embedded_now": len(todo), "reused_from_cache": len(rows) - len(todo),
            "prompt_tokens": usage["prompt_tokens"]}


class VectorIndex:
    def __init__(self, folder: Path):
        self.folder = folder
        self.index = faiss.read_index(str(folder / FAISS_NAME))
        con = sqlite3.connect(folder / DB_NAME)
        try:
            con.row_factory = sqlite3.Row
            self.meta = {k: v for k, v in con.execute("SELECT key, value FROM meta")}
            self.rows = {r["id"]: dict(r) for r in con.execute(
                "SELECT id, chunk_key, kind, source_id, ref, locator, heading, category, received_at, order_numbers "
                "FROM chunks")}
        finally:
            con.close()
        self._query_cache: Dict[str, "np.ndarray"] = {}

    def search(self, query: str, embedder: Embedder, *, kind: Optional[str] = None,
               min_similarity: Optional[float] = None) -> List[Tuple[float, Dict[str, Any]]]:
        if min_similarity is None:
            min_similarity = float(self.meta.get("min_similarity", MIN_SIMILARITY))
        masked = mask_text(query)[0]  # mask the query the same way the indexed text was masked
        if masked not in self._query_cache:
            vectors, _ = embedder([masked])
            self._query_cache[masked] = _normalise(np.asarray(vectors, dtype="float32"))
        scores, ids = self.index.search(self._query_cache[masked], max(1, self.index.ntotal))
        hits = []
        for score, i in zip(scores[0], ids[0]):
            row = self.rows.get(int(i))
            if row is None or (kind and row["kind"] != kind) or float(score) < min_similarity:
                continue
            hits.append((round(float(score), 4), row))
        return hits


def query_embedder(vi: "VectorIndex", out_dir: Path) -> Embedder:
    """The embedder that matches how this index was built (never mix models between index and query)."""
    model = vi.meta.get("embed_model", "")
    if is_local(model):
        from .local_embed import LocalEmbedder
        try:
            return LocalEmbedder.load(vi.folder)
        except (OSError, ValueError, KeyError) as exc:
            raise VectorUnavailable("INDEX_MISSING", f"local embedder file missing or invalid: {exc}") from exc
    return make_embedder(out_dir, tool="embed_query", model=model)[0]


def make_embedder(out_dir: Path, tool: str, model: Optional[str] = None) -> Tuple[Optional[Embedder], str]:
    """Embedder from the team repo .env. A_EMBED_MODEL unset -> local TF-IDF (free, offline; returns None and
    build() fits it). Set A_EMBED_MODEL=text-embedding-3-small to use the class endpoint with the TEAM key."""
    from . import llm  # local import: keeps this module importable without the network layer in tests
    cfg = llm.settings(Path.cwd())
    model = model or cfg["embed_model"] or "local-tfidf-chargram-v1"
    if is_local(model):
        return None, model
    cfg = {**cfg, "embed_model": model}

    def embed(texts: List[str]) -> Tuple[List[List[float]], Dict[str, int]]:
        try:
            return llm.embed_texts(texts, api_key=cfg["api_key"], model=cfg["embed_model"], base_url=cfg["base_url"],
                                   tool=tool, telemetry_path=out_dir / "telemetry.jsonl")
        except llm.LLMError as exc:
            raise VectorUnavailable(f"EMBED_{exc.code}", str(exc)) from exc
    return embed, cfg["embed_model"]


_CACHE: Dict[str, Tuple[float, VectorIndex]] = {}


def load(out_dir: Path) -> VectorIndex:
    """Load (and memoise) the index, refusing a missing or stale one with a coded reason."""
    if not HAVE_FAISS:
        raise VectorUnavailable("NO_FAISS", "faiss-cpu / numpy not installed")
    folder = index_dir(out_dir)
    if not (folder / FAISS_NAME).is_file() or not (folder / DB_NAME).is_file():
        raise VectorUnavailable("INDEX_MISSING", "vector index not built; run python -m backend.unstructured.build_index")
    stamp = (folder / FAISS_NAME).stat().st_mtime
    key = str(folder.resolve())
    if key not in _CACHE or _CACHE[key][0] != stamp:
        _CACHE[key] = (stamp, VectorIndex(folder))
    vi = _CACHE[key][1]
    if vi.meta.get("sources_sha256") != _sources_sha(out_dir):
        raise VectorUnavailable("INDEX_STALE", "ingest outputs changed since the index was built; rerun build_index")
    return vi
