"""Masking tests. All values are synthetic."""
import unittest

from backend.unstructured.masking import mask_text


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


if __name__ == "__main__":
    unittest.main()
