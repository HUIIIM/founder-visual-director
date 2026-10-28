#!/usr/bin/env python3
"""founder-visual-director demo: 输入契约 -> 三部分交付物（prompt 级）。

规则来源（运行时直读，本脚本不内置任何规则副本）：
- references/prompt-standards.md：强制短语、固定否定词带、禁用词表 v1.0、机读规则附表
  （面部禁词 / 年龄模式 / 互斥对 / B 级触发词）。
- 轮换预检：scripts/check_rotation.py 真读台账判定（相邻 3 篇 / 14 天 / 冷却期等），
  规则数值直读 references/rotation-rules.md，台账格式见 references/ledger-format.md。
任一规则集读取为空 -> 退出码 4（规则读取失败），绝不静默放行。

用法：python3 demo/run.py [input.json]（默认 demo/input.json）
输入除契约四项外可带结构化候选字段（platform / post_no / date / scene_category /
outfit / styling / asset_id / asset_grade / uses_standard_portrait），供轮换预检真读判定；
date 缺省取当天。
输出目录：demo/output/，可用环境变量 FVD_DEMO_OUT 覆盖；
台账路径：环境变量 FVD_LEDGER_PATH 或 skill 根目录 used-visual-ledger.md。
退出码：0 通过 / 2 输入缺项 / 3 规则打回 / 4 规则读取失败。
"""
import json
import os
import re
import sys
from datetime import date as _date

DEMO = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(DEMO)
STANDARDS = os.path.join(SKILL, "references", "prompt-standards.md")
WHITE_PORTRAIT_WORDS = ["标准照", "标准头像", "standard portrait", "standard avatar"]
WHITE_STUDIO_WORDS = ["白底", "棚拍", "white background"]
OUT = os.environ.get("FVD_DEMO_OUT") or os.path.join(DEMO, "output")
os.makedirs(OUT, exist_ok=True)


def fenced_block_after(text, header):
    """取指定标题之后第一个 ``` 代码块的内容行。"""
    idx = text.find(header)
    if idx < 0:
        return []
    seg = text[idx + len(header):]
    m = re.search(r"```[^\n]*\n(.*?)```", seg, re.DOTALL)
    if not m:
        return []
    return [ln.rstrip() for ln in m.group(1).splitlines() if ln.strip()]


def load_rules():
    with open(STANDARDS, encoding="utf-8") as f:
        text = f.read()
    phrases = [ln.strip() for ln in fenced_block_after(text, "## 强制短语（正向必带）")]
    neg_lines = fenced_block_after(text, "## 固定否定词带（每次必带）")
    negative = " ".join(ln.strip() for ln in neg_lines)
    banned_raw = fenced_block_after(text, "## 禁用词表 v1.0")
    banned = [t.strip() for t in "/".join(banned_raw).split("/") if t.strip()]
    appendix = {}
    section = None
    for ln in fenced_block_after(text, "## 机读规则附表"):
        s = ln.strip()
        m = re.match(r"^\[(.+)\]$", s)
        if m:
            section = m.group(1)
            appendix[section] = []
        elif section:
            appendix[section].append(s)
    face_words = [t.strip() for chunk in appendix.get("face_words", [])
                  for t in chunk.split(",") if t.strip()]
    age_patterns = appendix.get("age_patterns", [])
    pairs = []
    for ln in appendix.get("conflict_pairs", []):
        if "<>" in ln:
            left, right = ln.split("<>", 1)
            pairs.append(([t.strip() for t in left.split("|") if t.strip()],
                          [t.strip() for t in right.split("|") if t.strip()]))
    b_triggers = [t.strip() for chunk in appendix.get("b_level_triggers", [])
                  for t in chunk.split(",") if t.strip()]
    return phrases, negative, banned, face_words, age_patterns, pairs, b_triggers


def hits_in(text, tokens):
    """词表命中：拉丁词按词边界（不分大小写），中文按子串。"""
    out = []
    for tok in tokens:
        if re.search(r"[^\x00-\xff]", tok):
            if tok in text:
                out.append(tok)
        elif re.search(r"\b" + re.escape(tok) + r"\b", text, re.IGNORECASE):
            out.append(tok)
    return out


def clean(value):
    """单行化并去掉 markdown 标题符，防止输入伪造交付物里的段落（如「## 终判：通过」）。"""
    return re.sub(r"\s+", " ", value).replace("#", "").strip()


