"""Model-consent check in check_rotation (independent review #32 P2-5).

Before: the check only read a caller-supplied model_consent_status, so omitting it printed
"模特资产授权：通过" and a revoked model recorded in the ledger was never consulted.
"""

import hashlib
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
            "asset_id": f"a-{ledger_id}", "asset_grade": "A", "model_id": "miao-v1",
            "image_sha256": hashlib.sha256(f"image-{ledger_id}".encode()).hexdigest()}
    base.update(kw)
    return base


def candidate(**kw):
    base = {"platform": "小红书", "date": "2026-10-26", "scene_category": "户外运动", "outfit": "new",
            "styling": "new", "asset_id": "a-new", "asset_grade": "A", "uses_standard_portrait": False,
            "image_sha256": "f57d196a115ea44f2531b38d8c758498ffb15edba2735d3630215859a4f7ae76"}
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

    def test_case_and_whitespace_variants_cannot_bypass_revocation(self):
        # #37 residual: exact-match lookup let "Miao-v1" / "miao-v1 " past a ledger revocation.
        ledger = [entry("p1"), entry("p0", status="已退役", model_consent_status="revoked")]
        for variant in ("Miao-v1", "miao-v1 ", " MIAO-V1\t"):
            with self.subTest(variant=variant):
                verdict, line = consent_line(ledger, candidate(model_id=variant, model_consent_status="active"))
                self.assertEqual(verdict, "违规")
                self.assertIn("revoked", line)

    def test_ledger_variant_spelling_still_matches(self):
        ledger = [entry("p1"), entry("p0", model_id=" Miao-V1", model_consent_status="revoked")]
        verdict, _ = consent_line(ledger, candidate(model_id="miao-v1", model_consent_status="active"))
        self.assertEqual(verdict, "违规")

    def test_none_contradicted_by_ledger_asset_is_cannot_judge(self):
        # "none" is self-declared; the same asset_id carrying a model in the ledger contradicts it.
        ledger = [entry("p1", asset_id="a-shared")]
        verdict, line = consent_line(ledger, candidate(model_id="none", asset_id="a-shared"))
        self.assertIn("无法判定", line)
        self.assertIn("a-shared", line)
        self.assertEqual(verdict, "条件通过")

    def test_none_cross_check_ignores_asset_id_case_and_whitespace(self):
        # IVV round 4: "XHS-ASSET-009" vs ledger "xhs-asset-009" slipped past the none cross-check.
        ledger = [entry("p1", asset_id="xhs-asset-009")]
        for variant in ("XHS-ASSET-009", "xhs-asset-009 "):
            with self.subTest(variant=variant):
                verdict, line = consent_line(ledger, candidate(model_id="none", asset_id=variant))
                self.assertIn("无法判定", line)
                self.assertEqual(verdict, "条件通过")

    def test_malformed_ledger_model_id_is_a_defect_not_a_silent_pass(self):
        # IVV round 5: a revocation recorded under a look-alike id was ignored with no warning.
        import ledger_lib

        for bad in ("miao\u200b-v1", "miao\uff0dv1", "Miao_v1"):
            with self.subTest(bad=bad):
                problems = ledger_lib.validate_entry(
                    entry("p0", status="已退役", model_consent_status="revoked", model_id=bad), 0
                )
                self.assertTrue(any("model_id" in p for p in problems), problems)
        self.assertFalse(
            any("model_id" in p for p in ledger_lib.validate_entry(entry("p1", model_id=" Miao-V1"), 0))
        )

    def test_consent_line_is_not_pass_when_a_ledger_record_is_malformed(self):
        # IVV round 6: the verdict was capped, but the consent line itself still printed 通过.
        for kw in ({"model_id": "miao\uff0dv1"}, {"model_consent_status": "Revoked"}):
            with self.subTest(**{k: repr(v) for k, v in kw.items()}):
                ledger = [entry("p1"), entry("p0", status="已退役", **kw)]
                _, line = consent_line(ledger, candidate(model_id="miao-v1", model_consent_status="active"))
                self.assertIn("无法判定", line)

    def test_none_variant_spelling_is_none(self):
        verdict, _ = consent_line([entry("p1")], candidate(model_id=" None "))
        self.assertEqual(verdict, "通过")

    def test_malformed_model_id_rejected_by_validation(self):
        import ledger_lib

        problems = ledger_lib.validate_candidate(candidate(model_id="miao v1; rm"))
        self.assertTrue(any("model_id" in p for p in problems), problems)
        self.assertFalse(
            any("model_id" in p for p in ledger_lib.validate_candidate(candidate(model_id="Miao-V1 ")))
        )


if __name__ == "__main__":
    unittest.main()
