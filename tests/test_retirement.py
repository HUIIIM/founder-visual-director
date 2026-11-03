"""Permanent retirement and key normalisation in check_rotation (#41; SOTA #6 round 2, beyond-rubric 1/2).

On main @72b0223:
- a published image could be posted again once its asset's cooldown ended, or on another
  platform (the red line "已发布图永久退役，含跨平台复用" was "guarded by manual review");
- asset_id / outfit / styling were compared exactly, so "XHS-ASSET-009", a trailing space or a
  full-width「＋」slipped past the cooldown and adjacent-3 checks.
"""

import hashlib
import json
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import check_rotation

FIXTURES = os.path.join(ROOT, "demo", "fixtures")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def compliant_ledger():
    with open(os.path.join(FIXTURES, "ledger-compliant.md"), encoding="utf-8") as f:
        entries = json.loads(re.search(r"```json\n(.*?)```", f.read(), re.DOTALL).group(1))
    for e in entries:
        e["image_sha256"] = sha("image-" + e["ledger_id"])
    return entries


def compliant_candidate(**kw):
    with open(os.path.join(FIXTURES, "candidate-compliant.json"), encoding="utf-8") as f:
        cand = json.load(f)
    cand.update(kw)
    return cand


def run(candidate, entries=None):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "ledger.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(compliant_ledger() if entries is None else entries, f, ensure_ascii=False)
        code, report = check_rotation.run(path, candidate)
    return code, report


def line(report, name):
    return next(ln for ln in report.splitlines() if name in ln and ln.startswith("- 检查"))


class PermanentRetirement(unittest.TestCase):
    def test_baseline_passes(self):
        code, report = run(compliant_candidate())
        self.assertEqual(code, 0, report)

    def test_published_image_reused_after_cooldown_is_a_violation(self):
        # xhs-2026-003 was published 2026-09-18 (B grade, 14-day cooldown long over).
        code, report = run(compliant_candidate(image_sha256=sha("image-xhs-2026-003")))
        self.assertEqual(code, 1, report)
        self.assertIn("违规", line(report, "已发布图永久退役"))

    def test_published_image_reused_on_another_platform_is_a_violation(self):
        code, report = run(compliant_candidate(platform="IG", image_sha256=sha("image-xhs-2026-009")))
        self.assertEqual(code, 1, report)

    def test_retired_entry_still_counts(self):
        entries = compliant_ledger()
        entries[2]["status"] = "已退役"
        code, report = run(compliant_candidate(image_sha256=sha("image-xhs-2026-003")), entries)
        self.assertEqual(code, 1, report)

    def test_hash_case_and_whitespace_variants_match(self):
        digest = " " + sha("image-xhs-2026-007").upper() + " "
        code, report = run(compliant_candidate(image_sha256=digest))
        self.assertEqual(code, 1, report)

    def test_missing_image_hash_is_cannot_judge_not_pass(self):
        cand = compliant_candidate()
        cand.pop("image_sha256")
        code, report = run(cand)
        self.assertEqual(code, 4, report)
        self.assertIn("无法判定", line(report, "已发布图永久退役"))

    def test_published_entries_without_hash_are_cannot_judge_not_pass(self):
        # #49 round 1: a ledger whose published entries carry no image_sha256 gave 通过 (vacuous).
        entries = compliant_ledger()
        for e in entries:
            e.pop("image_sha256")
        code, report = run(compliant_candidate(), entries)
        self.assertEqual(code, 4, report)
        self.assertIn("无法判定", line(report, "已发布图永久退役"))
        self.assertIn("缺 image_sha256", report)

    def test_malformed_hash_line_is_cannot_judge_not_pass(self):
        # #49 round 2 P2: the overall verdict was capped, but the check line still said 通过.
        for kw in ({"image_sha256": "md5:" + sha("x")}, {"image_sha256": sha("x")[:63]}):
            with self.subTest(**kw):
                code, report = run(compliant_candidate(**kw))
                self.assertNotEqual(code, 0, report)
                self.assertIn("无法判定", line(report, "已发布图永久退役"))
        entries = compliant_ledger()
        entries[0]["image_sha256"] = "md5:" + entries[0]["image_sha256"]
        code, report = run(compliant_candidate(), entries)
        self.assertIn("无法判定", line(report, "已发布图永久退役"))

    def test_sha256_label_is_not_part_of_the_hash(self):
        # #49 round 3: "sha256:<hex>" on either or both sides is the same digest.
        target = sha("image-xhs-2026-009")
        for cand, led in (("sha256:" + target, None), (target, "sha256:" + target), ("SHA256:" + target, "sha256:" + target)):
            with self.subTest(candidate=cand[:10], ledger=(led or "")[:10]):
                entries = compliant_ledger()
                if led:
                    entries[0]["image_sha256"] = led
                code, report = run(compliant_candidate(image_sha256=cand), entries)
                self.assertEqual(code, 1, report)
                self.assertIn("违规", line(report, "已发布图永久退役"))

    def test_malformed_hash_is_a_candidate_problem(self):
        code, report = run(compliant_candidate(image_sha256="not-a-hash"))
        self.assertNotEqual(code, 0, report)
        self.assertIn("image_sha256 非法", report)

    def test_reusing_a_source_asset_after_cooldown_with_a_new_image_passes(self):
        # asset_id is reusable source material (rotation-rules.md cooldown), not the image.
        code, report = run(compliant_candidate(asset_id="xhs-asset-003"))
        self.assertEqual(code, 0, report)


class KeyNormalisation(unittest.TestCase):
    def test_asset_id_variants_hit_the_cooldown(self):
        for variant in ("XHS-ASSET-009", "xhs-asset-009 ", "ｘｈｓ-asset-009", "xhs-asset-009\u200b"):
            with self.subTest(variant=repr(variant)):
                code, report = run(compliant_candidate(asset_id=variant))
                self.assertEqual(code, 1, report)
                self.assertIn("违规", line(report, "冷却期"))

    def test_cooldown_counts_other_platforms(self):
        # xhs-asset-009 used on 小红书 2026-10-24 (A grade, 21 days); IG on 10-26 is inside it.
        code, report = run(compliant_candidate(platform="IG", asset_id="xhs-asset-009"))
        self.assertEqual(code, 1, report)
        self.assertIn("违规", line(report, "冷却期"))

    def test_outfit_variants_hit_adjacent_three(self):
        for variant in ("藏青西装外套+白衬衫  ", "藏青西装外套＋白衬衫", "藏青西装外套 + 白衬衫", "藏青西装外套、白衬衫"):
            with self.subTest(variant=variant):
                code, report = run(compliant_candidate(outfit=variant))
                self.assertEqual(code, 1, report)
                self.assertIn("违规", line(report, "相邻 3 篇"))

    def test_malformed_ledger_asset_id_is_a_defect(self):
        entries = compliant_ledger()
        entries[0]["asset_id"] = "xhs_asset 009"
        code, report = run(compliant_candidate(), entries)
        self.assertEqual(code, 4, report)
        self.assertIn("asset_id 非法", report)


if __name__ == "__main__":
    unittest.main()
