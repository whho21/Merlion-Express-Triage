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


class PrivacyGuardCasingTests(unittest.TestCase):
    """PR #14 review (John + Copilot): P1 casing and name-length variations, P2 greetings before complaint text."""

    def check(self, text, expected):
        self.assertEqual(privacy_guard(text)[0], expected)

    def test_p1_reviewer_repro_caps_name_and_lower_case_numbered_address(self):
        self.check("Customer: JANE TAN at 12 bedok north drive", "Customer: [NAME] at [ADDRESS]")

    def test_p1_names_in_any_casing(self):
        cases = {"customer: jane tan": "customer: [NAME]",
                 "tan mei ling complained": "[NAME] complained",
                 "TAN AH KOW complained": "[NAME] complained",
                 "ZHI WEI TAN complained": "[NAME] complained",
                 "Dear MR TAN, your parcel": "Dear [NAME], your parcel",
                 "Mr TAN AH KOW": "[NAME]",
                 "mr tan ah kow said the parcel was late": "[NAME] said the parcel was late",
                 "Regards, JOHN": "Regards, [NAME]",
                 "regards, jane tan": "regards, [NAME]",
                 "jane tan here, order 12345": "[NAME] here, order 12345",
                 "JANE TAN here, order 12345": "[NAME] here, order 12345",
                 "lim jane said": "[NAME] said",
                 "ahmad bin yusof": "[NAME]",
                 "Name: tan ah kow": "Name: [NAME]",
                 "my name is jane tan lee and my parcel is late": "my name is [NAME] and my parcel is late",
                 "Customer: Tan Ah Kow Jr": "Customer: [NAME]"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.check(text, expected)

    def test_p1_numbered_addresses_in_any_casing(self):
        cases = {"12 BEDOK NORTH DRIVE": "[ADDRESS]", "12 bedok north drive": "[ADDRESS]", "5 orchard way": "[ADDRESS]",
                 "JALAN BUKIT MERAH": "[ADDRESS]", "jln bukit merah": "[ADDRESS]", "ANG MO KIO CENTRAL": "[ADDRESS]",
                 "at 12 bedok north drive, call me": "at [ADDRESS], call me"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.check(text, expected)

    def test_p2_greeting_before_complaint_text_is_kept(self):  # John's repro: "Hi, Lat Parcle Apolgy" became [NAME]
        for text in ("Hi, Lat Parcle Apolgy", "Hi, Late Delivery Complaint", "Hi, Damaged Parcel",
                     "hello my parcel is late again", "Hi team, where is order 25574", "Hi there, wrong address",
                     "Hey, COD amount wrong", "Hi Lat parcel late", "Hi, Late delivery. Order 25574 came 3 days late."):
            with self.subTest(text=text):
                self.check(text, text)

    def test_p2_greeting_before_a_real_name_still_masks(self):
        cases = {"Hi Jane, my parcel is late": "Hi [NAME], my parcel is late",
                 "Hello Zhi Wei,\nmy parcel": "Hello [NAME],\nmy parcel",
                 "Hi Mr Tan": "Hi [NAME]", "hey Priya!": "hey [NAME]!", "Hi JANE": "Hi [NAME]",
                 "Hi Zhi Wei": "Hi [NAME]"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.check(text, expected)

    def test_copilot_apostrophe_surname_prefix(self):
        self.check("Ryan D'Cruz called", "[NAME] called")
        self.check("Mary D\u2019Souza called", "[NAME] called")

    def test_copilot_surname_first_before_a_given_name(self):
        self.check("Lim Jane Tan", "[NAME]")
        self.check("Customer Lim Jane Tan of 123 Orchard Road", "Customer [NAME] of [ADDRESS]")

    def test_everyday_words_near_name_or_street_rules_stay(self):
        for text in ("2 days late and no way to reach the driver", "took 3 attempts to find a place",
                     "3 parcels went the wrong way", "The Central zone had most complaints",
                     "parcel left at the side of the road", "I AM VERY UPSET", "COD AMOUNT WRONG", "SIM CARD MISSING",
                     "low quality packaging", "MY PARCEL IS LATE AGAIN", "This is unacceptable", "i am still waiting",
                     "thanks for your help", "Dear Sir/Madam", "dear valued customer", "10 KG PARCEL"):
            with self.subTest(text=text):
                self.check(text, text)

    def test_stress_findings_lower_case_town_streets_and_name_particles(self):
        """Found by running every real name and street through the guard in 3 casings (17 Nov evening)."""
        cases = {"bedok central": "[ADDRESS]", "bishan st 11": "[ADDRESS]", "bukit batok drive": "[ADDRESS]",
                 "parcel left at toa payoh st 21 yesterday": "parcel left at [ADDRESS] yesterday",
                 "Blk 584 bedok drive #04-621": "blk [BLOCK] [ADDRESS] [UNIT]",
                 "blk 916 tampines st 11 #15-29 singapore 462057": "blk [BLOCK] [ADDRESS] [UNIT] [POSTAL]",
                 "clara de silva said the parcel was late": "[NAME] said the parcel was late",
                 "Clara de Silva": "[NAME]", "Hi clara de silva,": "Hi [NAME],"}
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.check(text, expected)

    def test_stress_findings_title_case_every_word_complaints_stay(self):
        for text in ("Sim Card Missing From The Box", "Low Quality Packaging, Item Broke", "LOW QUALITY PACKAGING",
                     "What Is The Weight Limit For The 3 Kg Band", "WHAT IS THE WEIGHT LIMIT FOR THE 3 KG BAND",
                     "Parcel Delivered To The Wrong Block", "Driver Was Rude And Threw The Parcel",
                     "complaints in bedok", "Bedok zone had most late deliveries"):
            with self.subTest(text=text):
                self.check(text, text)

    def test_guard_is_idempotent_on_every_new_form(self):
        for text in ("Customer: JANE TAN at 12 bedok north drive", "tan mei ling complained", "Regards, JOHN",
                     "Lim Jane Tan", "Hi Jane,", "ahmad bin yusof", "ZHI WEI TAN"):
            once = privacy_guard(text)[0]
            self.assertEqual(privacy_guard(once)[0], once)


if __name__ == "__main__":
    unittest.main()
