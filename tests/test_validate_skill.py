"""Tests for scripts/validate_skill.py. Run: python3 -m unittest discover -s tests -v"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import validate_skill


class RepoIsValid(unittest.TestCase):
    """The committed skill package passes every check."""

    def test_repo_validates(self):
        copy = _copy_repo()
        self.addCleanup(shutil.rmtree, os.path.dirname(copy))
        self.assertEqual(validate_skill.validate(copy), [])

    def test_frontmatter_has_only_spec_fields(self):
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            fields, errors = validate_skill.parse_frontmatter(f.read())
        self.assertEqual(errors, [])
        self.assertLessEqual(set(fields), validate_skill.ALLOWED_FIELDS)
        self.assertEqual(fields["metadata"]["version"], "1.1.0")


class BrokenCopiesFail(unittest.TestCase):
    """Each check rejects the defect it exists for (old-red, new-green regression cases)."""

    def setUp(self):
        self.skill = _copy_repo()
        self.addCleanup(shutil.rmtree, os.path.dirname(self.skill))

    def _edit(self, rel, old, new):
        path = os.path.join(self.skill, rel)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn(old, text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace(old, new, 1))

    def _assert_fails_with(self, fragment):
        errors = validate_skill.validate(self.skill)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_pre_1_1_frontmatter_fields_are_rejected(self):
        # The frontmatter this repo shipped up to v1.0.0 had six non-spec fields.
        self._edit("SKILL.md", "license: MIT\n", 'license: MIT\nversion: "1.0.0"\nuser_invocable: true\n')
        self._assert_fails_with("unexpected frontmatter fields")

    def test_bad_name_is_rejected(self):
        self._edit("SKILL.md", "name: founder-visual-director", "name: Founder--Visual")
        self._assert_fails_with("'name' must be")

    def test_name_must_match_directory(self):
        renamed = os.path.join(os.path.dirname(self.skill), "other-name")
        os.rename(self.skill, renamed)
        self.skill = renamed
        self._assert_fails_with("must match the skill directory name")

    def test_missing_reference_path_is_rejected(self):
        self._edit("SKILL.md", "`references/face-angle-rules.md`", "`references/no-such-file.md`")
        self._assert_fails_with("references/no-such-file.md")

    def test_inline_mandatory_phrase_drift_is_rejected(self):
        self._edit("SKILL.md", "`seamless neck-to-shoulder transition`", "`seamless neck transition`")
        self._assert_fails_with("mandatory phrases")

    def test_inline_negative_band_drift_is_rejected(self):
        self._edit("SKILL.md", "floating head, wide-angle distortion`", "floating head`")
        self._assert_fails_with("negative band")

    def test_duplicate_eval_ids_are_rejected(self):
        path = os.path.join(self.skill, "evals", "evals.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["evals"][1]["id"] = data["evals"][0]["id"]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self._assert_fails_with("duplicated")

    def test_eval_without_assertions_is_rejected(self):
        path = os.path.join(self.skill, "evals", "evals.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["evals"][0]["assertions"] = []
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        self._assert_fails_with("assertions")


def _copy_repo():
    """Copy the skill into <tmp>/founder-visual-director so the directory-name check holds."""
    tmp = tempfile.mkdtemp()
    dest = os.path.join(tmp, "founder-visual-director")
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    return dest


if __name__ == "__main__":
    unittest.main()
