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
- 台账条目有字段缺陷 -> 每项检查仍用具备该项所需字段的全部条目判定（缺无关字段不剔除），
  缺本项字段的条目逐条标注；有违规即违规，否则结论上限为「条件通过」；
- 候选字段不全 -> 受影响的检查标注「无法判定」，结论上限为「条件通过」；
- 候选 platform 缺失或不在平台枚举内（ledger-format.md）-> 「无法判定」，不做静默放行；
- 台账有条目但没有一条具备平台与生效日期 -> 「无法判定」。
退出码：0 通过 / 1 违规 / 2 无法判定 / 3 规则读取失败或用法错误 / 4 条件通过 / 5 内部错误。

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


def _shown(value):
    """报告里展示调用方提供的值：单行化并加「」，使其无法伪造「- 结论：」等报告行（#23 第 2 项）。"""
    if value is None:
        return "（缺）"
    return "「" + re.sub(r"\s+", " ", str(value)).strip() + "」"


def _check_line(name, hits, unknown):
    if hits:
        return f"{name}：违规 " + "；".join(hits)
    if unknown:
        return f"{name}：无法判定（" + "；".join(unknown) + "）"
    return f"{name}：通过"


def evaluate(entries, candidate, rules, defect_count=0):
    """真读判定。返回 dict：verdict（通过/条件通过/违规/无法判定）、findings、
    checks（逐项状态行）、notes（不确定性标注）。

    每项检查用「具备该项所需字段」的全部条目判定；某条目缺的是别的字段（如 model_id、
    AI 声明），不会把它从轮换比对里剔除（独立评估 #16 P1-2）。
    """
    categories, cooldowns = rules
    findings, checks, notes = [], [], []
    cand_problems = ledger_lib.validate_candidate(candidate)
    if defect_count:
        notes.append(f"台账有 {defect_count} 处字段缺陷（见上方台账缺陷），结论带不确定性")
    if cand_problems:
        notes.append("候选字段不全或非法：" + "；".join(cand_problems))
    if not isinstance(candidate, dict):
        checks.append("全部检查：无法判定（候选不是 JSON 对象）")
        return {"verdict": "无法判定", "findings": findings, "checks": checks, "notes": notes}

    cand_date = _d(candidate.get("date"))
    platform = ledger_lib.normalize_platform(candidate.get("platform"))
    if cand_date is None or platform is None:
        why = "候选 date 缺失或不可解析" if cand_date is None else "候选 platform 缺失或不在平台枚举内"
        checks.append(f"全部检查：无法判定（{why}）")
        return {"verdict": "无法判定", "findings": findings, "checks": checks, "notes": notes}

    # 基础可用条目：对象、状态为已发布/待发、平台可归一、有可解析的生效日期
    usable_any, unusable = [], 0
    for e in entries:
        if not isinstance(e, dict):
            unusable += 1
            continue
        d = ledger_lib.effective_date(e)
        p = ledger_lib.normalize_platform(e.get("platform"))
        if e.get("status") not in ACTIVE_STATUSES:
            continue  # 已退役条目不参与轮换比对（不是缺陷）
        if d is None or p is None:
            unusable += 1
            continue
        usable_any.append((d, p, e))
    if unusable:
        notes.append(f"{unusable} 条在用条目缺平台/生效日期或不是对象，未参与任何检查")
    if entries and not usable_any:
        checks.append("全部检查：无法判定（台账有条目，但没有一条具备平台与生效日期）")
        return {"verdict": "无法判定", "findings": findings, "checks": checks, "notes": notes}
    dated = sorted(((d, e) for d, p, e in usable_any if p == platform), key=lambda t: t[0], reverse=True)
    if usable_any and not dated:
        notes.append(f"台账中没有 {platform} 平台的在用条目（若为该平台首发，须人工确认后再放行）")

    def missing_in(rows, field):
        return [e.get("ledger_id") or "?" for _, e in rows if not e.get(field)]

    # 检查 1：相邻 3 篇（同场景大类/同服装/同造型任一重复）
    hit, unknown = [], []
    for field, label in (("scene_category", "场景大类"), ("outfit", "服装"), ("styling", "造型")):
        if not candidate.get(field):
            unknown.append(f"候选缺{label}")
            continue
        gaps = missing_in(dated[:3], field)
        if gaps:
            unknown.append(f"条目 {','.join(gaps)} 缺{label}")
        for d, e in dated[:3]:
            if ledger_lib.normalize_key(e.get(field)) == ledger_lib.normalize_key(candidate.get(field)):
                hit.append(f"相邻 3 篇内{label}重复：{e.get(field)}（{e.get('ledger_id')}，{d.isoformat()}）")
    findings.extend(hit)
    checks.append(_check_line("相邻 3 篇", hit, unknown))

    # 检查 2：同一场景大类 14 天内不重复（生效日期孰早口径）
    hit, unknown = [], []
    cat = candidate.get("scene_category")
    if not cat:
        unknown.append("候选缺场景大类")
    else:
        if cat not in categories:
            notes.append(f"候选场景大类 {cat!r} 未在 rotation-rules.md 大类表中登记（新大类应先登记）")
        gaps = [e.get("ledger_id") or "?" for d, e in dated if abs((cand_date - d).days) < 14 and not e.get("scene_category")]
        if gaps:
            unknown.append(f"14 天内条目 {','.join(gaps)} 缺场景大类")
        for d, e in dated:
            delta = abs((cand_date - d).days)
            if ledger_lib.normalize_key(e.get("scene_category")) == ledger_lib.normalize_key(cat) and delta < 14:
                hit.append(f"同场景大类 {cat} 距 {e.get('ledger_id')} 仅 {delta} 天（{d.isoformat()}）")
    findings.extend(hit)
    checks.append(_check_line("14 天同大类", hit, unknown))

    # 检查 3：冷却期（同一 asset_id，按上次使用条目的等级取冷却天数）
    hit, unknown = [], []
    asset = candidate.get("asset_id")
    if not asset:
        unknown.append("候选缺 asset_id")
    else:
        # 冷却期不分平台（rotation-rules.md「同一 ID 在冷却期内不得重复使用」；#41：换平台复用曾绕过）
        dated_all = sorted(((d, e) for d, p, e in usable_any), key=lambda t: t[0], reverse=True)
        gaps = missing_in(dated_all, "asset_id")
        if gaps:
            unknown.append(f"条目 {','.join(gaps)} 缺 asset_id")
        for d, e in dated_all:
            if ledger_lib.normalize_asset_id(e.get("asset_id")) == ledger_lib.normalize_asset_id(asset):
                need = cooldowns.get(e.get("asset_grade"))
                if need is None:
                    unknown.append(f"条目 {e.get('ledger_id')} 等级缺失或非法，冷却天数无从确定")
                    break
                elapsed = (cand_date - d).days
                if elapsed < need:
                    hit.append(f"资产 {asset} 冷却期未满：等级 {e.get('asset_grade')} 需 {need} 天，"
                               f"上次使用 {e.get('ledger_id')}（{d.isoformat()}），仅隔 {elapsed} 天")
                break  # dated 已按日期倒序，第一条即最近一次使用
    findings.extend(hit)
    checks.append(_check_line("冷却期", hit, unknown))

    # 检查 4：S 级月度上限（同平台同月 <=2 次）
    hit, unknown = [], []
    grade = candidate.get("asset_grade")
    if not grade:
        unknown.append("候选缺 asset_grade")
    elif grade == "S":
        same_month = [(d, e) for d, e in dated if (d.year, d.month) == (cand_date.year, cand_date.month)]
        gaps = missing_in(same_month, "asset_grade")
        if gaps:
            unknown.append(f"当月条目 {','.join(gaps)} 缺 asset_grade")
        month_uses = [e for _, e in same_month if e.get("asset_grade") == "S"]
        if len(month_uses) >= 2:
            hit.append(f"S 级资产当月已用 {len(month_uses)} 次（上限 2），候选为第 {len(month_uses) + 1} 次")
    findings.extend(hit)
    checks.append(_check_line("S 级月度上限", hit, unknown))

    # 检查 5：白底三禁
    hit, unknown = [], []
    if candidate.get("uses_standard_portrait") is True:
        hit.append("事故级：白底标准照作内容配图（白底三禁 1，永不作内容配图）")
    elif not isinstance(candidate.get("uses_standard_portrait", False), bool):
        unknown.append("uses_standard_portrait 不是布尔值")
    if cat == "白底棚拍":
        month_white = [e for d, e in dated
                       if e.get("scene_category") == "白底棚拍"
                       and (d.year, d.month) == (cand_date.year, cand_date.month)]
        if month_white:
            hit.append(f"白底棚拍原片当月已用作内容配图（{month_white[0].get('ledger_id')}），每月上限 1 次")
        if dated and dated[0][1].get("scene_category") == "白底棚拍":
            hit.append(f"白底棚拍不得连续两篇使用（上一篇 {dated[0][1].get('ledger_id')} 即白底棚拍）")
    elif not cat:
        unknown.append("候选缺场景大类，白底棚拍限额无法判定")
    findings.extend(hit)
    checks.append(_check_line("白底三禁", hit, unknown))

    # 检查 6：模特资产授权（docs/PRIVACY.md：授权过期或用途变更即停用）。
    # 候选给出 model_id 时，查全台账（不分平台、状态）里同一 model_id 的授权登记：
    # 任一条记为 expired / revoked 即违规；候选与台账都没有授权状态 = 无法判定（#32 P2-5）。
    hit, unknown = [], []
    consent = candidate.get("model_consent_status")
    model_id = ledger_lib.normalize_model_id(candidate.get("model_id"))
    if consent in ("expired", "revoked"):
        hit.append(f"模特资产授权状态为 {consent}，不得用于新内容")
    if not model_id:
        unknown.append("候选缺 model_id（不用模特资产时填 none）")
    elif model_id == "none":
        # "none" is the candidate's own claim; the ledger may know better (#37 residual).
        asset = ledger_lib.normalize_asset_id(candidate.get("asset_id"))
        modeled = [
            e
            for e in entries
            if isinstance(e, dict)
            and asset
            and ledger_lib.normalize_asset_id(e.get("asset_id")) == asset
            and ledger_lib.normalize_model_id(e.get("model_id")) not in (None, "none")
        ]
        if modeled:
            unknown.append(
                f"候选填 model_id none，但台账里同一 asset_id {_shown(asset)} 登记过模特 "
                f"{_shown(modeled[0].get('model_id'))}（条目 {_shown(modeled[0].get('ledger_id'))}）"
            )
    else:
        same_model = [
            e for e in entries if isinstance(e, dict) and ledger_lib.normalize_model_id(e.get("model_id")) == model_id
        ]
        for e in same_model:
            if e.get("model_consent_status") in ("expired", "revoked"):
                hit.append(
                    f"台账登记 model_id {_shown(model_id)} 授权为 {e.get('model_consent_status')}"
                    f"（条目 {_shown(e.get('ledger_id'))}），不得用于新内容"
                )
        recorded = consent or any(e.get("model_consent_status") for e in same_model)
        if not recorded and not hit:
            unknown.append(f"model_id {_shown(model_id)} 在候选与台账中都没有授权状态")
    # 台账里任一条目的 model_id / 授权状态本身不合法，就无法确认它记的不是这个模特的撤销：
    # 本行判「无法判定」，不印「通过」（#37 第 6 轮）。
    if not hit:
        for e in entries:
            if not isinstance(e, dict):
                continue
            mid, cst = e.get("model_id"), e.get("model_consent_status")
            bad_id = mid is not None and not (
                isinstance(mid, str) and ledger_lib.MODEL_ID_RE.match(ledger_lib.normalize_model_id(mid) or "")
            )
            bad_status = cst is not None and cst not in ledger_lib.MODEL_CONSENT_STATUSES
            if bad_id or bad_status:
                unknown.append(f"台账条目 {_shown(e.get('ledger_id'))} 的 model_id 或授权状态不合法，无法确认其授权记录")
                break
    findings.extend(hit)
    checks.append(_check_line("模特资产授权", hit, unknown))

    # 检查 7：已发布图永久退役（SKILL.md § 红线：凡已发布用过的图永久退役，含跨平台复用）。
    # 判定对象是产物图本身（image_sha256，ledger-format.md「一图一记录」字段），不是可在冷却期后
    # 复用的素材 asset_id：任一已发布/已退役条目登记了同一哈希即违规，不分平台、不看日期（#41）。
    hit, unknown = [], []
    digest = ledger_lib.normalize_key(candidate.get("image_sha256"))
    if not digest:
        unknown.append("候选缺 image_sha256，已发布图是否被复用无法机判（须人工确认）")
    else:
        for e in entries:
            if not isinstance(e, dict) or e.get("status") not in ("已发布", "已退役"):
                continue
            if ledger_lib.normalize_key(e.get("image_sha256")) == digest:
                hit.append(
                    f"该图已发布过（条目 {_shown(e.get('ledger_id'))}，{_shown(e.get('platform'))}），"
                    "已发布图永久退役，不得二次使用"
                )
    findings.extend(hit)
    checks.append(_check_line("已发布图永久退役", hit, unknown))

    if findings:
        verdict = "违规"
    elif notes or any("：无法判定" in c for c in checks):
        verdict = "条件通过"
    else:
        verdict = "通过"
    return {"verdict": verdict, "findings": findings, "checks": checks, "notes": notes}


