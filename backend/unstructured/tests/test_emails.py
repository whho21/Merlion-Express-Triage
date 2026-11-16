"""Email parser tests. Every email here is synthetic: invented addresses, numbers and blocks."""
import tempfile
import unittest
from pathlib import Path

from backend.unstructured.emails import parse_email_file, parse_email_text


def make_email(subject, body, sender="someone.test@example.com", date="Mon, 02 Mar 2026 13:14:00 +0800"):
    return f"From: {sender}\nTo: support@example.com\nDate: {date}\nSubject: {subject}\n\n{body}\n"


def parse(subject, body, **kw):
    return parse_email_text(make_email(subject, body, **kw), "email:test", "data/docs/complaint_emails/test.txt")


def located(record, text, locator):
    """Return the text a body:char:<a>-<b> locator points at, checking the file and record["body"] agree."""
    start, end = map(int, locator.split(":")[-1].split("-"))
    in_file = text[record["locators"]["body_offset_in_file"]:][start:end]
    assert in_file == record["body"][start:end]
    return in_file


class CategoryAndFieldTests(unittest.TestCase):
    def test_wrong_address_claims_blocks_and_order(self):
        body = "You delivered my parcel to the wrong block!! I stay blk 111 but the POD photo shows blk 222. Order 20001."
        r = parse("Wrong address delivered", body)
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["category"], "wrong_address")
        self.assertTrue(r["is_complaint"])
        self.assertEqual(r["order_numbers"], ["20001"])
        self.assertEqual((r["claims"]["stay_block"], r["claims"]["pod_block"]), ("111", "222"))
        self.assertIn("blk 111", r["body"])  # unmasked on purpose: B/C/D mask (John, 16 Nov)
        self.assertEqual(r["pii_detected"], {"block": 2})

    def test_order_locator_points_at_the_number(self):
        body = "I ordered 4 days ago and tracking still say IN_TRANSIT. Order number 20002. Call me at 91234567."
        text = make_email("Where is my parcel?!", body)
        r = parse_email_text(text, "email:test", "ref")
        self.assertEqual(r["category"], "where_is_parcel")
        self.assertEqual(located(r, text, r["locators"]["order_numbers"][0]), "20002")
        self.assertEqual(r["claims"]["days_ago"], 4)
        self.assertEqual(r["claims"]["status_claimed"], "IN_TRANSIT")
        self.assertEqual(r["pii_detected"], {"phone": 1})
        self.assertIn("91234567", r["body"])

    def test_cod_amount(self):
        r = parse("COD amount wrong", "Driver collect $10 extra for COD, order 20003. Please refund.")
        self.assertEqual((r["category"], r["claims"]["amount_extra"], r["order_numbers"]), ("cod_wrong", 10.0, ["20003"]))

    def test_corporate_and_others(self):
        r = parse("Late again — third time",
                  "3rd late delivery (corporate account MERL-C-0001). Orders 20004 and others.")
        self.assertEqual(r["category"], "late")
        self.assertEqual(r["corporate_account"], "MERL-C-0001")
        self.assertTrue(r["more_orders_unspecified"])

    def test_compliment_without_order_is_ok_and_not_a_complaint(self):
        r = parse("Compliment for driver", "Your driver DRV001 very polite and helpful. Well done!")
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["category"], "compliment")
        self.assertFalse(r["is_complaint"])
        self.assertEqual(r["driver_codes"], ["DRV001"])
        self.assertEqual(r["order_numbers"], [])

    def test_missing_item_and_thrown_over_gate(self):
        self.assertEqual(parse("Item missing from parcel", "Box opened. Order 20005.")["category"], "missing_item")
        self.assertEqual(parse("Parcel thrown over gate", "Driver THREW it over the gate. Order 20006.")["category"],
                         "thrown_over_gate")

    def test_unknown_subject_falls_back_to_body_then_unclassified(self):
        self.assertEqual(parse("Hello", "My parcel is late. Order 20007.")["category"], "late")
        r = parse("Hello", "Just checking in. Order 20008.")
        self.assertEqual((r["category"], r["status"]), ("unclassified", "partial"))
        self.assertIsNone(r["is_complaint"])


