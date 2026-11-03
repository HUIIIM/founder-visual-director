"""Rule-table bypass probes and the two-tier design (#42, #46; SOTA #6 round 2, beyond-rubric 3/6).

Each probe passed demo/run.py on main although the rule it dodges is in SKILL.md or
references/prompt-standards.md. Rounds 6-9 of the independent assessment showed that hard-
rejecting every rewording keeps rejecting normal founder scenes, so the table has two tiers:

- HARD_PROBES: forms of the v0.1 rules themselves (normalised), rejected with exit 3.
- REVIEW_PROBES: v0.2 rewordings, flagged 「人工复核：疑似…」 and capped at 条件通过 (exit 5).
- BENIGN and CORPUS: never hard-rejected; BENIGN is never even flagged; the realistic corpus has
  a review-rate ceiling, so proportionality is checked by CI instead of argued each round.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, "demo", "run.py")
with open(os.path.join(ROOT, "demo", "input.json"), encoding="utf-8") as _f:
    BASE = json.load(_f)

HARD_PROBES = {
    "Cinematic-lighting rooftop at dawn": "banned: cinematic lighting, hyphenated",
    "cine\u200bmatic rooftop at dawn": "banned word split by a zero-width space",
    "\uff43inematic rooftop": "banned word, full-width letter",
    "smiling founder at a cafe": "face word (v0.1)",
    "与名人合影的晚宴": "B-level (v0.1)",
    "白底标准照作为封面": "white-background standard portrait (v0.1)",
    "standard portraits of the founder as the banner": "standard portrait, plural (round 10)",
    "standard avatars grid": "standard avatar, plural (round 10)",
    "城市晨跑后拉伸, cinematic\u200blighting": "banned word glued to the next by a zero-width space (round 11)",
    "城市晨跑后拉伸, celebrity\u2122 cameo": "B-level token followed by ™ (round 11)",
}

REVIEW_PROBES = {
    "电影感 天台上的清晨": "banned: cinematic (中文对应)",
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
    # Round 7: the narrowed rules must still catch the real thing.
    "中年男人在书房": "age: 中年 as a person",
    "四十岁的创始人在书房": "age, Chinese numerals, the founder's own",
    "ID photo of the founder": "standard portrait: id photo as words",
    "founder portrait against a white wall": "white-background portrait: white wall",
    "白墙前的创始人半身照": "white-background portrait: 白墙前",
    "纯白背景的创始人头像": "white-background portrait: 纯白背景",
    "创始人今年四十岁，在书房": "age: the founder's own, subject first",
    # Round 9: the founder's own age and white-wall forms the round-8 rules missed.
    "三十五岁女创始人在书房": "age: 女创始人",
    "四十岁出头的创始人": "age: 岁出头",
    "founder headshot on a white wall": "white-background portrait: on a white wall",
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


REVIEW_MARK = "人工复核：疑似"
# Realistic founder content-calendar scenes; the second half deliberately uses trigger
# vocabulary in a benign sense (round 9 of the assessment). None may be hard-rejected.
CORPUS = [
    # work
    "创始人在共享办公区敲键盘", "仓库里清点新到的样品", "团队白板前讨论产品路线图", "深夜书房里改融资 deck",
    "founder reviewing a prototype on the workbench", "standing desk by the window, founder reading contracts",
    "团队晨会，大家说说笑笑", "年会现场，欢声笑语", "路演前在后台候场", "酒店宴会厅改成的路演会场",
    "founder speaking at a startup gala", "founder hosting a dinner party for the team at home",
    "明星产品发布会后台", "voice actor recording session for the brand podcast", "红毯式入口的展会现场",
    "工厂车间里和工人讨论工艺", "咖啡馆角落写周报", "founder on a video call in a quiet meeting room",
    # family
    "创始人和三岁的儿子在客厅搭乐高", "创始人和两岁的女儿在公园散步", "她陪五岁的女儿在公园放风筝",
    "他和七岁的女儿在海边捡贝壳", "她带着三岁的儿子逛菜市场", "其他三岁小孩在游乐场，创始人坐在长椅上",
    "周末和家人在厨房包饺子", "创始人25岁那年创业的第一间办公室，如今改成了会议室",
    "女儿两岁生日，创始人在家", "孩子三岁那年创办公司的创始人在书房",
    # travel / city
    "founder walking through the famous Tsukiji outer market", "a cafe famous for its pour-over, founder at the bar",
    "目光所及之处是整座城市的夜景", "高铁上用笔记本处理邮件", "机场贵宾室候机", "老城区巷子里散步",
    "forties-era jazz bar after a client dinner", "founder portrait in a sixties-style lounge",
    "东京街头的便利店门口", "海边日落时分的木栈道",
    # sport / life
    "城市晨跑后拉伸", "健身房里做硬拉", "周末徒步登山，山顶休息", "雨天在书店翻书",
    "早餐桌上读报纸", "在阳台给植物浇水", "骑行通勤穿过公园", "游泳馆出水的瞬间",
    "戴眼镜的创始人在窗边看书", "黑白墙绘前的创始人半身照", "off-white wall behind a founder portrait",
    "founder in a plain white t-shirt, portrait orientation", "暗调棚拍肖像，低调布光", "书房夜景，grind 叙事",
    "the daily grind at a co-working desk", "人群中年轻的创业者围坐讨论",
]

REVIEW_RATE_CEILING = 0.30


class BypassProbes(unittest.TestCase):
    def test_hard_probes_are_rejected(self):
        for scene, why in HARD_PROBES.items():
            with self.subTest(scene=scene, why=why):
                rc, out, _ = run_demo(scene)
                self.assertEqual(rc, 3, f"{why}: expected reject (3), got {rc}\n{out[-400:]}")

    def test_review_probes_are_flagged_not_passed(self):
        for scene, why in REVIEW_PROBES.items():
            with self.subTest(scene=scene, why=why):
                rc, out, _ = run_demo(scene)
                self.assertEqual(rc, 5, f"{why}: expected conditional (5), got {rc}\n{out[-400:]}")
                self.assertIn(REVIEW_MARK, out, why)

    def test_benign_scenes_are_neither_rejected_nor_flagged(self):
        for scene in BENIGN:
            with self.subTest(scene=scene):
                rc, out, _ = run_demo(scene)
                self.assertIn(rc, (0, 5), out[-400:])
                self.assertNotIn(REVIEW_MARK, out)


def _main_hits(text, tokens):
    """The v0.1 matcher on main: CJK substring, Latin \\btoken\\b case-insensitive on raw text."""
    out = []
    for tok in tokens:
        if re.search(r"[^\x00-\xff]", tok):
            if tok in text:
                out.append(tok)
        elif re.search(r"\b" + re.escape(tok) + r"\b", text, re.IGNORECASE):
            out.append(tok)
    return out


class HardTierNotLooserThanMain(unittest.TestCase):
    """Round 10 (#46): a matching-semantics change narrowed a hard-tier rule (plural
    `standard portraits` passed). For every hard-tier token and common variants, whenever
    main's own matcher would reject the scene, this head must reject it too."""

    def test_hard_tier_is_at_least_as_strict_as_main(self):
        sys.path.insert(0, os.path.join(ROOT, "demo"))
        import run as demo_run

        _, _, banned, face_words, _, _, b_triggers = demo_run.load_rules()
        white = demo_run.WHITE_PORTRAIT_WORDS
        looser = []
        for tok in banned + face_words + b_triggers + white:
            variants = [f"{tok}s at the office", f"{tok.upper()} at the office", f"founder {tok} today"]
            # Round 11: characters that normalisation deletes or folds, next to the token.
            for ch in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff", "\u00ad", "\u2122", "\u2120"):
                variants += [f"founder {tok}{ch}today", f"founder today{ch}{tok} shot"]
            for scene in variants:
                main_rejects = (
                    _main_hits(scene, banned + face_words + b_triggers)
                    or any(w in scene.lower() for w in white)
                )
                if main_rejects and run_demo(scene)[0] != 3:
                    looser.append(scene)
        self.assertEqual(looser, [], "hard tier looser than main")


class Proportionality(unittest.TestCase):
    def test_realistic_corpus_has_no_hard_rejects_and_a_bounded_review_rate(self):
        hard, flagged = [], []
        for scene in CORPUS:
            rc, out, _ = run_demo(scene)
            if rc == 3:
                hard.append(scene)
            elif REVIEW_MARK in out:
                flagged.append(scene)
        self.assertEqual(hard, [], "a realistic scene was hard-rejected")
        rate = len(flagged) / len(CORPUS)
        self.assertLessEqual(rate, REVIEW_RATE_CEILING, f"review rate {rate:.0%}: {flagged}")


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
