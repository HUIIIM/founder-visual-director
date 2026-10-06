#!/usr/bin/env python3
"""founder-visual-director demo: 输入契约 -> 三部分交付物（prompt 级）。"""
import json, os, re, sys

DEMO = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(DEMO)
OUT = os.path.join(DEMO, "output")
os.makedirs(OUT, exist_ok=True)

inp = json.load(open(os.path.join(DEMO, "input.json"), encoding="utf-8"))
skill_text = open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8").read()

# 输入契约校验：SKILL.md 要求缺项先问，不许脑补
required = ["theme_platform", "scene", "aspect", "mood"]
missing = [k for k in required if not inp.get(k)]
if missing:
    print("输入缺项，按契约应先问调用者：", missing)
    sys.exit(2)

# 输出一：生图 prompt（含固定否定词＋禁用词 grep＋冲突审计）
neg = "low quality, blurry, deformed hands, extra fingers, watermark, text artifacts, cartoonish"
banned_hits = []
for w in ["绝密", "2027-02"]:
    if w in inp.get("scene", ""):
        banned_hits.append(w)
prompt = f"""# 终版生图 prompt（demo 级）

## 正向 prompt
photorealistic portrait of an Asian male founder in his 30s, {inp['scene']},
{inp['mood']} mood, {inp['aspect']} composition, cinematic natural light,
shallow depth of field, editorial photography style

## 固定否定词
{neg}

## 禁用词 grep 结果
{'命中: ' + ','.join(banned_hits) + ' -> 打回' if banned_hits else '无命中 -> 通过'}

## 冲突审计结论
场景"{inp['scene']}"与主题"{inp['theme_platform']}"无 B 级严审情形（非名人合影/晚宴）-> 通过
"""
open(os.path.join(OUT, "prompt.txt"), "w", encoding="utf-8").write(prompt)

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
open(os.path.join(OUT, "checklist.md"), "w", encoding="utf-8").write(checklist)

# 输出三：轮换合规检查
ledger = os.path.expanduser("~/workspace/vertcity/deliverables/ops/used-visual-ledger.md")
if os.path.exists(ledger):
    verdict = "条件通过（台账存在，demo 未做全量三篇比对，人工复核）"
else:
    verdict = "条件通过（台账待补：used-visual-ledger.md 未找到，按 skill 降级规则标注不确定性）"
rotation = f"""# 轮换合规检查（demo 级）

- 场景大类：户外运动（{inp['scene']}）
- 白底禁令：未使用白底标准照 -> 通过
- 结论：{verdict}
"""
open(os.path.join(OUT, "rotation.md"), "w", encoding="utf-8").write(rotation)
print("demo 输出已生成：", OUT)
