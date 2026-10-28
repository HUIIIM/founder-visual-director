#!/usr/bin/env python3
"""台账解析与字段校验（scripts 共用库）。

台账正式格式见 references/ledger-format.md（v1.0）：
- 台账文件为 markdown，其中唯一的机器可读区是一个 ```json 代码块，
  内容为条目对象数组；也可直接给 .json 文件（数组本体）。
- 字段名沿用 references/rotation-rules.md 的 schema 草案 v0.1，不得另起一套；
  v1.0 仅补结构化参考图字段 references 与预留字段，见 ledger-format.md。

本库只做「读取 + 校验 + 生效日期计算」，不做任何业务判定；
判定在 check_rotation.py / check_face_consistency.py。
校验失败不抛异常：返回 problems 列表，由调用方按降级规则处置
（不得静默丢弃坏条目后给出无保留的「通过」）。
"""
import json
import os
import re
from datetime import date

GRADES = ("S", "A", "B")
STATUSES = ("已发布", "待发", "已退役")
ROLES = ("anchor", "style", "layout", "negative")
DISCLOSURE_METHODS = ("platform_declaration", "c2pa", "caption", "none")

# 条目必填字段（格式 v1.0）；date_published 仅 status=已发布 时必填，单列处理。
REQUIRED_FIELDS = (
    "ledger_id", "platform", "post_no", "date_made", "scene_category",
    "outfit", "styling", "asset_grade", "asset_id", "model_id",
    "status", "ai_generated", "ai_disclosure_method",
)


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def effective_date(entry):
    """生效日期 = 制作/发布孰早（rotation-rules.md 轮换四条 3）。
    date_published 缺失时取 date_made；两者皆不可解析返回 None。"""
    made = _parse_date(entry.get("date_made"))
    published = _parse_date(entry.get("date_published"))
    pool = [d for d in (made, published) if d is not None]
    return min(pool) if pool else None


def extract_entries_text(text):
    """从台账文本提取条目数组。返回 (entries, error)；error 非 None 表示不可解析。"""
    blocks = re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        stripped = text.strip()
        if stripped.startswith("["):
            blocks = [stripped]
        else:
            return None, "未找到 ```json 条目块（台账无机器可读区）"
    for block in blocks:
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return data, None
    return None, "```json 条目块存在但无法解析为条目数组（JSON 语法错误或非数组）"


def load_ledger(path):
    """读取台账文件。返回 (entries, problems, fatal)：
    - fatal 非 None：整本不可读（文件缺失 / 无机器可读区 / JSON 不可解析），entries 为 None；
    - problems：逐条字段缺陷列表（条目仍返回，调用方须按降级规则标注不确定性）。
    """
    if not os.path.exists(path):
        return None, [], "台账文件不存在：" + str(path)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    entries, error = extract_entries_text(text)
    if error:
        return None, [], error
    problems = []
    for i, entry in enumerate(entries):
        problems.extend(validate_entry(entry, i))
    return entries, problems, None


def validate_entry(entry, idx):
    """单条字段校验，返回缺陷字符串列表（空 = 合规）。"""
    tag = f"条目[{idx}]"
    if not isinstance(entry, dict):
        return [tag + " 不是对象"]
    lid = entry.get("ledger_id")
    if isinstance(lid, str) and lid:
        tag = "条目 " + lid
    problems = []
    for field in REQUIRED_FIELDS:
        value = entry.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append(f"{tag} 缺必填字段 {field}")
    if _parse_date(entry.get("date_made")) is None and entry.get("date_made") is not None:
        problems.append("{} 的 date_made 不可解析：{!r}".format(tag, entry.get("date_made")))
    status = entry.get("status")
    if status is not None and status not in STATUSES:
        problems.append("{} 的 status 非法：{!r}（应为 {}）".format(tag, status, "/".join(STATUSES)))
    if status == "已发布" and entry.get("date_published") is None:
        problems.append(f"{tag} 状态为已发布但缺 date_published")
    if entry.get("date_published") is not None and _parse_date(entry.get("date_published")) is None:
        problems.append("{} 的 date_published 不可解析：{!r}".format(tag, entry.get("date_published")))
    grade = entry.get("asset_grade")
    if grade is not None and grade not in GRADES:
        problems.append(f"{tag} 的 asset_grade 非法：{grade!r}（应为 S/A/B）")
    if entry.get("ai_generated") is True:
        if not entry.get("ai_disclosure_text"):
            problems.append(f"{tag} ai_generated=true 但缺 ai_disclosure_text")
        if not entry.get("ai_disclosure_basis"):
            problems.append(f"{tag} ai_generated=true 但缺 ai_disclosure_basis")
    method = entry.get("ai_disclosure_method")
    if method is not None and method not in DISCLOSURE_METHODS:
        problems.append(f"{tag} 的 ai_disclosure_method 非法：{method!r}")
    refs = entry.get("references")
    if refs is not None:
        if not isinstance(refs, list):
            problems.append(f"{tag} 的 references 不是数组")
        else:
            for j, ref in enumerate(refs):
                if not isinstance(ref, dict) or not ref.get("file") or not ref.get("role"):
                    problems.append(f"{tag} 的 references[{j}] 缺 file/role")
                elif ref["role"] not in ROLES:
                    problems.append(f"{tag} 的 references[{j}] 角色非法：{ref['role']!r}")
    return problems


def validate_candidate(candidate):
    """候选（本次待检交付）字段校验，返回缺陷列表。
    候选字段见 ledger-format.md「候选字段」节。"""
    problems = []
    for field in ("platform", "date", "scene_category", "outfit", "styling",
                  "asset_id", "asset_grade"):
        value = candidate.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append("候选缺字段 " + field)
    if candidate.get("date") is not None and _parse_date(candidate.get("date")) is None:
        problems.append("候选 date 不可解析：{!r}".format(candidate.get("date")))
    grade = candidate.get("asset_grade")
    if grade is not None and grade not in GRADES:
        problems.append(f"候选 asset_grade 非法：{grade!r}")
    return problems
