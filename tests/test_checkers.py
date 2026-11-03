"""Unit tests for the rule checkers: rotation, ledger parsing, brand lock, face consistency.

Each case names the rule it covers; the #16 cases reproduce the independent assessment's findings
(they failed on the code before the fix).
"""

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
FIXTURES = os.path.join(ROOT, "demo", "fixtures")
sys.path.insert(0, SCRIPTS)

import check_brand_lock
import check_rotation
import ledger_lib

RULES = check_rotation.load_rotation_rules()


def entry(ledger_id, date, **kw):
    base = {
        "ledger_id": ledger_id, "platform": "小红书", "post_no": ledger_id, "date_made": date,
        "date_published": date, "scene_category": "室内书房", "outfit": f"outfit-{ledger_id}",
        "styling": f"styling-{ledger_id}", "asset_grade": "A", "asset_id": f"asset-{ledger_id}",
        "model_id": "miao-v1", "status": "已发布", "ai_generated": True,
        "ai_disclosure_text": "本图由 AI 生成", "ai_disclosure_method": "platform_declaration",
        "ai_disclosure_basis": "标识办法",
    }
    base.update(kw)
    return base


def candidate(**kw):
    base = {"platform": "小红书", "date": "2026-10-26", "scene_category": "户外运动", "outfit": "new-outfit",
            "styling": "new-styling", "asset_id": "asset-new", "asset_grade": "A",
            "uses_standard_portrait": False, "model_id": "miao-v1", "model_consent_status": "active"}
    base.update(kw)
    return base


def verdict(entries, cand):
    problems = [p for i, e in enumerate(entries) for p in ledger_lib.validate_entry(e, i)]
    return check_rotation.evaluate(entries, cand, RULES, defect_count=len(problems))


class RotationRules(unittest.TestCase):
    def setUp(self):
        self.ledger = [entry("p1", "2026-09-01"), entry("p2", "2026-09-20"), entry("p3", "2026-10-01")]

    def test_clean_candidate_passes(self):
        self.assertEqual(verdict(self.ledger, candidate())["verdict"], "通过")

    def test_adjacent_three_outfit_repeat_is_violation(self):
        self.assertEqual(verdict(self.ledger, candidate(outfit="outfit-p2"))["verdict"], "违规")

    def test_same_category_within_14_days_is_violation(self):
        self.assertEqual(verdict(self.ledger, candidate(scene_category="室内书房", date="2026-10-10"))["verdict"], "违规")

    def test_same_category_after_14_days_passes(self):
        # 3 adjacent posts are all 室内书房, so use one adjacent post of a different category
        ledger = [entry("p1", "2026-09-01", scene_category="户外运动"), entry("p2", "2026-09-20"), entry("p3", "2026-10-01")]
        self.assertEqual(verdict(ledger, candidate(date="2026-10-26"))["verdict"], "违规")  # p1 is adjacent
        ledger.append(entry("p4", "2026-10-05"))
        self.assertEqual(verdict(ledger, candidate(date="2026-10-26"))["verdict"], "通过")

    def test_cooldown_by_previous_grade(self):
        ledger = self.ledger + [entry("p4", "2026-10-15", asset_id="asset-x", asset_grade="S")]
        self.assertEqual(verdict(ledger, candidate(asset_id="asset-x", date="2026-10-26"))["verdict"], "违规")
        self.assertEqual(verdict(ledger, candidate(asset_id="asset-x", date="2026-11-20"))["verdict"], "通过")

    def test_standard_portrait_is_incident(self):
        self.assertEqual(verdict(self.ledger, candidate(uses_standard_portrait=True))["verdict"], "违规")

    def test_revoked_model_consent_is_violation(self):
        self.assertEqual(verdict(self.ledger, candidate(model_consent_status="revoked"))["verdict"], "违规")

    # --- independent assessment #16 -------------------------------------------------------------
    def test_16_p1_2_unrelated_missing_field_keeps_entry_in_checks(self):
        ledger = [{k: v for k, v in e.items() if k != "model_id"} for e in self.ledger]
        result = verdict(ledger, candidate(outfit="outfit-p3"))
        self.assertEqual(result["verdict"], "违规", result)

    def test_16_p1_2_ledger_with_no_usable_entry_cannot_pass(self):
        ledger = [{k: v for k, v in e.items() if k not in ("date_made", "date_published")} for e in self.ledger]
        self.assertEqual(verdict(ledger, candidate())["verdict"], "无法判定")

    def test_16_p1_3_theme_string_as_platform_cannot_pass(self):
        result = verdict(self.ledger, candidate(platform="小红书第 10 篇封面", outfit="outfit-p3"))
        self.assertEqual(result["verdict"], "无法判定")

    def test_16_p1_3_platform_aliases_normalize(self):
        for alias in ("XHS", "xiaohongshu", " 小红书 ", "RedNote"):
            with self.subTest(alias=alias):
                self.assertEqual(verdict(self.ledger, candidate(platform=alias, outfit="outfit-p3"))["verdict"], "违规")

    def test_16_p1_3_no_entries_on_candidate_platform_is_conditional(self):
        self.assertEqual(verdict(self.ledger, candidate(platform="LinkedIn"))["verdict"], "条件通过")

    def test_16_p2_1_missing_candidate_fields_mark_checks_unknown(self):
        result = verdict(self.ledger, {"platform": "小红书", "date": "2026-10-26"})
        self.assertEqual(result["verdict"], "条件通过")
        self.assertTrue(all("无法判定" in line for line in result["checks"][:5]), result["checks"])

    def test_16_p2_4_string_portrait_flag_is_rejected_by_validation(self):
        self.assertTrue(any("布尔" in p for p in ledger_lib.validate_candidate(candidate(uses_standard_portrait="false"))))


