"""Vector index for A's text sources: SQLite (chunks, metadata, embedding cache) + FAISS (vectors).

Team decision 17 Nov 2026: add embeddings + FAISS + SQLite to A's retrieval. Keyword search stays as the fallback.

Chunks (one per natural unit; no splitting or overlap needed — the longest is ~310 characters):
  email  = one complaint email (subject + body)       key = email source_id
  policy = one Resolution Guide rule row or note     key = "<ref>|<locator>"
Stored in SQLite with their source, exact locator, category, date, order numbers and guide version, so every
vector hit maps back to a verifiable citation. FAISS holds only the vectors, keyed by the SQLite row id.

PDPA (PR #13 review P1): every text that is embedded — index chunks AND search queries — goes through
masking.privacy_guard first (emails, phones, NRIC, unit, postal, block, street addresses, personal names). The API
embedder applies it again just before the request, so nothing unguarded can leave the machine even if a caller
forgets. The unmasked text stays only in the local SQLite file under output/ (git-ignored).

Cost control: vectors are cached in SQLite by sha256(model + masked text), so a rebuild only embeds new or changed
chunks. The index records the sha256 of its source files; if they change, search reports INDEX_STALE and the caller
falls back to keyword search until `python -m backend.unstructured.build_index` is rerun.

Damaged files (PR #13 review P2): the SQLite file records the sha256 of the FAISS file and of the local embedder file
it was built with. The SQLite write is one transaction; the other files are written to a temp file and swapped in
(os.replace), so a reader never sees half a file. A partial, foreign or unreadable file is refused as INDEX_CORRUPT,
and search falls back to keyword instead of crashing.

Needs `faiss-cpu` and `numpy` (backend/unstructured/requirements.txt). Without them, search reports NO_FAISS and
keyword search is used.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .masking import privacy_guard

try:  # optional dependency: everything else in A works without it
    import faiss  # type: ignore
    import numpy as np  # type: ignore
    HAVE_FAISS = True
except ImportError:  # pragma: no cover - exercised by patching HAVE_FAISS in tests
    faiss = None
    np = None
    HAVE_FAISS = False

INDEX_VERSION = "a-vec-3"  # a-vec-2: privacy_guard on embedded text, file checksums (PR #13 review);
# a-vec-3: guard also catches CAPS / lower-case names and numbered addresses, so the embedded text changed (PR #14 review)
DB_NAME = "a_index.sqlite"
FAISS_NAME = "a_index.faiss"
LOCAL_EMBED_NAME = "local_embed.npz"
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


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    """Write to a temp file beside the target, flush it to disk, then swap it in one step (old file or new, never half)."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        with tmp.open("wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


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
                     "embed_text": privacy_guard(f"{r.get('subject') or ''}. {body.strip()}")[0]})
    for c in _load_jsonl(policy_path) if policy_path.is_file() else []:
        rows.append({"chunk_key": policy_key(c), "kind": "policy", "source_id": c["source_id"], "ref": c["ref"],
                     "locator": c["locator"], "heading": c.get("heading"),
                     "category": json.dumps(c.get("email_categories") or []), "received_at": None,
                     "order_numbers": "[]", "guide_version": c.get("guide_version"), "text": c["text"],
                     "embed_text": privacy_guard(f"{c.get('heading') or ''}. {c['text']}")[0]})
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
    files: Dict[str, bytes] = {}  # written (atomically) only after the SQLite transaction commits
    if is_local(model):
        from .local_embed import LocalEmbedder
        fitted = LocalEmbedder.fit([r["embed_text"] for r in rows])
        files[LOCAL_EMBED_NAME] = fitted.to_bytes()
        embedder = fitted
    elif embedder is None:
        raise VectorUnavailable("NO_EMBEDDER", f"no embedder for model {model!r}")
    con = None
    try:
        con = sqlite3.connect(folder / DB_NAME)
        con.executescript(SCHEMA)
    except sqlite3.Error as exc:
        if con is not None:
            con.close()
        raise VectorUnavailable("INDEX_CORRUPT", f"index database unreadable ({exc}); delete {folder} and rebuild "
                                                 "(API vectors will be re-embedded)") from exc
    try:
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
        files[FAISS_NAME] = faiss.serialize_index(index).tobytes()
        meta = {"index_version": INDEX_VERSION, "embed_model": model, "dim": str(dim),
                "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "chunks": str(len(rows)), "emails": str(sum(r["kind"] == "email" for r in rows)),
                "policy": str(sum(r["kind"] == "policy" for r in rows)), "sources_sha256": _sources_sha(out_dir),
                "min_similarity": str(LOCAL_MIN_SIMILARITY if is_local(model) else MIN_SIMILARITY),
                "faiss_sha256": _sha(files[FAISS_NAME]),
                "local_embed_sha256": _sha(files[LOCAL_EMBED_NAME]) if LOCAL_EMBED_NAME in files else ""}
        con.execute("DELETE FROM meta")
        con.executemany("INSERT INTO meta (key, value) VALUES (?, ?)", meta.items())
        con.commit()
    finally:
        con.close()
    _CACHE.clear()
    # If a write below fails or the process dies here, the checksums in SQLite no longer match the files, so load()
    # refuses the index (INDEX_CORRUPT -> keyword fallback) instead of mapping vectors to the wrong chunks.
    try:
        for name, data in files.items():
            _atomic_write(folder / name, data)
    except OSError as exc:
        raise VectorUnavailable("INDEX_WRITE_FAILED", f"could not write the index files ({exc}); rerun build_index") from exc
    return {**meta, "embedded_now": len(todo), "reused_from_cache": len(rows) - len(todo),
            "prompt_tokens": usage["prompt_tokens"]}


