"""Policy parser and end-to-end ingest tests on a synthetic data folder."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.unstructured import ingest, policy
from backend.unstructured.tests.fixtures import GUIDE_ROWS, make_xlsx


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, content):
        path = self.data / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def test_missing_guide_is_reported_not_invented(self):
        chunks, entries = policy.ingest_policy(self.data)
        self.assertEqual(chunks, [])
        self.assertEqual(entries[0]["status"], "failed")
        self.assertEqual(entries[0]["issues"][0]["code"], "SOURCE_MISSING")

    def test_markdown_split_by_heading_with_locators(self):
        self.write("tabular/Resolution_Guide.md", "# Refunds\nRefund if lost.\n\n# Re-delivery\nRe-deliver once.\n")
        chunks, entries = policy.ingest_policy(self.data)
        self.assertEqual(entries[0]["status"], "ok")
        self.assertEqual([c["heading"] for c in chunks], ["Refunds", "Re-delivery"])
        self.assertEqual(chunks[0]["locator"], "section:Refunds|line:2-3")
        self.assertEqual(chunks[0]["source_id"], "policy:Resolution_Guide")
        self.assertEqual(chunks[0]["ref"], "data/tabular/Resolution_Guide.md")

    def test_csv_one_chunk_per_row(self):
        self.write("tabular/resolution_guide.csv", "case_type,action\nlost,refund\ndamaged,compensate\n")
        chunks, _ = policy.ingest_policy(self.data)
        self.assertEqual([c["locator"] for c in chunks], ["row:1", "row:2"])
        self.assertEqual(chunks[1]["text"], "case_type: damaged; action: compensate")

    def test_unsupported_format_is_visible(self):
        self.write("tabular/Resolution_Guide.pdf", b"%PDF-1.4")
        chunks, entries = policy.ingest_policy(self.data)
        self.assertEqual(chunks, [])
        self.assertEqual(entries[0]["issues"][0]["code"], "UNSUPPORTED_FORMAT")

    def test_broken_xlsx_is_visible_not_a_crash(self):
        self.write("tabular/Resolution_Guide.xlsx", b"PK\x03\x04 not really a zip")
        chunks, entries = policy.ingest_policy(self.data)
        self.assertEqual((chunks, entries[0]["status"], entries[0]["issues"][0]["code"]), ([], "failed", "BAD_XLSX"))

    def test_case_log_is_not_mistaken_for_the_guide(self):
        self.write("tabular/cs_case_log.csv", "case_id,order\n1,20001\n")
        make_xlsx(self.data / "tabular" / "cs_case_log.xlsx", {"Case Log": [["Case No", "Order Ref"], ["1", "20001"]]})
        _, entries = policy.ingest_policy(self.data)
        self.assertEqual(entries[0]["issues"][0]["code"], "SOURCE_MISSING")

    def test_guide_tab_inside_the_case_log_workbook(self):
        # the client's real layout: one workbook, "Case Log" (B's) + "Resolution Guide" (A's)
        make_xlsx(self.data / "tabular" / "cs_case_log.xlsx",
                  {"Case Log": [["Case No", "Customer"], ["1", "Test Person"]], "Resolution Guide": GUIDE_ROWS})
        chunks, entries = policy.ingest_policy(self.data)
        e = entries[0]
        self.assertEqual((e["status"], e["source_id"], e["tabs_skipped"]),
                         ("ok", "policy:cs_case_log:resolution_guide", ["Case Log"]))
        self.assertEqual((e["guide"][0]["version"], e["guide"][0]["updated"]), ("v2", "2026-03-02"))
        self.assertEqual([c["heading"] for c in chunks],
                         ["Late delivery", "COD overcharge", "Corporate account (TEST-*)", "Notes"])
        late = chunks[0]
        self.assertEqual(late["locator"], "sheet:Resolution Guide|row:5")
        self.assertEqual(late["email_categories"], ["late"])
        self.assertEqual(late["fields"]["Resolution"], "Under 2 days: apology only")
        self.assertIn("Q02", late["authority"])
        self.assertEqual(chunks[2]["email_categories"], ["corporate"])
        self.assertEqual(chunks[3]["text"], "One complaint = one case.")
        self.assertNotIn("Test Person", json.dumps(chunks))  # the case-log tab is never read by A


class IngestTests(unittest.TestCase):
    def test_every_file_gets_an_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            data, out = Path(tmp) / "data", Path(tmp) / "out"
            emails_dir = data / "docs" / "complaint_emails"
            emails_dir.mkdir(parents=True)
            good = "From: a@example.com\nTo: s@example.com\nDate: Mon, 02 Mar 2026 13:14:00 +0800\n" \
                   "Subject: Item missing from parcel\n\nOrder 20001. Call 91234567.\n"
            (emails_dir / "2026-03-02_001.txt").write_text(good, encoding="utf-8")
            (emails_dir / "2026-03-02_002.txt").write_text("not an email", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = ingest.main(["--data", str(data), "--out", str(out)])
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            lines = (out / "emails.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(code, 1)  # one email failed, so the run says so
        self.assertEqual(len(lines), 2)
        self.assertEqual([f["status"] for f in manifest["files"]], ["ok", "failed", "failed"])
        self.assertEqual(manifest["files"][2]["issues"][0]["code"], "SOURCE_MISSING")
        self.assertEqual(manifest["summary"]["emails"]["pii_detected"], {"phone": 1})
        self.assertIn("91234567", lines[0])  # unmasked on purpose (B/C/D mask)
        self.assertEqual(json.loads(lines[0])["sender"], "a@example.com")
        self.assertNotIn("91234567", json.dumps(manifest))  # manifest and summary carry counts only

    def test_missing_email_folder_returns_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(ingest.main(["--data", tmp, "--out", tmp]), 1)


if __name__ == "__main__":
    unittest.main()
