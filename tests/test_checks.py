import unittest

from helpers import AS_OF, CFG, checks, hist, run, vendor
from vlt import validate


class TestBaseline(unittest.TestCase):
    def test_clean_vendor_raises_nothing(self):
        self.assertEqual(checks(), set())


class TestTransitions(unittest.TestCase):
    def test_skipping_a_gate(self):
        h = hist(("intake", "2025-01-02", None), ("active", "2025-02-01", None))
        self.assertIn("SKIPPED_GATE", checks(history=h))

    def test_going_backwards_is_invalid_not_skipped(self):
        h = hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"),
                 ("active", "2024-03-01", None), ("offboarding", "2025-01-01", None), ("offboarded", "2025-02-01", None), ("active", "2026-01-01", None))
        got = checks(history=h)
        self.assertIn("INVALID_TRANSITION", got)
        self.assertNotIn("SKIPPED_GATE", got)

    def test_reassessment_loop_is_allowed(self):
        h = vendor()["history"] + hist(("reassessment", "2026-01-01", None), ("active", "2026-02-01", None))
        self.assertEqual(checks(history=h), set())


class TestApproval(unittest.TestCase):
    def test_missing_approver_severity_follows_tier(self):
        h = hist(("intake", "2025-01-02", None), ("due_diligence", "2025-01-10", None), ("approved", "2025-02-20", None), ("active", "2025-03-01", None))
        sev = {t: [i["severity"] for i in run(history=h, tier=t)["issues"] if i["check"] == "GO_LIVE_WITHOUT_APPROVAL"] for t in (1, 2, 3, 4)}
        self.assertEqual(sev, {1: ["critical"], 2: ["high"], 3: ["medium"], 4: ["low"]})

    def test_incomplete_due_diligence_lists_what_is_missing(self):
        i = [x for x in run(checklist={"tier_assigned": True})["issues"] if x["check"] == "DUE_DILIGENCE_INCOMPLETE"]
        self.assertEqual(len(i), 1)
        self.assertIn("questionnaire_received", i[0]["detail"])
        self.assertIn("evidence_reviewed", i[0]["detail"])
        self.assertNotIn("tier_assigned", i[0]["detail"])

    def test_dpa_needed_only_for_regulated_data(self):
        self.assertIn("DUE_DILIGENCE_INCOMPLETE", checks(data_types=["personal"], dpa_signed=False))
        self.assertNotIn("DUE_DILIGENCE_INCOMPLETE", checks(data_types=["internal"], dpa_signed=False))
        self.assertNotIn("DUE_DILIGENCE_INCOMPLETE", checks(data_types=["personal"], dpa_signed=True))

    def test_live_vendor_without_tier(self):
        self.assertIn("TIER_MISSING", checks(tier=None))


class TestStalls(unittest.TestCase):
    def dd(self, start):
        return dict(stage="due_diligence", history=hist(("intake", "2026-06-01", None), ("due_diligence", start, None)))

    def test_boundary(self):
        self.assertIn("STALLED_STAGE", checks(**self.dd("2026-09-07")))        # 46 days, limit 45
        self.assertNotIn("STALLED_STAGE", checks(**self.dd("2026-09-08")))      # 45 days


class TestReassessment(unittest.TestCase):
    def test_cadence_depends_on_tier(self):
        self.assertIn("REASSESSMENT_OVERDUE", checks(tier=1, last_assessment="2025-10-22"))
        self.assertNotIn("REASSESSMENT_OVERDUE", checks(tier=1, last_assessment="2025-10-23"))
        self.assertNotIn("REASSESSMENT_OVERDUE", checks(tier=3, last_assessment="2025-10-22"))   # 24 months
        self.assertIn("REASSESSMENT_OVERDUE", checks(tier=3, last_assessment="2024-10-22"))

    def test_never_assessed(self):
        self.assertIn("REASSESSMENT_OVERDUE", checks(last_assessment=None))

    def test_only_for_live_vendors(self):
        h = hist(("intake", "2026-10-01", None))
        self.assertNotIn("REASSESSMENT_OVERDUE", checks(stage="intake", history=h, last_assessment=None))


class TestOffboarding(unittest.TestCase):
    OFF = hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"),
               ("active", "2024-03-01", None), ("offboarding", "2026-08-01", None), ("offboarded", "2026-09-01", None))
    DONE = {"access_revoked": True, "data_disposal_confirmed": True, "contract_closed": True, "register_updated": True}

    def test_clean_offboarding(self):
        self.assertEqual(checks(stage="offboarded", history=self.OFF, active_access=False, offboarding=self.DONE), set())

    def test_incomplete_checklist_severity(self):
        i = run(stage="offboarded", history=self.OFF, active_access=False, offboarding=dict(self.DONE, data_disposal_confirmed=False))["issues"]
        self.assertEqual([(x["check"], x["severity"]) for x in i], [("OFFBOARD_INCOMPLETE", "high")])
        i = run(stage="offboarded", history=self.OFF, active_access=False, offboarding=dict(self.DONE, access_revoked=False))["issues"]
        self.assertEqual([(x["check"], x["severity"]) for x in i], [("OFFBOARD_INCOMPLETE", "critical")])

    def test_access_after_offboarded_is_critical(self):
        i = [x for x in run(stage="offboarded", history=self.OFF, active_access=True, offboarding=self.DONE)["issues"]]
        self.assertEqual([(x["check"], x["severity"]) for x in i], [("OFFBOARD_ACCESS_LINGERING", "critical")])

    def test_lingering_access_during_offboarding_boundary(self):
        h = lambda d: hist(("intake", "2024-01-02", None), ("due_diligence", "2024-01-10", None), ("approved", "2024-02-20", "CISO"),
                           ("active", "2024-03-01", None), ("offboarding", d, None))
        self.assertIn("OFFBOARD_ACCESS_LINGERING", checks(stage="offboarding", history=h("2026-09-22"), active_access=True))     # 31 days
        self.assertNotIn("OFFBOARD_ACCESS_LINGERING", checks(stage="offboarding", history=h("2026-09-23"), active_access=True))  # 30 days
        self.assertNotIn("OFFBOARD_ACCESS_LINGERING", checks(stage="offboarding", history=h("2026-08-01"), active_access=False))


class TestValidation(unittest.TestCase):
    def test_rejects_bad_input(self):
        bad = [dict(stage="nonsense"), dict(tier=7), dict(data_types=["secrets"]),
               dict(history=hist(("intake", "2025-01-02", None))),                               # does not end at current stage
               dict(history=hist(("intake", "2025-03-02", None), ("active", "2025-01-02", None))),   # dates go backwards
               dict(history=[{"stage": "active", "date": "yesterday"}])]
        for kw in bad:
            with self.assertRaises(ValueError, msg=str(kw)):
                validate([vendor(**kw)])
        with self.assertRaises(ValueError):
            validate([vendor(), vendor()])


if __name__ == "__main__":
    unittest.main()