class VectorIndex:
    """A loaded index. Every way the files can be damaged ends in VectorUnavailable, never a raw FAISS/SQLite error."""

    def __init__(self, folder: Path):
        self.folder = folder
        try:
            con = sqlite3.connect(folder / DB_NAME)
            try:
                con.row_factory = sqlite3.Row
                self.meta = {k: v for k, v in con.execute("SELECT key, value FROM meta")}
                self.rows = {r["id"]: dict(r) for r in con.execute(
                    "SELECT id, chunk_key, kind, source_id, ref, locator, heading, category, received_at, order_numbers "
                    "FROM chunks")}
            finally:
                con.close()
        except sqlite3.Error as exc:
            raise VectorUnavailable("INDEX_CORRUPT", f"index database unreadable ({exc}); rerun build_index") from exc
        if self.meta.get("index_version") != INDEX_VERSION:
            raise VectorUnavailable("INDEX_STALE", f"index format {self.meta.get('index_version')!r}, this code reads "
                                                   f"{INDEX_VERSION!r}; rerun build_index")
        try:  # every value search() relies on is checked here, so a damaged meta row cannot crash a query later
            self.min_similarity = float(self.meta.get("min_similarity", MIN_SIMILARITY))
            dim = int(self.meta.get("dim", 0))
        except (TypeError, ValueError) as exc:
            raise VectorUnavailable("INDEX_CORRUPT", f"index metadata unreadable ({exc}); rerun build_index") from exc
        if not (0.0 <= self.min_similarity <= 1.0) or dim <= 0:
            raise VectorUnavailable("INDEX_CORRUPT", f"index metadata out of range (min_similarity="
                                                     f"{self.meta.get('min_similarity')!r}, dim={self.meta.get('dim')!r}); "
                                                     "rerun build_index")
        try:
            raw = (folder / FAISS_NAME).read_bytes()
        except OSError as exc:
            raise VectorUnavailable("INDEX_MISSING", f"FAISS file unreadable ({exc}); rerun build_index") from exc
        if _sha(raw) != self.meta.get("faiss_sha256"):
            raise VectorUnavailable("INDEX_CORRUPT", "FAISS file does not match the index database (partial write or "
                                                     "files from different builds); rerun build_index")
        try:
            self.index = faiss.deserialize_index(np.frombuffer(raw, dtype="uint8"))
        except (RuntimeError, ValueError, TypeError) as exc:
            raise VectorUnavailable("INDEX_CORRUPT", f"FAISS file unreadable ({exc}); rerun build_index") from exc
        if self.index.ntotal != len(self.rows):
            raise VectorUnavailable("INDEX_CORRUPT", f"FAISS holds {self.index.ntotal} vectors but the database has "
                                                     f"{len(self.rows)} chunks; rerun build_index")
        self._query_cache: Dict[str, "np.ndarray"] = {}

    def search(self, query: str, embedder: Embedder, *, kind: Optional[str] = None,
               min_similarity: Optional[float] = None) -> List[Tuple[float, Dict[str, Any]]]:
        if min_similarity is None:
            min_similarity = self.min_similarity
        masked = privacy_guard(query)[0]  # same guard as the indexed text; names/addresses never reach the embedder
        if masked not in self._query_cache:
            vectors, _ = embedder([masked])
            matrix = np.asarray(vectors, dtype="float32")
            if matrix.ndim != 2 or matrix.shape != (1, self.index.d):
                raise VectorUnavailable("INDEX_STALE", f"query vector shape {matrix.shape} does not fit the index "
                                                       f"(dim {self.index.d}); embedder and index differ, rerun build_index")
            self._query_cache[masked] = _normalise(matrix)
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
            raw = (vi.folder / LOCAL_EMBED_NAME).read_bytes()
        except FileNotFoundError as exc:
            raise VectorUnavailable("INDEX_MISSING", f"local embedder file missing: {exc}") from exc
        except OSError as exc:
            raise VectorUnavailable("INDEX_CORRUPT", f"local embedder file unreadable: {exc}") from exc
        if _sha(raw) != vi.meta.get("local_embed_sha256"):
            raise VectorUnavailable("INDEX_CORRUPT", "local embedder file does not match the index; rerun build_index")
        try:
            return LocalEmbedder.from_bytes(raw)
        except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile) as exc:
            raise VectorUnavailable("INDEX_CORRUPT", f"local embedder file invalid: {exc}") from exc
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
        guarded = [privacy_guard(t)[0] for t in texts]  # last line of defence: this is where text leaves the machine
        try:
            return llm.embed_texts(guarded, api_key=cfg["api_key"], model=cfg["embed_model"], base_url=cfg["base_url"],
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
    try:
        stamp = ((folder / FAISS_NAME).stat().st_mtime_ns, (folder / DB_NAME).stat().st_mtime_ns)
    except OSError as exc:
        raise VectorUnavailable("INDEX_MISSING", "vector index not built; run python -m backend.unstructured.build_index") from exc
    key = str(folder.resolve())
    if key not in _CACHE or _CACHE[key][0] != stamp:
        _CACHE.pop(key, None)
        _CACHE[key] = (stamp, VectorIndex(folder))  # raises VectorUnavailable on any damaged file; nothing cached
    vi = _CACHE[key][1]
    if vi.meta.get("sources_sha256") != _sources_sha(out_dir):
        raise VectorUnavailable("INDEX_STALE", "ingest outputs changed since the index was built; rerun build_index")
    return vi