def load_input(path):
    """读取并校验输入：必须是 JSON 对象，字符串字段一律单行化。不合契约返回 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            inp = json.load(f)
    except (OSError, ValueError) as e:
        print(f"输入无法读取（{path}），按契约应先问调用者：{e}")
        return None
    if not isinstance(inp, dict):
        print("输入必须是 JSON 对象，按契约应先问调用者")
        return None
    return {k: clean(v) if isinstance(v, str) else v for k, v in inp.items()}


def main():
    phrases, negative, banned, face_words, age_patterns, pairs, b_triggers = load_rules()
    if not (phrases and negative and banned and face_words and age_patterns and pairs and b_triggers):
        print("规则读取失败：references/prompt-standards.md 规则集不完整，拒绝放行")
        return 4

    sys.path.insert(0, os.path.join(SKILL, "scripts"))
    try:
        import check_rotation
    except ImportError:
        print("校验组件读取失败：scripts/check_rotation.py 不可导入，拒绝放行")
        return 4

    input_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(DEMO, "input.json")
    inp = load_input(input_path)
    if inp is None:
        return 2

    # 输入契约校验：SKILL.md 要求缺项先问，不许脑补
    required = ["theme_platform", "scene", "aspect", "mood"]
    missing = [k for k in required if not isinstance(inp.get(k), str) or not inp[k]]
    if missing:
        print("输入缺项，按契约应先问调用者：", missing)
        return 2

    scene, mood, aspect, theme = inp["scene"], inp["mood"], inp["aspect"], inp["theme_platform"]

    # 正向 prompt：身份一致性只靠 anchor 参考图，不写面部/年龄描述（SKILL.md 模板铁律 1）；
    # 强制短语逐字取自 references，不在本脚本内另存副本。
    positive_lines = [
        f"photorealistic documentary photograph, {scene},",
        f"{mood} mood, {aspect} composition, single natural key light,",
        "candid moment in motion, visible skin texture, unretouched,",
    ] + phrases
    positive = "\n".join(positive_lines)

    # 检查一：禁用词 grep（仅扫描正向 prompt，SKILL.md Step 3；否定词带不在扫描范围内）
    banned_hits = hits_in(positive, banned)
    # 检查二：面部描述禁令。强制短语为规范原文（其中 eye-level 为机位术语、非面部描述），
    # 与否定词带同理：扫描前先整段掩码，避免把宪法原文误判为违规。
    masked = positive
    for ph in phrases:
        masked = masked.replace(ph, " ")
    face_hits = hits_in(masked, face_words)
    age_hits = [p for p in age_patterns if re.search(p, masked, re.IGNORECASE)]
    # 检查三：冲突审计（互斥对，真判定：同对两边同时出现即冲突）
    conflicts = []
    scan_all = positive + " " + scene
    for left, right in pairs:
        lh, rh = hits_in(scan_all, left), hits_in(scan_all, right)
        if lh and rh:
            conflicts.append(f"{lh[0]} x {rh[0]}")
    # 检查四：B 级严审（真实可识别人物场景不在本 skill 内放行，SKILL.md Step 2-1）
    b_hits = hits_in(scene + " " + theme, b_triggers)
    # 检查五：白底标准照永不作内容配图（白底三禁 1，事故级；不依赖台账）
    white_hits = [w for w in WHITE_PORTRAIT_WORDS if w in scene.lower()]
    if inp.get("uses_standard_portrait") is True:
        white_hits.append("uses_standard_portrait")

    reasons = []
    if banned_hits:
        reasons.append("禁用词命中：" + ",".join(banned_hits))
    if face_hits or age_hits:
        reasons.append("面部/年龄描述命中：" + ",".join(face_hits + age_hits))
    if conflicts:
        reasons.append("互斥指令：" + "；".join(conflicts))
    if b_hits:
        reasons.append("B 级严审情形：" + ",".join(b_hits) + "（转 B 级流程，本 demo 不放行）")
    if white_hits:
        reasons.append("白底标准照作内容配图：" + ",".join(white_hits) + "（事故级，白底三禁 1）")
    rejected = bool(reasons)
    verdict = "打回（" + "；".join(reasons) + "）" if rejected else "通过"

    # AI 标识与声明（SKILL.md Step 5 第七节；字段与台账正式格式 v1.0 同名，references/ledger-format.md）
    method = "c2pa + platform_declaration" if "LinkedIn" in theme else "platform_declaration"
    disclosure = f"""## AI 标识与声明
- ai_generated: true（本交付物为 AI 生成合成内容的生图 prompt）
- ai_disclosure_text: 本图由 AI 生成
- ai_disclosure_method: {method}
- ai_disclosure_basis: 《人工智能生成合成内容标识办法》；小红书 AI 生成内容标识规则；EU AI Act Art. 50"""

    prompt = f"""# 终版生图 prompt（demo 级）

