"""Tests for scripts/make_sbom.py."""

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import make_sbom


class MakeSbom(unittest.TestCase):
    def test_sbom_lists_pinned_dev_tools_with_hashes(self):
        sbom = make_sbom.build("1.1.0", os.path.join(ROOT, "requirements-dev.txt"))
        self.assertEqual(sbom["bomFormat"], "CycloneDX")
        self.assertEqual(sbom["metadata"]["component"]["version"], "1.1.0")
        self.assertEqual(sbom["metadata"]["component"]["licenses"][0]["license"]["id"], "MIT")
        ruff = [c for c in sbom["components"] if c["name"] == "ruff"]
        self.assertEqual(len(ruff), 1)
        self.assertEqual(ruff[0]["scope"], "excluded")
        self.assertTrue(ruff[0]["hashes"])

    def test_bad_version_is_rejected(self):
        with self.assertRaises(ValueError):
            make_sbom.build("v1.1", os.path.join(ROOT, "requirements-dev.txt"))

    def test_cli_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "sbom.json")
            self.assertEqual(make_sbom.main(["make_sbom.py", "1.1.0", out]), 0)
            with open(out, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["specVersion"], "1.5")

    def test_skill_metadata_version_matches_changelog_release(self):
        # The version the release job tags must be the one SKILL.md declares.
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            skill = f.read()
        with open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8") as f:
            changelog = f.read()
        version = skill.split('version: "', 1)[1].split('"', 1)[0]
        self.assertIn(f"## [{version}]", changelog)


if __name__ == "__main__":
    unittest.main()
