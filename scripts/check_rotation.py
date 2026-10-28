#!/usr/bin/env python3
"""轮换预检（真读台账版）：SKILL.md Step 1 的可执行实现。

判定规则运行时直读 references/rotation-rules.md（场景大类表、冷却期数值），
本脚本不内置规则副本；检查对象是台账实读条目（references/ledger-format.md v1.0）。

检查项（均真读台账判定，逐项给出证据行）：
1. 相邻 3 篇：同平台最近 3 篇（已发布/待发）与候选的场景大类/服装/造型任一重复 -> 违规
2. 14 天：同平台同场景大类条目与候选生效日期相差 <14 天 -> 违规
3. 冷却期：同一 asset_id 上次使用距候选日期 < 冷却天数（按上次条目等级 S30/A21/B14）-> 违规
4. S 级月度上限：同平台同月 S 级已用 >=2 次且候选为 S 级 -> 违规（轮换四条 4）
5. 白底：候选使用白底标准照 -> 事故级违规；白底棚拍大类同平台同月第二次 -> 违规（白底三禁）

降级规则（SKILL.md Step 1 / rotation-rules.md）：
- 台账缺失/不可解析 -> 结论「无法判定」，三项检查不执行，绝不输出「通过」；
- 台账条目有字段缺陷 -> 在有效条目上判定，结论上限为「条件通过」并逐条标注不确定性；
- 候选字段不全 -> 受影响的检查标注「无法判定」，结论上限为「条件通过」。
退出码：0 通过 / 1 违规 / 2 降级或无法判定 / 3 规则读取失败或用法错误。

用法：
  python3 scripts/check_rotation.py --ledger <台账.md> --candidate <候选.json>
  python3 scripts/check_rotation.py --ledger <台账.md> --candidate-json '<json>'
"""
import argparse
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_lib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(REPO, "references", "rotation-rules.md")
ACTIVE_STATUSES = ("已发布", "待发")