class OrderNumberTests(unittest.TestCase):
    def test_system_prefix_kept_as_hint_only(self):
        r = parse("Item missing from parcel", "Order V2-20009 arrived open.")
        self.assertEqual((r["order_numbers"], r["system_hint"]), (["20009"], "v2"))

    def test_block_phone_postal_and_amount_are_not_orders(self):
        body = "Order 20010. I stay blk 12345. Call 91234567, postal 123456, paid $20011."
        self.assertEqual(parse("Wrong address delivered", body)["order_numbers"], ["20010"])

    def test_complaint_without_order_is_partial(self):
        r = parse("Item missing from parcel", "Box arrived opened, one item missing.")
        self.assertEqual(r["status"], "partial")
        self.assertIn("NO_ORDER_NUMBER", [i["code"] for i in r["issues"]])

    def test_two_orders_flagged(self):
        r = parse("Item missing from parcel", "Orders 20012 and 20013 both missing items.")
        self.assertEqual(r["order_numbers"], ["20012", "20013"])
        self.assertIn("MULTIPLE_ORDER_NUMBERS", [i["code"] for i in r["issues"]])


class RobustnessTests(unittest.TestCase):
    def test_headers_kept_as_written(self):
        r = parse("Item missing from parcel", "Order 20014.", sender="Same.Person@Example.com")
        self.assertEqual((r["sender"], r["to"], r["subject"]),
                         ("Same.Person@Example.com", "support@example.com", "Item missing from parcel"))
        self.assertEqual(r["locators"]["sender"], "header:From")

    def test_date_parsed_with_timezone(self):
        self.assertEqual(parse("Item missing from parcel", "Order 20016.")["received_at"], "2026-03-02T13:14:00+08:00")

    def test_bad_date_is_partial(self):
        r = parse("Item missing from parcel", "Order 20017.", date="sometime last week")
        self.assertEqual(r["status"], "partial")
        self.assertIn("BAD_DATE", [i["code"] for i in r["issues"]])

    def test_missing_header_is_failed_but_keeps_the_text(self):
        r = parse_email_text("From: a@example.com\nSubject: x\n\nOrder 20018.\n", "email:test", "ref")
        self.assertEqual(r["status"], "failed")
        self.assertIn("MISSING_HEADER", [i["code"] for i in r["issues"]])
        self.assertEqual((r["sender"], r["body"]), ("a@example.com", "Order 20018.\n"))

    def test_crlf_and_bom(self):
        text = "﻿" + make_email("Item missing from parcel", "Order 20019.").replace("\n", "\r\n")
        r = parse_email_text(text, "email:test", "ref")
        self.assertEqual((r["status"], r["order_numbers"]), ("ok", ["20019"]))

    def test_non_utf8_file_is_failed_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            path = data / "docs" / "complaint_emails" / "2026-01-01_000.txt"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"From: a@example.com\n\n\xff\xfe broken")
            record, entry = parse_email_file(path, data)
        self.assertEqual((record["status"], entry["status"]), ("failed", "failed"))
        self.assertEqual(entry["ref"], "data/docs/complaint_emails/2026-01-01_000.txt")
        self.assertEqual(record["source_id"], "email:2026-01-01_000")

    def test_nothing_is_masked_in_the_record(self):
        body = "I stay blk 111 but the POD photo shows blk 222. Order 20020. Call 91234567 or a.b@example.com."
        r = parse("Wrong address delivered", body)
        for placeholder in ("[PHONE]", "[EMAIL]", "[BLOCK]", "[MASKED]"):
            self.assertNotIn(placeholder, str(r))
        self.assertEqual(r["pii_detected"], {"email": 1, "phone": 1, "block": 2})


if __name__ == "__main__":
    unittest.main()
