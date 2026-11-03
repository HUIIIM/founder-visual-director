"""Model-consent check in check_rotation (independent review #32 P2-5).

Before: the check only read a caller-supplied model_consent_status, so omitting it printed
"模特资产授权：通过" and a revoked model recorded in the ledger was never consulted.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import check_rotation

RULES = check_rotation.load_rotation_rules()


def entry(ledger_id, **kw):
    base = {"ledger_id": ledger_id, "platform": "小红书", "date_made": "2026-09-01", "date_published": "2026-09-01",
            "status": "已发布", "scene_category": "室内书房", "outfit": f"o-{ledger_id}", "styling": f"s-{ledger_id}",
            "asset_id": f"a-{ledger_id}", "asset_grade": "A", "model_id": "miao-v1"}
    base.update(kw)
    return base


def candidate(**kw):
    base = {"platform": "小红书", "date": "2026-10-26", "scene_category": "户外运动", "outfit": "new",
            "styling": "new", "asset_id": "a-new", "asset_grade": "A", "uses_standard_portrait": False}
    base.update(kw)
    return base


def consent_line(entries, cand):
    result = check_rotation.evaluate(entries, cand, RULES)
    line = next(c for c in result["checks"] if c.startswith("模特资产授权"))
    return result["verdict"], line


class ModelConsent(unittest.TestCase):
    def test_omitted_model_id_is_not_a_pass(self):
        verdict, line = consent_line([entry("p1")], candidate())
        self.assertIn("无法判定", line)
        self.assertEqual(verdict, "条件通过")

    def test_revocation_recorded_in_ledger_blocks_the_post(self):
        ledger = [entry("p1"), entry("p0", status="已退役", model_consent_status="revoked", platform="LinkedIn")]
        verdict, line = consent_line(ledger, candidate(model_id="miao-v1"))
        self.assertEqual(verdict, "违规")
        self.assertIn("revoked", line)

    def test_expired_candidate_status_blocks_the_post(self):
        verdict, _ = consent_line([entry("p1")], candidate(model_id="miao-v1", model_consent_status="expired"))
        self.assertEqual(verdict, "违规")

    def test_unknown_consent_is_cannot_judge(self):
        verdict, line = consent_line([entry("p1")], candidate(model_id="miao-v1"))
        self.assertIn("没有授权状态", line)
        self.assertEqual(verdict, "条件通过")

    def test_active_consent_passes(self):
        verdict, line = consent_line([entry("p1")], candidate(model_id="miao-v1", model_consent_status="active"))
        self.assertEqual(line, "模特资产授权：通过")
        self.assertEqual(verdict, "通过")

    def test_ledger_active_record_counts_as_known(self):
        verdict, _ = consent_line([entry("p1", model_consent_status="active")], candidate(model_id="miao-v1"))
        self.assertEqual(verdict, "通过")

    def test_no_model_asset(self):
        verdict, _ = consent_line([entry("p1")], candidate(model_id="none"))
        self.assertEqual(verdict, "通过")


if __name__ == "__main__":
    unittest.main()