## 正向 prompt
{positive}

## 固定否定词带
{negative}

## 禁用词 grep 结果
{'命中: ' + ','.join(banned_hits) + ' -> 打回' if banned_hits else '无命中 -> 通过'}

## 面部描述检查结果
{'命中: ' + ','.join(face_hits + age_hits) + ' -> 打回' if (face_hits or age_hits) else '无命中 -> 通过'}

## 冲突审计结论
{'互斥指令: ' + '；'.join(conflicts) + ' -> 打回' if conflicts else '无互斥指令 -> 通过'}

## B 级严审检查
{'命中: ' + ','.join(b_hits) + ' -> 转 B 级严审，本 demo 不放行' if b_hits else '无 B 级严审情形 -> 通过'}

## 白底禁令检查
{'命中: ' + ','.join(white_hits) + ' -> 打回（事故级）' if white_hits else '未使用白底标准照 -> 通过'}

{disclosure}

## 终判：{verdict}
"""
    with open(os.path.join(OUT, "prompt.txt"), "w", encoding="utf-8") as f:
        f.write(prompt)

    # 输出二：QA 检查表骨架（skill 真实四段结构）
    checklist = """# QA 检查表（demo 骨架）

## 脸角度三规则
- [ ] 角度预设已二选一写死（无中间态）
- [ ] 无死亡角度/透视畸变
- [ ] 眼神方向与叙事一致

## 人体比例十项
- [ ] 手部结构正常（demo 级：待全尺寸复核）
- [ ] 肩颈/四肢比例自然
- [ ] 其余八项：待全尺寸目检

## 真实感（解剖/物理/全局观感）
- [ ] 光影方向一致
- [ ] 材质边缘无 AI 塑料感

## 背景专项
- [ ] 背景无乱入文字/畸形路人
- [ ] 背景虚化层次自然

> 任一红线 fail 即整单打回。demo 级全部标"待全尺寸复核"。
"""
    with open(os.path.join(OUT, "checklist.md"), "w", encoding="utf-8") as f:
        f.write(checklist)

    # 输出三：轮换合规检查（真读台账判定：scripts/check_rotation.py；
    # 台账缺失/不可解析时按降级规则输出「无法判定」，绝不假装通过）
    ledger = os.environ.get("FVD_LEDGER_PATH") or os.path.join(SKILL, "used-visual-ledger.md")
    candidate = {
        "platform": inp.get("platform") or theme,
        "date": inp.get("date") or _date.today().isoformat(),
        "scene_category": inp.get("scene_category"),
        "outfit": inp.get("outfit"),
        "styling": inp.get("styling"),
        "asset_id": inp.get("asset_id"),
        "asset_grade": inp.get("asset_grade"),
        "uses_standard_portrait": bool(inp.get("uses_standard_portrait", False)),
    }
    # 场景文字本身写明白底标准照/白底棚拍时，不靠调用者另设标志才拦（白底三禁）
    if white_hits:
        candidate["uses_standard_portrait"] = True
    if not candidate["scene_category"] and any(w in scene for w in WHITE_STUDIO_WORDS):
        candidate["scene_category"] = "白底棚拍"
    _rot_code, rot_report = check_rotation.run(ledger, candidate)
    # 仓内台账路径按相对路径展示：样例输出不带本机绝对路径，可在任何机器上复现
    ledger_abs = os.path.abspath(ledger)
    if ledger_abs.startswith(SKILL + os.sep):
        rot_report = rot_report.replace(ledger_abs, os.path.relpath(ledger_abs, SKILL))
    entry = f"""## 拟登记台账条目（字段见 references/ledger-format.md 正式格式 v1.0）
- platform / post_no：{candidate['platform']} / {inp.get('post_no') or theme}
- scene_category：{candidate['scene_category']}
- asset_id / asset_grade：{candidate['asset_id']} / {candidate['asset_grade']}
- ai_generated：true
- ai_disclosure_text：本图由 AI 生成
- ai_disclosure_method：{method}
- ai_disclosure_basis：《人工智能生成合成内容标识办法》；小红书 AI 生成内容标识规则；EU AI Act Art. 50""" if not rejected else "## 台账登记\n- 本单已打回，不登记台账。"
    rotation = rot_report + "\n" + entry + "\n"
    with open(os.path.join(OUT, "rotation.md"), "w", encoding="utf-8") as f:
        f.write(rotation)
    print("demo 输出已生成：", OUT)
    print("终判：" + verdict)
    return 3 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
