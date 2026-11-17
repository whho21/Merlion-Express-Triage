"""Vector index (SQLite + FAISS) and hybrid search, with a fake embedder: no network, no spend.

The fake embedder hashes words into a small vector, so texts sharing words are close — enough to test the
plumbing (build, cache, masking, filters, thresholds, fallbacks) deterministically.
"""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from backend.unstructured import search, vector_index

DIM = 64


def fake_vector(text):
    vec = [0.0] * DIM
    for word in text.lower().replace(".", " ").replace(",", " ").split():
        vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
    return vec


class FakeEmbedder:
    def __init__(self):
        self.calls = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        return [fake_vector(t) for t in texts], {"prompt_tokens": 7 * len(texts), "completion_tokens": 0}


def email(stem, order, category, subject, body):
    return {"source_id": f"email:{stem}", "ref": f"data/docs/complaint_emails/{stem}.txt", "status": "ok",
            "subject": subject, "category": category, "is_complaint": category != "compliment",
            "order_numbers": [order] if order else [], "received_at": "2026-03-02T10:00:00+08:00", "body": body}


def rule(row, heading, text, cats):
    return {"source_id": "policy:g", "ref": "data/tabular/g.xlsx", "locator": f"sheet:Guide|row:{row}",
            "heading": heading, "text": text, "email_categories": cats, "fields": {"Resolution": text}}


EMAILS = [email("a", "20001", "thrown_over_gate", "Parcel thrown", "Driver threw parcel over gate, item smashed. Call 91234567."),
          email("b", "20002", "late", "Late again", "Parcel late again, third time this month."),
          email("c", None, "compliment", "Compliment", "Driver very polite and helpful.")]
RULES = [rule(5, "Late delivery", "late parcel apology or refund delivery fee", ["late"]),
         rule(7, "Damaged / thrown parcel", "parcel damaged smashed thrown refund item value", ["thrown_over_gate"])]


