"""search_emails / search_policy and the eval runner, on synthetic outputs."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.unstructured import evals, search


def email(stem, order, subject, category, body, received="2026-03-02T10:00:00+08:00"):
    return {"source_id": f"email:{stem}", "ref": f"data/docs/complaint_emails/{stem}.txt", "status": "ok",
            "subject": subject, "category": category, "is_complaint": category != "compliment",
            "order_numbers": [order] if order else [], "received_at": received, "body": body}


class SearchTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.out = Path(self._tmp.name)
        rows = [email("a", "20001", "Wrong address delivered", "wrong_address", "Parcel went to the wrong block. Order 20001."),
                email("b", "20002", "COD amount wrong", "cod_wrong", "Driver collect $10 extra for COD, order 20002."),
                email("c", None, "Compliment for driver", "compliment", "Driver DRV001 very polite and helpful.")]
        (self.out / "emails.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        (self.out / "policy_chunks.jsonl").write_text("", encoding="utf-8")
        (self.out / "manifest.json").write_text(json.dumps({"files": [
            {"kind": "policy", "issues": [{"code": "SOURCE_MISSING"}]}]}), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_keyword_search_ranks_and_cites_exact_text(self):
        res = search.search_emails("COD extra", out_dir=self.out)
        self.assertEqual((res["ok"], res["status"], res["sources"][0]), (True, "found", "email:b"))
        hit = res["data"][0]
        a, b = map(int, hit["citation"]["locator"].split(":")[-1].split("-"))
        body = "Driver collect $10 extra for COD, order 20002."
        self.assertEqual(body[a:b], hit["text"])

    def test_order_filter_and_not_found(self):
        self.assertEqual(search.search_emails(order_number="20001", out_dir=self.out)["sources"], ["email:a"])
        none = search.search_emails(order_number="99999", out_dir=self.out)
        self.assertEqual((none["ok"], none["status"], none["data"]), (True, "not_found", []))

    def test_missing_index_is_a_failed_dependency(self):
        with tempfile.TemporaryDirectory() as empty:
            res = search.search_emails("x", out_dir=Path(empty))
        self.assertEqual((res["ok"], res["status"], res["error"]["code"]), (False, "failed", "INDEX_MISSING"))

    def test_policy_missing_guide_refuses_honestly(self):
        res = search.search_policy("refund for lost parcel", out_dir=self.out)
        self.assertEqual((res["ok"], res["status"], res["error"]["code"]), (False, "failed", "SOURCE_MISSING"))
        self.assertIn("Do not invent", res["error"]["message"])

    def test_policy_found_when_guide_exists(self):
        chunk = {"source_id": "policy:guide", "ref": "data/tabular/guide.md", "locator": "section:Refunds|line:2-3",
                 "heading": "Refunds", "text": "Refund in full if the parcel is lost."}
        (self.out / "policy_chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
        res = search.search_policy("lost parcel refund", out_dir=self.out)
        self.assertEqual((res["status"], res["data"][0]["citation"]["locator"]), ("found", "section:Refunds|line:2-3"))

    def test_telemetry_has_no_query_text(self):
        search.search_emails("secret words here", out_dir=self.out)
        self.assertNotIn("secret", (self.out / "telemetry.jsonl").read_text(encoding="utf-8"))


class EvalRunnerTests(unittest.TestCase):
    def test_pass_fail_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "emails.jsonl").write_text(json.dumps(email("x", "20001", "s", "late", "Order 20001.")) + "\n",
                                              encoding="utf-8")
            cases = {"cases": [
                {"id": "P", "needs": "emails.jsonl", "call": "email_record", "args": {"source_id": "email:x"},
                 "expect": [{"path": "order_numbers", "equals": ["20001"]}]},
                {"id": "F", "needs": "emails.jsonl", "call": "email_record", "args": {"source_id": "email:x"},
                 "expect": [{"path": "category", "equals": "compliment"}]},
                {"id": "W", "needs": "pod_records.jsonl", "call": "pod_record", "args": {"source_id": "pod:v1:1"},
                 "expect": [{"path": "status", "equals": "ok"}]}]}
            path = out / "cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            results = {r["id"]: r["verdict"] for r in evals.run_cases(path, out)}
            with contextlib.redirect_stdout(io.StringIO()):
                code = evals.main(["--cases", str(path), "--out", str(out)])
        self.assertEqual(results, {"P": "PASS", "F": "FAIL", "W": "PENDING"})
        self.assertEqual(code, 1)

    def test_shipped_cases_file_is_valid(self):
        cases = json.loads(Path("evals/developer_a_cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len(cases), 6)
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for c in cases:
            self.assertTrue({"id", "needs", "call", "expect"} <= set(c), c["id"])


if __name__ == "__main__":
    unittest.main()
