"""Rule-table bypass probes (#42; independent SOTA assessment #6 round 2, beyond-rubric 3 and 6).

Each probe passed demo/run.py on main @32466b7 although the rule it dodges is in SKILL.md or
references/prompt-standards.md. They must now be rejected (exit 3), while benign scenes still
get through (exit 0 pass or 5 conditional pass), and the QA checklist must carry every item.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "demo", "run.py")
with open(os.path.join(ROOT, "demo", "input.json"), encoding="utf-8") as _f:
    BASE = json.load(_f)

BYPASS_PROBES = {
    "电影感 天台上的清晨": "banned: cinematic (中文对应)",
    "Cinematic-lighting rooftop at dawn": "banned: cinematic lighting, hyphenated",
    "a founder in his thirties at a desk": "age in words",
    "thirty-something founder working late": "age in words",
    "四十多岁的创始人在书房": "age in Chinese words",
    "smiley founder at a cafe": "face word, inflected",
    "眼神坚定地看向远方": "face word 眼神",
    "office corner, lifted shadows, brightened face": "banned: lift shadows / brighten, inflected",
    "dinner party with a famous actor": "B-level, English",
    "gala evening portrait in a ballroom": "B-level, English",
    "studio portrait on white backdrop": "white-background standard portrait, English",
}

BENIGN = [
    BASE["scene"],
    "founder reading a book about galaxies by a cafe window",
    "walking past a bookstore on a rainy afternoon",
]


def run_demo(scene):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "input.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dict(BASE, scene=scene), f, ensure_ascii=False)
        env = dict(os.environ, FVD_DEMO_OUT=os.path.join(tmp, "out"))
        env.pop("FVD_LEDGER_PATH", None)
        proc = subprocess.run([sys.executable, RUN, path], capture_output=True, text=True, env=env, check=False)
        checklist = ""
        cpath = os.path.join(tmp, "out", "checklist.md")
        if os.path.exists(cpath):
            with open(cpath, encoding="utf-8") as f:
                checklist = f.read()
        return proc.returncode, proc.stdout, checklist


class BypassProbes(unittest.TestCase):
    def test_probes_are_rejected(self):
        for scene, why in BYPASS_PROBES.items():
            with self.subTest(scene=scene, why=why):
                rc, out, _ = run_demo(scene)
                self.assertEqual(rc, 3, f"{why}: expected reject (3), got {rc}\n{out[-400:]}")

    def test_benign_scenes_are_not_rejected(self):
        for scene in BENIGN:
            with self.subTest(scene=scene):
                rc, out, _ = run_demo(scene)
                self.assertIn(rc, (0, 5), out[-400:])


class Checklist(unittest.TestCase):
    def test_checklist_carries_every_item_from_references(self):
        # evals.json #7: face-angle 3, proportion 10, photorealism 11, background 5, each marked.
        _, _, checklist = run_demo(BASE["scene"])
        counts, section = {}, None
        for line in checklist.splitlines():
            if line.startswith("## "):
                section = line[3:]
                counts[section] = 0
            elif line.startswith("- [ ] ") and section:
                counts[section] += 1
                self.assertTrue(line.endswith("待全尺寸复核") or section == "发布前", line)
        got = [n for title, n in counts.items() if title != "发布前"]
        self.assertEqual(got, [3, 10, 11, 5], counts)


if __name__ == "__main__":
    unittest.main()