@unittest.skipUnless(vector_index.HAVE_FAISS, "faiss-cpu/numpy not installed")
class VectorIndexTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        self.write(EMAILS, RULES)
        vector_index._CACHE.clear()

    def tearDown(self):
        vector_index._CACHE.clear()
        self._tmp.cleanup()

    def write(self, emails, rules):
        (self.out / "emails.jsonl").write_text("\n".join(json.dumps(e) for e in emails) + "\n", encoding="utf-8")
        (self.out / "policy_chunks.jsonl").write_text("\n".join(json.dumps(r) for r in rules) + "\n", encoding="utf-8")
        (self.out / "manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")

    def build(self, embedder=None):
        embedder = embedder or FakeEmbedder()
        return vector_index.build(self.out, model="fake-model", embedder=embedder), embedder

    def test_build_writes_sqlite_and_faiss_with_citations(self):
        summary, emb = self.build()
        self.assertEqual((summary["chunks"], summary["emails"], summary["policy"]), ("5", "3", "2"))
        self.assertEqual((summary["embedded_now"], summary["prompt_tokens"]), (5, 35))
        folder = vector_index.index_dir(self.out)
        self.assertTrue((folder / vector_index.FAISS_NAME).is_file())
        con = sqlite3.connect(folder / vector_index.DB_NAME)
        row = con.execute("SELECT kind, locator, text, embed_text FROM chunks WHERE chunk_key = 'email:a'").fetchone()
        con.close()
        self.assertEqual(row[0], "email")
        self.assertTrue(row[1].startswith("body:char:0-"))
        self.assertIn("91234567", row[2])        # local copy keeps the full text for citations
        self.assertNotIn("91234567", row[3])     # what is sent to the embedding endpoint is masked
        self.assertFalse(any("91234567" in t for batch in emb.calls for t in batch))

    def test_rebuild_reuses_cache_and_only_embeds_changes(self):
        self.build()
        again, emb2 = self.build()
        self.assertEqual((again["embedded_now"], emb2.calls), (0, []))
        changed = [dict(EMAILS[0], body="Completely new wording about a gate.")] + EMAILS[1:]
        self.write(changed, RULES)
        third, emb3 = self.build()
        self.assertEqual((third["embedded_now"], len(emb3.calls[0])), (1, 1))

    def test_vector_search_filters_by_kind_and_threshold(self):
        self.build()
        vi = vector_index.load(self.out)
        hits = vi.search("parcel smashed thrown", FakeEmbedder(), kind="policy", min_similarity=0.1)
        self.assertEqual(hits[0][1]["heading"], "Damaged / thrown parcel")
        self.assertTrue(all(h[1]["kind"] == "policy" for h in hits))
        self.assertEqual(vi.search("zzz qqq", FakeEmbedder(), kind="policy", min_similarity=0.5), [])

    def test_stale_index_is_refused(self):
        self.build()
        self.write(EMAILS[:2], RULES)
        with self.assertRaises(vector_index.VectorUnavailable) as ctx:
            vector_index.load(self.out)
        self.assertEqual(ctx.exception.code, "INDEX_STALE")

    def test_hybrid_policy_search_uses_vectors_and_labels_it(self):
        self.build()
        res = search.search_policy("item smashed", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual((res["status"], res["data"][0]["heading"]), ("found", "Damaged / thrown parcel"))
        self.assertEqual(res["retrieval"], "hybrid:keyword+fake-model")
        self.assertEqual(res["data"][0]["citation"]["locator"], "sheet:Guide|row:7")

    def test_vector_email_hit_keeps_an_exact_citation(self):
        self.build()
        res = search.search_emails("smashed gate", mode="vector", out_dir=self.out, embedder=FakeEmbedder())
        hit = res["data"][0]
        a, b = map(int, hit["citation"]["locator"].split(":")[-1].split("-"))
        self.assertEqual(EMAILS[0]["body"][a:b], hit["text"])
        self.assertEqual(res["retrieval"], "vector:fake-model")

    def test_order_filter_still_exact_with_hybrid(self):
        self.build()
        res = search.search_emails("parcel", order_number="20002", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual(res["sources"], ["email:b"])

    # --- PR #13 review P1: names and street addresses never reach the embedder -------------------------------------
    def test_query_names_and_addresses_never_reach_the_embedder(self):
        self.build()
        emb = FakeEmbedder()
        vector_index.load(self.out).search("Customer Jane Tan of 123 Orchard Road, call 91234567, parcel smashed", emb)
        sent = " ".join(t for batch in emb.calls for t in batch)
        for leak in ("Jane", "Tan", "Orchard", "91234567"):
            self.assertNotIn(leak, sent)
        self.assertIn("parcel smashed", sent)

    def test_indexed_chunks_are_guarded_before_embedding(self):
        self.write([email("d", "20003", "late", "Late", "Regards, Priya Sharma, Blk 5 Tampines St 11. Parcel late.")],
                   RULES)
        _, emb = self.build()
        sent = " ".join(t for batch in emb.calls for t in batch)
        for leak in ("Priya", "Sharma", "Tampines"):
            self.assertNotIn(leak, sent)

    def test_api_embedder_guards_text_at_the_network_boundary(self):
        from backend.unstructured import llm
        captured = []

        def fake_embed_texts(texts, **kwargs):
            captured.extend(texts)
            return [[1.0, 0.0] for _ in texts], {"prompt_tokens": 1, "completion_tokens": 0}
        cfg = {"api_key": "test-key", "base_url": "http://unused", "model": "m", "embed_model": "text-embedding-3-small"}
        with mock.patch.object(llm, "settings", return_value=cfg), \
                mock.patch.object(llm, "embed_texts", side_effect=fake_embed_texts):
            embed, model = vector_index.make_embedder(self.out, tool="embed_query")
            embed(["Mdm Siti binte Omar at 123 Orchard Road: parcel late"])
        self.assertEqual(model, "text-embedding-3-small")
        self.assertEqual(captured, ["[NAME] at [ADDRESS]: parcel late"])

    # --- PR #13 review P2: damaged index files fall back to keyword, never crash -------------------------------------
    def assertFallsBack(self, code):
        vector_index._CACHE.clear()
        res = search.search_policy("late parcel", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual((res["status"], res["retrieval"]), ("found", f"keyword (fallback: {code})"))
        strict = search.search_policy("late parcel", mode="vector", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual((strict["ok"], strict["error"]["code"]), (False, code))

    def test_truncated_faiss_file_falls_back(self):  # the reviewer's repro
        self.build()
        path = vector_index.index_dir(self.out) / vector_index.FAISS_NAME
        path.write_bytes(path.read_bytes()[: path.stat().st_size // 2])
        self.assertFallsBack("INDEX_CORRUPT")

    def test_unparseable_faiss_with_matching_checksum_falls_back(self):
        self.build()
        folder = vector_index.index_dir(self.out)
        junk = b"not a faiss index"
        (folder / vector_index.FAISS_NAME).write_bytes(junk)
        con = sqlite3.connect(folder / vector_index.DB_NAME)
        con.execute("UPDATE meta SET value = ? WHERE key = 'faiss_sha256'", (hashlib.sha256(junk).hexdigest(),))
        con.commit()
        con.close()
        self.assertFallsBack("INDEX_CORRUPT")

    def test_garbage_database_falls_back(self):
        self.build()
        (vector_index.index_dir(self.out) / vector_index.DB_NAME).write_bytes(b"\x00garbage" * 64)
        self.assertFallsBack("INDEX_CORRUPT")

    def test_files_from_different_builds_are_refused(self):
        self.build()
        folder = vector_index.index_dir(self.out)
        other = Path(self._tmp.name) / "other"
        other.mkdir()
        (other / "emails.jsonl").write_text("\n".join(json.dumps(e) for e in reversed(EMAILS)) + "\n", encoding="utf-8")
        (other / "policy_chunks.jsonl").write_bytes((self.out / "policy_chunks.jsonl").read_bytes())
        vector_index.build(other, model="fake-model", embedder=lambda texts: (
            [fake_vector(t + " other build") for t in texts], {"prompt_tokens": 0, "completion_tokens": 0}))
        (folder / vector_index.FAISS_NAME).write_bytes((vector_index.index_dir(other) / vector_index.FAISS_NAME).read_bytes())
        self.assertFallsBack("INDEX_CORRUPT")

    def test_crash_between_database_and_faiss_swap_is_detected(self):
        self.build()
        self.write([email("z", "20009", "late", "Late", "Totally different parcel complaint.")] + EMAILS, RULES)
        real = vector_index._atomic_write

        def die_on_faiss(path, data):
            if path.name == vector_index.FAISS_NAME:
                raise OSError("disk full")
            real(path, data)
        with mock.patch.object(vector_index, "_atomic_write", side_effect=die_on_faiss):
            with self.assertRaises(vector_index.VectorUnavailable) as ctx:
                self.build()
        self.assertEqual(ctx.exception.code, "INDEX_WRITE_FAILED")
        self.assertFallsBack("INDEX_CORRUPT")  # old FAISS + new database: refused, not mis-cited
        self.build()
        self.assertEqual(vector_index.load(self.out).meta["chunks"], "6")

    def test_build_writes_atomically_and_leaves_no_temp_files(self):
        self.build()
        leftovers = [p.name for p in vector_index.index_dir(self.out).iterdir() if p.name.endswith(".tmp")]
        self.assertEqual(leftovers, [])

    def test_wrong_query_dimension_falls_back(self):
        self.build()

        def other_model(texts):
            return [[1.0] * (DIM + 3) for _ in texts], {"prompt_tokens": 0, "completion_tokens": 0}
        res = search.search_policy("late parcel", out_dir=self.out, embedder=other_model)
        self.assertEqual(res["retrieval"], "keyword (fallback: INDEX_STALE)")

    def test_index_from_older_format_is_stale(self):
        self.build()
        con = sqlite3.connect(vector_index.index_dir(self.out) / vector_index.DB_NAME)
        con.execute("UPDATE meta SET value = 'a-vec-1' WHERE key = 'index_version'")
        con.commit()
        con.close()
        self.assertFallsBack("INDEX_STALE")

    def test_embedding_failure_falls_back_to_keyword(self):
        self.build()

        def broken(texts):
            raise vector_index.VectorUnavailable("EMBED_HTTP_429", "no credits")
        res = search.search_policy("late parcel", out_dir=self.out, embedder=broken)
        self.assertEqual((res["status"], res["retrieval"]), ("found", "keyword (fallback: EMBED_HTTP_429)"))
        strict = search.search_policy("late parcel", mode="vector", out_dir=self.out, embedder=broken)
        self.assertEqual((strict["ok"], strict["error"]["code"], strict["error"]["retryable"]),
                         (False, "EMBED_HTTP_429", True))


@unittest.skipUnless(vector_index.HAVE_FAISS, "faiss-cpu/numpy not installed")
class LocalEmbeddingTests(unittest.TestCase):
    """The free, offline backend (numpy TF-IDF over words + character n-grams)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        (self.out / "emails.jsonl").write_text("\n".join(json.dumps(e) for e in EMAILS) + "\n", encoding="utf-8")
        (self.out / "policy_chunks.jsonl").write_text("\n".join(json.dumps(r) for r in RULES) + "\n", encoding="utf-8")
        (self.out / "manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")
        vector_index._CACHE.clear()

    def tearDown(self):
        vector_index._CACHE.clear()
        self._tmp.cleanup()

    def test_local_build_needs_no_embedder_and_saves_its_model(self):
        summary = vector_index.build(self.out, model="local-tfidf-chargram-v1")
        self.assertEqual((summary["embed_model"], summary["chunks"], summary["prompt_tokens"]),
                         ("local-tfidf-chargram-v1", "5", 0))
        self.assertTrue((vector_index.index_dir(self.out) / "local_embed.npz").is_file())

    def test_search_uses_the_local_model_automatically_and_tolerates_typos(self):
        vector_index.build(self.out, model="local-tfidf-chargram-v1")
        res = search.search_policy("lat parcle apolgy", mode="vector", out_dir=self.out)
        self.assertEqual((res["status"], res["data"][0]["heading"]), ("found", "Late delivery"))
        thrown = search.search_policy("parcel smashd thrwn", mode="vector", out_dir=self.out)
        self.assertEqual(thrown["data"][0]["heading"], "Damaged / thrown parcel")
        self.assertEqual(res["retrieval"], "vector:local-tfidf-chargram-v1")

    def test_unrelated_question_is_not_found(self):
        vector_index.build(self.out, model="local-tfidf-chargram-v1")
        res = search.search_policy("weather in tokyo", mode="vector", out_dir=self.out)
        self.assertEqual(res["status"], "not_found")

    def test_vectors_are_deterministic_and_normalised(self):
        from backend.unstructured.local_embed import LocalEmbedder
        emb = LocalEmbedder.fit(["late parcel", "thrown parcel"])
        (a,), _ = emb(["late parcel"])
        (b,), _ = emb(["late parcel"])
        self.assertEqual(a, b)
        self.assertAlmostEqual(sum(x * x for x in a), 1.0, places=5)

    def test_missing_local_model_file_falls_back_to_keyword(self):
        vector_index.build(self.out, model="local-tfidf-chargram-v1")
        (vector_index.index_dir(self.out) / "local_embed.npz").unlink()
        res = search.search_policy("late parcel", out_dir=self.out)
        self.assertEqual(res["retrieval"], "keyword (fallback: INDEX_MISSING)")

    def test_damaged_local_model_file_falls_back_to_keyword(self):
        vector_index.build(self.out, model="local-tfidf-chargram-v1")
        path = vector_index.index_dir(self.out) / "local_embed.npz"
        path.write_bytes(path.read_bytes()[:100])
        vector_index._CACHE.clear()
        res = search.search_policy("late parcel", out_dir=self.out)
        self.assertEqual((res["status"], res["retrieval"]), ("found", "keyword (fallback: INDEX_CORRUPT)"))


class FallbackWithoutIndexTests(unittest.TestCase):
    """These run even without faiss installed."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        (self.out / "policy_chunks.jsonl").write_text("\n".join(json.dumps(r) for r in RULES) + "\n", encoding="utf-8")
        (self.out / "manifest.json").write_text(json.dumps({"files": []}), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_index_means_keyword_with_reason(self):
        res = search.search_policy("late parcel", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual(res["status"], "found")
        self.assertTrue(res["retrieval"].startswith("keyword (fallback: "))

    def test_no_faiss_installed_means_keyword(self):
        with mock.patch.object(vector_index, "HAVE_FAISS", False):
            res = search.search_policy("late parcel", out_dir=self.out, embedder=FakeEmbedder())
        self.assertEqual(res["retrieval"], "keyword (fallback: NO_FAISS)")

    def test_keyword_mode_never_calls_the_embedder(self):
        emb = FakeEmbedder()
        res = search.search_policy("late parcel", mode="keyword", out_dir=self.out, embedder=emb)
        self.assertEqual((res["retrieval"], emb.calls), ("keyword", []))

    def test_bad_mode_is_an_error(self):
        res = search.search_policy("late", mode="magic", out_dir=self.out)
        self.assertEqual((res["status"], res["error"]["code"]), ("failed", "BAD_MODE"))


if __name__ == "__main__":
    unittest.main()
