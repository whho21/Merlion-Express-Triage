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

    def test_embedding_failure_falls_back_to_keyword(self):
        self.build()

        def broken(texts):
            raise vector_index.VectorUnavailable("EMBED_HTTP_429", "no credits")
        res = search.search_policy("late parcel", out_dir=self.out, embedder=broken)
        self.assertEqual((res["status"], res["retrieval"]), ("found", "keyword (fallback: EMBED_HTTP_429)"))
        strict = search.search_policy("late parcel", mode="vector", out_dir=self.out, embedder=broken)
        self.assertEqual((strict["ok"], strict["error"]["code"], strict["error"]["retryable"]),
                         (False, "EMBED_HTTP_429", True))


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
