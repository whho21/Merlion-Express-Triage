"""Masking tests. All values are synthetic."""
import unittest

from backend.unstructured.masking import mask_text, privacy_guard


class MaskTextTests(unittest.TestCase):
    def test_masks_each_pii_kind(self):
        text = ("Mail me at tester.one@example.com or call 9123 4567 / +65 61234567. "
                "NRIC S1234567D. Unit #05-123, Singapore 123456, blk 101A.")
        masked, counts = mask_text(text)
        for leaked in ("tester.one@example.com", "9123 4567", "61234567", "S1234567D", "#05-123", "123456",
                       "101A"):
            self.assertNotIn(leaked, masked)
        self.assertEqual(counts, {"email": 1, "nric": 1, "phone": 2, "unit": 1, "postal": 1, "block": 1})

    def test_keeps_order_numbers_driver_codes_and_amounts(self):
        text = "Order 20095 by DRV007, account MERL-C-0001, collected $123456 extra."
        masked, counts = mask_text(text)
        self.assertEqual(masked, text)
        self.assertEqual(counts, {})

    def test_eight_digit_number_not_starting_3689_is_not_a_phone(self):
        masked, counts = mask_text("ref 12345678")
        self.assertNotIn("phone", counts)


class PrivacyGuardTests(unittest.TestCase):
    """PR #13 review P1: names and street addresses must not reach an AI endpoint."""

    def assertHidden(self, text, *leaks):
        guarded = privacy_guard(text)[0]
        for leak in leaks:
            self.assertNotIn(leak, guarded, f"{leak!r} leaked in {guarded!r}")
        return guarded

    def test_reviewer_repro_name_and_street(self):
        guarded = self.assertHidden("Customer Jane Tan of 123 Orchard Road says parcel smashed",
                                    "Jane", "Tan", "Orchard", "123")
        self.assertEqual(guarded, "Customer [NAME] of [ADDRESS] says parcel smashed")

    def test_singapore_name_forms(self):
        cases = {"Mdm Siti Zulaikha binte Omar complained": ("Siti", "Zulaikha", "Omar"),
                 "Ahmad Danial bin Yusof": ("Ahmad", "Danial", "Yusof"),
                 "Ravi s/o Kumar": ("Ravi", "Kumar"),
                 "Ng Chee Keong said order 25574 late": ("Chee", "Keong"),
                 "Regards,\nPriya Sharma": ("Priya", "Sharma"),
                 "Dear Mr Lim, my parcel": ("Lim",),
                 "mr tan said the parcel was late": ("tan",),
                 "my name is jane tan and my parcel is late": ("jane", "tan"),
                 "From: Daniel Souza <d.souza@example.com>": ("Daniel", "Souza", "d.souza"),
                 "Xavier Lim called": ("Xavier", "Lim"),
                 "Ryan D says": ("Ryan",),
                 "Customer: Tan Mei Ling": ("Mei", "Ling")}
        for text, leaks in cases.items():
            with self.subTest(text=text):
                self.assertHidden(text, *leaks)

    def test_singapore_address_forms(self):
        cases = {"Blk 584 Pasir Ris Crescent #04-621 Singapore 424042": ("584", "Pasir", "Ris", "04-621", "424042"),
                 "Blk 916 Tampines St 11": ("Tampines", "11"),
                 "Blk 454 Ang Mo Kio Ring Road": ("Ang", "Kio"),
                 "Choa Chu Kang Ring Road": ("Choa", "Kang"),
                 "Bedok North Dr 1": ("Bedok",),
                 "I stay at Jalan Bukit Merah": ("Bukit", "Merah"),
                 "lorong 4 toa payoh and the parcel": ("toa", "payoh"),
                 "12 jurong west street 41": ("jurong",)}
        for text, leaks in cases.items():
            with self.subTest(text=text):
                self.assertHidden(text, *leaks)

    def test_complaint_wording_is_untouched(self):
        for text in ("Parcel thrown over gate, item smashed. 3 days late. Order 25574, driver DRV107.",
                     "delivered to the wrong block", "parcel left at the side of the road",
                     "The Central zone had most complaints", "COD amount wrong, driver collected $10 extra",
                     "Hi team, my parcel is late", "Dear Sir/Madam, the parcel never came", "April 2026 rate card",
                     "Box sealed at POD: reject, refer to merchant.", "by the way, very close",
                     "This is the 3rd late delivery this month (corporate account MERL-C-0042)."):
            with self.subTest(text=text):
                self.assertEqual(privacy_guard(text)[0], mask_text(text)[0])

    def test_idempotent_and_counts(self):
        text = "Regards, Jane Tan, 123 Orchard Road, call 91234567"
        once, counts = privacy_guard(text)
        self.assertEqual(privacy_guard(once)[0], once)
        self.assertEqual(counts, {"phone": 1, "address": 1, "name": 1})


if __name__ == "__main__":
    unittest.main()