class RotationCli(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_rotation.py"), *args],
                              check=False, capture_output=True, text=True)

    def test_exit_codes_distinguish_conditional_from_pass(self):
        ledger = os.path.join(FIXTURES, "ledger-violation.md")
        self.assertEqual(self.run_cli("--ledger", ledger, "--candidate",
                                      os.path.join(FIXTURES, "candidate-violation.json")).returncode, 1)
        self.assertEqual(self.run_cli("--ledger", os.path.join(FIXTURES, "ledger-compliant.md"), "--candidate",
                                      os.path.join(FIXTURES, "candidate-compliant.json")).returncode, 0)
        cond = self.run_cli("--ledger", ledger, "--candidate-json", '{"platform":"小红书","date":"2026-10-26"}')
        self.assertEqual(cond.returncode, 4, cond.stdout)

    def test_16_p2_2_bad_candidate_is_not_reported_as_violation(self):
        res = self.run_cli("--ledger", os.path.join(FIXTURES, "ledger-violation.md"), "--candidate-json", "[1]")
        self.assertNotIn("Traceback", res.stderr)
        self.assertEqual(res.returncode, 2)
        res = self.run_cli("--ledger", os.path.join(FIXTURES, "ledger-violation.md"), "--candidate-json", "{bad")
        self.assertEqual(res.returncode, 3)


class BrandLock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = check_brand_lock.load_bundle(check_brand_lock.DEFAULT_BUNDLE)

    def violations(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
        self.addCleanup(os.unlink, f.name)
        return check_brand_lock.check_file(f.name, *self.bundle)

    def test_16_p2_3_colour_forms_are_all_checked(self):
        for text in ("#FF6B35AA", "rgb(255 107 53)", "hsl(20 100% 60%)", "#F63A", "color: navy",
                     "oklch(0.7 0.1 30)", "rgba(255, 107, 53, .5)"):
            with self.subTest(text=text):
                self.assertTrue(self.violations(text), text)

    def test_palette_colours_and_prose_pass(self):
        for text in ("#0E7C74", "#0e7c74", "rgb(14, 124, 116)", "red jacket in the rain", "Background: city park"):
            with self.subTest(text=text):
                self.assertEqual(self.violations(text), [], text)

    def test_16_p2_2_non_utf8_file_is_unreadable_not_violation(self):
        with tempfile.NamedTemporaryFile("wb", delete=False) as f:
            f.write(b"\xff\xfe bad")
        self.addCleanup(os.unlink, f.name)
        res = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_brand_lock.py"), f.name],
                             check=False, capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.assertNotIn("Traceback", res.stderr)


class FaceConsistency(unittest.TestCase):
    def run_cli(self, path):
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_face_consistency.py"), path],
                              check=False, capture_output=True, text=True)

    def test_fixtures(self):
        self.assertEqual(self.run_cli(os.path.join(FIXTURES, "ledger-compliant.md")).returncode, 0)
        self.assertEqual(self.run_cli(os.path.join(FIXTURES, "ledger-face-violation.md")).returncode, 1)

    def test_16_p2_2_non_object_entries_do_not_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(["oops"], f)
            res = self.run_cli(path)
            self.assertNotIn("Traceback", res.stderr)
            self.assertEqual(res.returncode, 2)

    def test_hash_mismatch_is_violation(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref = os.path.join(tmp, "anchor.txt")
            with open(ref, "w", encoding="utf-8") as f:
                f.write("anchor")
            good = hashlib.sha256(b"anchor").hexdigest()
            e = entry("p1", "2026-10-01", references=[{"file": "anchor.txt", "role": "anchor", "sha256": good}])
            path = os.path.join(tmp, "ledger.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump([e], f, ensure_ascii=False)
            self.assertEqual(self.run_cli(path).returncode, 0)
            bad = copy.deepcopy(e)
            bad["references"][0]["sha256"] = "0" * 64
            with open(path, "w", encoding="utf-8") as f:
                json.dump([bad], f, ensure_ascii=False)
            self.assertEqual(self.run_cli(path).returncode, 1)


if __name__ == "__main__":
    unittest.main()