EXIT_CODES = {"通过": 0, "违规": 1, "无法判定": 2, "条件通过": 4}


def run(ledger_path, candidate):
    """完整跑一次预检，返回 (exit_code, report_text)。供 CLI 与 demo/run.py 共用。
    退出码：0 通过 / 1 违规 / 2 无法判定 / 3 规则读取失败 / 4 条件通过。"""
    rules = load_rotation_rules()
    if rules is None:
        return 3, "规则读取失败：references/rotation-rules.md 场景大类表/冷却期读取不完整，拒绝放行\n"
    entries, problems, fatal = ledger_lib.load_ledger(ledger_path)
    lines = ["# 轮换预检（真读台账）", f"- 台账：{ledger_path}"]
    if fatal:
        lines.append(f"- 结论：无法判定（降级）—— {fatal}")
        lines.append("- 说明：按 SKILL.md 降级规则标注「台账待补」，本次检查未执行，不得视为通过；"
                     "请补台账后重跑，或按实物另行人工判定并留痕。")
        return EXIT_CODES["无法判定"], "\n".join(lines) + "\n"
    result = evaluate(entries, candidate, rules, defect_count=len(problems))
    c = candidate if isinstance(candidate, dict) else {}
    lines.append("- 候选：{} / {} / {} / 资产 {}（{} 级）".format(
        *(_shown(c.get(k)) for k in ("platform", "date", "scene_category", "asset_id", "asset_grade"))))
    lines.append(f"- 台账条目：共 {len(entries)} 条，字段缺陷 {len(problems)} 处")
    for p in problems:
        lines.append("- 台账缺陷：" + re.sub(r"\s+", " ", p))
    lines.append("")
    for line in result["checks"]:
        lines.append("- 检查·" + re.sub(r"\s+", " ", line))
    for n in result["notes"]:
        lines.append("- 不确定性：" + re.sub(r"\s+", " ", n))
    if result["findings"]:
        lines.append("")
        lines.append("## 违规明细")
        for f in result["findings"]:
            lines.append("- " + re.sub(r"\s+", " ", f))
        lines.append("- 处置建议：换场景大类 / 换服装造型 / 推迟到冷却期满后，并按 SKILL.md Step 1 "
                     "在 prompt 上标注「待场景确认」。")
    lines.append("")
    lines.append("- 结论：{}".format(result["verdict"]))
    return EXIT_CODES[result["verdict"]], "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="轮换预检（真读台账）")
    ap.add_argument("--ledger", required=True, help="台账文件路径（used-visual-ledger.md 或 .json）")
    ap.add_argument("--candidate", help="候选 JSON 文件路径")
    ap.add_argument("--candidate-json", help="候选 JSON 字符串（与 --candidate 二选一）")
    args = ap.parse_args(argv)
    try:
        if args.candidate:
            with open(args.candidate, encoding="utf-8") as f:
                candidate = json.load(f)
        elif args.candidate_json:
            candidate = json.loads(args.candidate_json)
        else:
            print("用法错误：须给 --candidate 或 --candidate-json", file=sys.stderr)
            return 3
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"用法错误：候选不可读或不是合法 JSON（{exc}）", file=sys.stderr)
        return 3
    code, report = run(args.ledger, candidate)
    sys.stdout.write(report)
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 -- 内部错误不得冒充「违规」(1) 或任何判定结果
        print(f"内部错误：{exc.__class__.__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
