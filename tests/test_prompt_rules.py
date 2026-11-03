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
    # Round 6 (#46): rewordings of the same classes that still passed.
    "暗调电影质感的书房": "banned: 暗调电影质感 (prompt-standards.md says never write it into a prompt)",
    "电影级布光的办公室": "banned: 电影级",
    "a 35-year-old founder at a desk": "age, hyphenated",
    "forty-year-old founder on a bench": "age in words, hyphenated",
    "三十五岁的创始人": "age, Chinese numerals",
    "中年创始人在书房": "age: 中年",
    "grinning founder at a cafe": "face word, inflected",
    "beaming founder at the office": "face word",
    "笑着看向窗外的创始人": "face word: 笑",
    "目光坚定地看向远方": "face word: 目光",
    "嘴角上扬的创始人": "face word: 嘴角",
    "founder among celebrities at an event": "B-level, plural",
    "颁奖典礼后台": "B-level: 颁奖典礼",
    "走红毯的瞬间": "B-level: 红毯",
    "公司宴会上敬酒": "B-level: 宴会",
    "白色背景前的证件照": "white-background standard portrait, Chinese",
    "white-background headshot": "white-background standard portrait, hyphenated",
    "headshot against a plain white wall": "white-background standard portrait, plain white",
    "cine\u200bmatic rooftop at dawn": "banned word split by a zero-width space",
    # Round 7: the narrowed rules must still catch the real thing.
    "中年男人在书房": "age: 中年 as a person",
    "四十岁的创始人在书房": "age, Chinese numerals, the founder's own",
    "ID photo of the founder": "standard portrait: id photo as words",
    "founder portrait against a white wall": "white-background portrait: white wall",
    "白墙前的创始人半身照": "white-background portrait: 白墙前",
    "纯白背景的创始人头像": "white-background portrait: 纯白背景",
    "创始人今年四十岁，在书房": "age: the founder's own, subject first",
}

BENIGN = [
    BASE["scene"],
    "founder reading a book about galaxies by a cafe window",
    "walking past a bookstore on a rainy afternoon",
    # Round 6 (#46) regressions: the skill's own tone vocabulary (SKILL.md 叙事调性) and the
    # brand's dark studio direction must not be rejected.
    "书房夜景，grind 叙事",
    "the daily grind at a co-working desk",
    "暗调棚拍肖像，低调布光",
    "dark low-key studio portrait, 棚拍",
    "old money 克制：老钱风书房，深色木书架",
    "强抓眼球的屋顶健身",
    "生活感：周末菜市场买菜",
    "戴眼镜的创始人在窗边看书",
    "a famously quiet library",
    # Round 7 (#46): false positives introduced by the round-6 table.
    "founder in a plain white t-shirt, portrait orientation",
    "a vivid photo essay of a founder's morning commute",
    "solid photo wall in the office lobby",
    "人群中年轻的创业者围坐讨论",
    "初中年级的公益课堂",
    "春节前夕的办公室，中年味渐浓",
    "陪两岁的女儿在公园散步",
    # Round 8 (#46): false positives introduced by the round-7 table.
    "黑白墙绘前的创始人半身照",
    "创始人在白墙画廊里看肖像画展",
    "off-white wall behind a founder portrait",
    "white wall gallery, founder portrait among paintings",
    "女儿两岁生日，创始人在家",
    "孩子三岁那年创办公司的创始人在书房",
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