def load_rotation_rules(path=RULES):
    """从 rotation-rules.md 直读场景大类表与冷却期数值。任一读取为空返回 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = re.search(r"## 场景大类（判定粒度）\s*\n(.*?)\n## ", text, re.DOTALL)
    if not m:
        return None
    categories = []
    for line in m.group(1).splitlines():
        line = re.sub(r"（[^）]*）", "", line)  # 去括注（含其中的 / 分隔）
        if "/" not in line:
            continue  # 说明行不含分隔符，跳过；只收大类枚举行
        categories.extend(c.strip() for c in line.split("/") if c.strip())
    cooldowns = {}
    cm = re.search(r"## 冷却期\s*\n(.*?)\n## ", text, re.DOTALL)
    if cm:
        for grade, days in re.findall(r"-\s*([SAB])\s*级：\s*(\d+)\s*天", cm.group(1)):
            cooldowns[grade] = int(days)
    if not categories or len(cooldowns) != 3:
        return None
    return categories, cooldowns


def _d(value):
    try:
        return date.fromisoformat(str(value).strip())
    except (ValueError, TypeError):
        return None


def evaluate(entries, candidate, rules, invalid_count=0):
    """真读判定。返回 dict：verdict（通过/条件通过/违规/无法判定）、findings、
    checks（逐项状态行）、notes（不确定性标注）。"""
    categories, cooldowns = rules
    findings, checks, notes = [], [], []
    cand_problems = ledger_lib.validate_candidate(candidate)
    cand_date = _d(candidate.get("date"))
    if invalid_count:
        notes.append(f"台账有 {invalid_count} 条字段缺陷（见校验输出），结论带不确定性")
    if cand_problems:
        notes.append("候选字段不全：" + "；".join(cand_problems))

    if cand_date is None:
        checks.append("全部检查：无法判定（候选 date 缺失或不可解析）")
        return {"verdict": "无法判定", "findings": findings, "checks": checks, "notes": notes}

    platform = candidate.get("platform")
    same_platform = [e for e in entries
                     if e.get("platform") == platform and e.get("status") in ACTIVE_STATUSES]
    dated = [(ledger_lib.effective_date(e), e) for e in same_platform]
    dated = [(d, e) for d, e in dated if d is not None]
    dated.sort(key=lambda t: t[0], reverse=True)

    # 检查 1：相邻 3 篇（同场景大类/同服装/同造型任一重复）
    hit = []
    for d, e in dated[:3]:
        for field, label in (("scene_category", "场景大类"), ("outfit", "服装"), ("styling", "造型")):
            if candidate.get(field) and e.get(field) == candidate.get(field):
                hit.append("相邻 3 篇内{}重复：{}（{}，{}）".format(label, e.get(field), e.get("ledger_id"), d.isoformat()))
    findings.extend(hit)
    checks.append("相邻 3 篇：%s" % ("违规 " + "；".join(hit) if hit else "通过"))

    # 检查 2：同一场景大类 14 天内不重复（生效日期孰早口径）
    hit = []
    if candidate.get("scene_category"):
        if candidate["scene_category"] not in categories:
            notes.append("候选场景大类 {!r} 未在 rotation-rules.md 大类表中登记（新大类应先登记）".format(candidate["scene_category"]))
        for d, e in dated:
            if e.get("scene_category") == candidate["scene_category"]:
                delta = abs((cand_date - d).days)
                if delta < 14:
                    hit.append(f"同场景大类 {candidate['scene_category']} 距 {e.get('ledger_id')} "
                               f"仅 {delta} 天（{d.isoformat()}）")
    findings.extend(hit)
    checks.append("14 天同大类：%s" % ("违规 " + "；".join(hit) if hit else "通过"))

    # 检查 3：冷却期（同一 asset_id，按上次使用条目的等级取冷却天数）
    hit = []
    if candidate.get("asset_id"):
        for d, e in dated:
            if e.get("asset_id") == candidate["asset_id"]:
                need = cooldowns.get(e.get("asset_grade"))
                if need is None:
                    notes.append("条目 {} 等级非法，冷却期无法判定".format(e.get("ledger_id")))
                    continue
                elapsed = (cand_date - d).days
                if elapsed < need:
                    hit.append(f"资产 {candidate['asset_id']} 冷却期未满：等级 {e.get('asset_grade')} "
                               f"需 {need} 天，上次使用 {e.get('ledger_id')}（{d.isoformat()}），"
                               f"仅隔 {elapsed} 天")
                break  # dated 已按日期倒序，第一条即最近一次使用
    findings.extend(hit)
    checks.append("冷却期：%s" % ("违规 " + "；".join(hit) if hit else "通过"))

    # 检查 4：S 级月度上限（同平台同月 <=2 次）
    hit = []
    if candidate.get("asset_grade") == "S":
        month_uses = [e for d, e in dated
                      if e.get("asset_grade") == "S"
                      and (d.year, d.month) == (cand_date.year, cand_date.month)]
        if len(month_uses) >= 2:
            hit.append(f"S 级资产当月已用 {len(month_uses)} 次（上限 2），"
                       f"候选为第 {len(month_uses) + 1} 次")
    findings.extend(hit)
    checks.append("S 级月度上限：%s" % ("违规 " + "；".join(hit) if hit else "通过"))

    # 检查 5：白底三禁
    hit = []
    if candidate.get("uses_standard_portrait"):
        hit.append("事故级：白底标准照作内容配图（白底三禁 1，永不作内容配图）")
    if candidate.get("scene_category") == "白底棚拍":
        month_white = [e for d, e in dated
                       if e.get("scene_category") == "白底棚拍"
                       and (d.year, d.month) == (cand_date.year, cand_date.month)]
        if month_white:
            hit.append("白底棚拍原片当月已用作内容配图（{}），每月上限 1 次".format(month_white[0].get("ledger_id")))
        recent = dated[:1]
        if recent and recent[0][1].get("scene_category") == "白底棚拍":
            hit.append("白底棚拍不得连续两篇使用（上一篇 {} 即白底棚拍）".format(recent[0][1].get("ledger_id")))
    findings.extend(hit)
    checks.append("白底三禁：%s" % ("违规 " + "；".join(hit) if hit else "通过"))

    if findings:
        verdict = "违规"
    elif notes:
        verdict = "条件通过"
    else:
        verdict = "通过"
    return {"verdict": verdict, "findings": findings, "checks": checks, "notes": notes}


def run(ledger_path, candidate):
    """完整跑一次预检，返回 (exit_code, report_text)。供 CLI 与 demo/run.py 共用。"""
    rules = load_rotation_rules()
    if rules is None:
        return 3, "规则读取失败：references/rotation-rules.md 场景大类表/冷却期读取不完整，拒绝放行"
    entries, problems, fatal = ledger_lib.load_ledger(ledger_path)
    lines = ["# 轮换预检（真读台账）", f"- 台账：{ledger_path}"]
    if fatal:
        lines.append(f"- 结论：无法判定（降级）—— {fatal}")
        lines.append("- 说明：按 SKILL.md 降级规则标注「台账待补」，本次三项检查未执行，不得视为通过；"
                     "请补台账后重跑，或按实物另行人工判定并留痕。")
        return 2, "\n".join(lines) + "\n"
    invalid_idx = {i for i, e in enumerate(entries) if ledger_lib.validate_entry(e, i)}
    valid = [e for i, e in enumerate(entries) if i not in invalid_idx]
    result = evaluate(valid, candidate, rules, invalid_count=len(entries) - len(valid))
    lines.append("- 候选：{} / {} / {} / 资产 {}（{} 级）".format(candidate.get("platform"), candidate.get("date"),
                    candidate.get("scene_category"), candidate.get("asset_id"),
                    candidate.get("asset_grade")))
    lines.append(f"- 台账条目：共 {len(entries)} 条，合规 {len(valid)} 条")
    for p in problems:
        lines.append(f"- 台账缺陷：{p}")
    lines.append("")
    for c in result["checks"]:
        lines.append(f"- 检查·{c}")
    for n in result["notes"]:
        lines.append(f"- 不确定性：{n}")
    if result["findings"]:
        lines.append("")
        lines.append("## 违规明细")
        for f in result["findings"]:
            lines.append("- " + f)
        lines.append("- 处置建议：换场景大类 / 换服装造型 / 推迟到冷却期满后，并按 SKILL.md Step 1 "
                     "在 prompt 上标注「待场景确认」。")
    lines.append("")
    lines.append("- 结论：{}".format(result["verdict"]))
    code = {"通过": 0, "条件通过": 0, "违规": 1, "无法判定": 2}[result["verdict"]]
    return code, "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="轮换预检（真读台账）")
    ap.add_argument("--ledger", required=True, help="台账文件路径（used-visual-ledger.md 或 .json）")
    ap.add_argument("--candidate", help="候选 JSON 文件路径")
    ap.add_argument("--candidate-json", help="候选 JSON 字符串（与 --candidate 二选一）")
    args = ap.parse_args(argv)
    if args.candidate:
        with open(args.candidate, encoding="utf-8") as f:
            candidate = json.load(f)
    elif args.candidate_json:
        candidate = json.loads(args.candidate_json)
    else:
        print("用法错误：须给 --candidate 或 --candidate-json", file=sys.stderr)
        return 3
    code, report = run(args.ledger, candidate)
    sys.stdout.write(report)
    return code


if __name__ == "__main__":
    sys.exit(main())
