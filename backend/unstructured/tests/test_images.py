"""POD + rate-card normalisation, SQL validation, lookups and the extraction run. Synthetic data, fake model."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.unstructured import extract_images, pod, ratecard
from backend.unstructured.sqlref import Reference

SQL = """-- synthetic
INSERT INTO `drivers` (`driver_id`, `driver_code`, `driver_name`, `mobile`, `vehicle_type`, `joined_date`) VALUES
(1, 'DRV001', 'Test Driver', '90000000', 'van', '2021-01-01');

INSERT INTO `orders` (`order_id`, `system_version`, `order_date`, `customer_name`, `customer_phone`, `delivery_address`, `postal_code`, `parcel_weight_kg`, `cod_amount`, `promised_date`, `status`) VALUES
(20001, 'v1', '2025-10-01', 'Test Person', '90000001', 'Blk 101 Test Street #01-01 Singapore 100001', '100001', 2.5, 0.00, '2025-10-03', 'DELIVERED'),
(20001, 'v2', '2026-02-02', 'Other Person', '90000002', 'Blk 202 Other Road #02-02 Singapore 200002', '200002', 3.0, 0.00, '2026-02-04', 'DELIVERED');

INSERT INTO `deliveries` (`delivery_id`, `order_id`, `system_version`, `driver_id`, `delivered_time`, `outcome`, `was_late`, `remarks`) VALUES
(1, 20001, 'v1', 1, '2025-10-02 16:16:13', 'DELIVERED', 0, '');
"""

GOOD_POD = {"order_ref": "V1-20001", "date_time": "02/10/2025 16:16", "driver": "DRV001",
            "delivered_to": "Blk 101 Test Street #01-01 Singapore 100001", "received_by": "Test Person",
            "remarks": "COD collected $10", "signature_present": True,
            "footer": "Hotline: 6000 0000 www.example.sg", "unreadable": [], "notes": None}

RATE_ANSWER = {
    "title": "TEST LOGISTICS", "effective_text": "STANDARD RATE CARD - EFFECTIVE 1 APRIL 2026 (supersedes all previous)",
    "columns": ["Zone", "<=3kg", "3-10kg", "10-25kg", "Same-day surcharge"],
    "rows": [{"label": "Central", "cells": ["$1.00", "$2.00", "$3.00", "+$4.00"]},
             {"label": "Island", "cells": ["$5.00", "$6.00", "$7.00", "not available"]},
             {"label": "Peak hours", "cells": ["+$0.50", "+$0.50", "+$1.00", "—"]}],
    "notes": ["COD handling: 1.5% of collected amount, min $2.00", "Failed delivery re-attempt: $3.00 from 3rd attempt onwards",
              "Public holidays: no standard delivery.", "* All rates before GST (9%). Corporate accounts: volume rebate 5% above 2,000 parcels/mth."],
    "unreadable": []}


def reference():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.sql"
        path.write_text(SQL, encoding="utf-8")
        return Reference.from_sql(path)


def pod_record(answer, ref=None, system="v1", order_id=20001):
    return pod.build_record(answer, source_id=f"pod:{system}:{order_id}", image_ref="data/x.jpg", image_sha256="0",
                            file_system=system, file_order_id=order_id, ref=ref, extraction={"status": "ok"})


class PodTests(unittest.TestCase):
    def test_reference_keys_by_version_and_order(self):
        ref = reference()
        self.assertEqual(ref.orders[("v1", 20001)]["block"], "101")
        self.assertEqual(ref.orders[("v2", 20001)]["postal_code"], "200002")
        self.assertEqual(ref.deliveries[("v1", 20001)][0]["driver_code"], "DRV001")

    def test_clean_card_matches_sql_and_flags_cod_conflict(self):
        r = pod_record(GOOD_POD, reference())
        self.assertEqual(r["fields"]["delivered_at"]["value"], "2025-10-02T16:16")  # day-first
        self.assertEqual(r["validation"]["matches_sql"],
                         {"order": True, "delivered_at": True, "driver": True, "postal_code": True, "block": True})
        self.assertIn("cod_conflict_with_sql", r["flags"])  # card $10 vs SQL 0.00 (T-A08)
        self.assertEqual((r["status"], r["template"]), ("ok", "hotline_footer"))

    def test_lookalike_digit_is_repaired_and_flagged_not_silently_trusted(self):
        r = pod_record({**GOOD_POD, "date_time": "O2/1O/2025 I6:16"}, reference())
        self.assertEqual(r["fields"]["delivered_at"]["value"], "2025-10-02T16:16")
        self.assertEqual(r["fields"]["delivered_at"]["confidence"], "medium")
        self.assertIn("lookalike_repaired:delivered_at", r["flags"])

    def test_unreadable_date_is_null_never_guessed(self):
        r = pod_record({**GOOD_POD, "date_time": None, "unreadable": ["date_time"]}, reference())
        self.assertIsNone(r["fields"]["delivered_at"]["value"])
        self.assertEqual(r["status"], "partial")
        self.assertIn("low_confidence:delivered_at", r["flags"])
        self.assertIn("model_unreadable:date_time", r["flags"])

    def test_completely_unreadable_card_is_failed_but_emitted(self):
        blank = {k: None for k in GOOD_POD}
        blank["unreadable"] = list(GOOD_POD)
        self.assertEqual(pod_record(blank, reference())["status"], "failed")
        self.assertEqual(pod_record(None, reference())["status"], "failed")  # model call failed

    def test_sql_mismatch_is_partial(self):
        r = pod_record({**GOOD_POD, "driver": "DRV009"}, reference())
        self.assertEqual(r["status"], "partial")
        self.assertIn("sql_mismatch:driver", r["flags"])

    def test_receiver_roles_and_contradictions(self):
        self.assertEqual(pod.receiver_kind("mum"), ("role", "mum"))
        self.assertEqual(pod.receiver_kind("Front desk"), ("role", "front desk"))
        self.assertEqual(pod.receiver_kind(""), ("blank", None))
        self.assertEqual(pod.receiver_kind("Test Person")[0], "name")
        r = pod_record({**GOOD_POD, "remarks": "left outside door as instructed"})
        self.assertIn("remark_contradicts_signature", r["flags"])
        r = pod_record({**GOOD_POD, "remarks": "neighbour take", "received_by": "mum"})
        self.assertIn("remark_contradicts_receiver", r["flags"])
        r = pod_record({**GOOD_POD, "remarks": "neighbour take", "received_by": "Test Person"})
        self.assertNotIn("remark_contradicts_receiver", r["flags"])  # the name may be the neighbour's

    def test_absent_signature_is_not_trusted(self):
        r = pod_record({**GOOD_POD, "signature_present": False}, reference())
        self.assertEqual((r["fields"]["signature"]["value"], r["fields"]["signature"]["confidence"]), ("absent", "medium"))
        self.assertIn("signature_absent_verify_by_eye", r["flags"])
        self.assertEqual(r["status"], "ok")  # key fields still fine; the flag carries the doubt

    def test_find_pod_never_reuses_v1_card_for_v2(self):
        records = [pod_record(GOOD_POD, reference())]
        self.assertEqual(pod.find_pod(records, "v1", 20001)["status"], "found")
        v2 = pod.find_pod(records, "v2", 20001)
        self.assertEqual(v2["status"], "not_found")
        self.assertIn("No POD on file", v2["reason"])  # client Q04 wording: say it, never imply a check
        self.assertIn("Q04", v2["reason"])


class RateCardTests(unittest.TestCase):
    def card(self):
        return ratecard.normalise(RATE_ANSWER, source_id="ratecard:x", image_ref="data/r.jpg", image_sha256="0",
                                  extraction={})

    def test_structure(self):
        c = self.card()
        self.assertEqual((c["effective_from"], c["supersedes_previous"], c["status"]), ("2026-04-01", True, "ok"))
        self.assertEqual(len(c["rows"]), 6)  # 2 zones x 3 bands; the "+$" row is a surcharge
        self.assertEqual(c["rows"][0], {"zone": "Central", "band": "<=3kg", "min_kg": 0.0, "max_kg": 3.0,
                                        "boundary_rule": ratecard.BOUNDARY_RULE, "price": 1.0,
                                        "locator": "row:Central/col:<=3kg"})
        same_day = {s["zone"]: s for s in c["surcharges"] if s["name"] == "same_day"}
        self.assertEqual((same_day["Central"]["amount"], same_day["Island"]["available"]), (4.0, False))
        self.assertEqual(sum(1 for s in c["surcharges"] if s["name"] == "Peak hours"), 3)
        n = c["notes"]
        self.assertEqual((n["cod_handling"], n["reattempt_fee"], n["gst_included"], n["gst_pct"]),
                         ({"pct": 1.5, "min": 2.0}, {"amount": 3.0, "from_attempt": 3}, False, 9.0))
        self.assertEqual(n["corporate_rebate"], {"pct": 5.0, "above_parcels_per_month": 2000})

    def test_lookup_found_with_citation(self):
        hit = ratecard.lookup_rate([self.card()], zone="central", weight_kg=5, on_date="2026-05-01")
        d = hit["data"]
        self.assertEqual((hit["status"], d["price"], d["citation"]["locator"], d["applied_retrospectively"]),
                         ("found", 2.0, "row:Central/col:3-10kg", False))
        self.assertIn("standard", d["notes"][0])  # client Q08

    def test_exact_band_edges_go_to_the_lower_band(self):  # client Q07: upper limit inclusive
        cards = [self.card()]
        band = lambda w: ratecard.lookup_rate(cards, zone="Central", weight_kg=w, on_date="2026-05-01")  # noqa: E731
        self.assertEqual([band(w)["data"]["band"] for w in (3.0, 3.01, 10.0, 10.01, 25.0)],
                         ["<=3kg", "3-10kg", "3-10kg", "10-25kg", "10-25kg"])
        self.assertEqual(band(25.5)["status"], "not_found")
        self.assertIn("Q07", band(25.5)["reason"])
        self.assertEqual(band(0)["status"], "not_found")

    def test_april_card_applies_retrospectively_with_authority(self):  # client Q06
        early = ratecard.lookup_rate([self.card()], zone="Central", weight_kg=5, on_date="2025-10-15")
        self.assertEqual((early["status"], early["data"]["applied_retrospectively"]), ("found", True))
        self.assertIn("retrospectively, per client (Q06", early["data"]["notes"][1])

    def test_other_cards_are_not_back_dated_automatically(self):
        later = {**self.card(), "effective_from": "2027-01-01", "source_id": "ratecard:2027-01-01"}
        res = ratecard.lookup_rate([later], zone="Central", weight_kg=5, on_date="2026-06-01")
        self.assertEqual(res["status"], "not_found")
        self.assertIn("no client authority", res["reason"])

    def test_ops_zone_maps_to_price_row(self):  # client Q03
        answer = {**RATE_ANSWER, "rows": [{"label": "East / North-East", "cells": ["$1.10", "$2.20", "$3.30", "+$1.00"]},
                                          {"label": "North / West", "cells": ["$1.20", "$2.40", "$3.60", "+$1.00"]}]}
        cards = [ratecard.normalise(answer, source_id="r", image_ref="r", image_sha256="0", extraction={})]
        look = lambda z: ratecard.lookup_rate(cards, zone=z, weight_kg=2, on_date="2026-05-01")  # noqa: E731
        self.assertEqual([look(z)["data"]["price_zone"] for z in ("North-East", "East", "north", "West")],
                         ["East / North-East", "East / North-East", "North / West", "North / West"])
        self.assertEqual(look("Mars")["status"], "not_found")

    def test_surcharge_row_without_plus_sign_is_still_a_surcharge(self):
        # seen on the real card: the model copied "+$1.50" as "$1.50" for the ERP row
        answer = {**RATE_ANSWER, "rows": RATE_ANSWER["rows"][:2] +
                  [{"label": "CBD ERP hours (0730-1900)", "cells": ["$1.50", "$1.50", "$2.50", "—"]}]}
        c = ratecard.normalise(answer, source_id="s", image_ref="r", image_sha256="0", extraction={})
        self.assertEqual({r["zone"] for r in c["rows"]}, {"Central", "Island"})
        self.assertEqual(sum(1 for s in c["surcharges"] if s["name"].startswith("CBD ERP")), 3)
        self.assertEqual([i["code"] for i in c["issues"]], ["SURCHARGE_SIGN_MISSING"])
        self.assertEqual(c["status"], "partial")

    def test_missing_price_and_date_are_visible(self):
        broken = {**RATE_ANSWER, "effective_text": "STANDARD RATE CARD",
                  "rows": [{"label": "Central", "cells": ["$1.00", None, "$3.00", "+$4.00"]}]}
        c = ratecard.normalise(broken, source_id="s", image_ref="r", image_sha256="0", extraction={})
        self.assertEqual(c["status"], "partial")
        self.assertEqual({i["code"] for i in c["issues"]}, {"PRICE_UNREADABLE", "NO_EFFECTIVE_DATE"})


class ExtractionRunTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.data, self.out = root / "data", root / "out"
        (self.data / "images" / "proof_of_delivery").mkdir(parents=True)
        (self.data / "images" / "rate_cards").mkdir(parents=True)
        (self.data / "images" / "proof_of_delivery" / "POD_v1_20001.jpg").write_bytes(b"\xff\xd8 card one")
        (self.data / "images" / "proof_of_delivery" / "POD_v1_20002.jpg").write_bytes(b"\xff\xd8 card two")
        (self.data / "images" / "rate_cards" / "rate_card_test.jpg").write_bytes(b"\xff\xd8 rate card")
        self.calls = []

    def tearDown(self):
        self._tmp.cleanup()

    def fake_call(self, image, mime, prompt, **kw):
        self.calls.append(kw["source_id"])
        if kw["source_id"] == "pod:v1:20002":
            from backend.unstructured.llm import LLMError
            raise LLMError("HTTP_503", "down", retryable=True)
        answer = RATE_ANSWER if kw["tool"] == "ratecard_extract" else GOOD_POD
        return answer, {"prompt_tokens": 10, "completion_tokens": 5}

    def run_once(self):
        cfg = {"api_key": "k", "base_url": "u", "model": "gpt-4o-mini"}
        return extract_images.run(self.data, self.out, cfg=cfg, call=self.fake_call, reference=reference())

    def test_outcomes_cache_and_failed_retry(self):
        first = self.run_once()
        self.assertEqual([f["status"] for f in first["files"]], ["ok", "failed", "ok"])
        self.assertEqual(first["files"][1]["error"]["code"], "HTTP_503")
        self.assertEqual(first["files"][2]["source_id"], "ratecard:2026-04-01")
        self.assertEqual(first["summary"]["calls"]["paid_call"], 2)
        self.calls.clear()
        second = self.run_once()
        self.assertEqual(self.calls, ["pod:v1:20002"])  # only the failed card is retried; others from cache
        self.assertEqual(second["summary"]["calls"]["cache_hit"], 2)
        pods = [json.loads(l) for l in (self.out / "pod_records.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(pods), 2)
        # spend: run 1 = 2 paid calls x (10 in + 5 out) tokens at gpt-4o-mini prices; run 2 = cache only
        self.assertEqual(first["summary"]["spend"]["this_run_usd"], (20 * 0.15 + 10 * 0.60) / 1_000_000)
        self.assertEqual(second["summary"]["spend"]["this_run_usd"], 0.0)
        self.assertEqual(second["summary"]["spend"]["a_total_usd"], first["summary"]["spend"]["a_total_usd"])
        self.assertEqual(len((self.out / "spend_log.jsonl").read_text(encoding="utf-8").splitlines()), 2)

    def test_dry_run_sends_nothing(self):
        cfg = {"api_key": None, "base_url": "u", "model": "m"}
        plan = extract_images.dry_run(self.data, self.out, None, None, cfg)
        self.assertEqual((plan["pod_to_send"], plan["ratecard_to_send"], plan["team_key_found"]), (2, 1, False))
        self.assertEqual(self.calls, [])

    def test_no_key_stops_before_any_call(self):
        import os
        saved = os.environ.pop("OPENAI_API_KEY", None)
        cwd = os.getcwd()
        try:
            os.chdir(self._tmp.name)  # no .env here
            with contextlib.redirect_stderr(io.StringIO()):
                code = extract_images.main(["--data", str(self.data), "--out", str(self.out)])
        finally:
            os.chdir(cwd)
            if saved is not None:
                os.environ["OPENAI_API_KEY"] = saved
        self.assertEqual(code, 2)
        self.assertFalse((self.out / "pod_records.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
