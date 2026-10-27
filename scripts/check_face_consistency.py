#!/usr/bin/env python3
"""面部一致性可执行校验：SKILL.md Reference Roles + prompt 模板铁律的机器实现。

身份一致性只靠 anchor 参考图（模板铁律 1），此前只存在于散文；本脚本对台账
（references/ledger-format.md v1.0）中的生成登记做机读核验，逐条检查：

1. 结构化参考图登记存在（references 数组非空）；
2. anchor 齐备且唯一：每条登记恰好 1 张 role=anchor 的参考图（缺失/多张均为违规）；
3. 一张图不许兼两角：同一文件在同一条目内不得登记两个角色；
4. 每张参考图登记了 sha256（64 位十六进制）；
5. 参考图文件存在（路径相对台账文件所在目录解析，或绝对路径）；
6. 文件实际 SHA-256 与登记值一致（台账与实物对不上 -> 违规）；
7. reference_roles 摘要串（若填）中出现的角色集合与结构化登记一致
   （摘要串无可识别角色时标注不确定性，不判违规）。

预留接口（一图一记录候选，本轮不实现其本体）：条目可带 output_file / image_sha256，
若存在则按同一方式校验产物文件存在性与哈希；不存在时仅提示「未启用」。
授权/版本面（model_id 停用等）不在本脚本范围，登记字段校验由 ledger_lib 承担。

退出码：0 通过 / 1 违规 / 2 台账不可读（降级，无法判定）。
用法：python3 scripts/check_face_consistency.py <台账.md|.json> [--all]
（默认只查 已发布/待发 条目；--all 连同已退役条目一并查。）
"""
import argparse, hashlib, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger_lib

SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_entry(entry, base_dir):
    """返回 (violations, notes)。"""
    violations, notes = [], []
    if not isinstance(entry, dict):
        return ["台账中存在非对象条目（格式违规，见 ledger_lib 校验）"], []
    tag = "条目 %s" % (entry.get("ledger_id") or "?")
    refs = entry.get("references")
    if not isinstance(refs, list) or not refs:
        violations.append("%s 未登记结构化参考图（references 缺失或为空），"
                          "anchor 身份锚无从核验" % tag)
        refs = []
    anchors = [r for r in refs if isinstance(r, dict) and r.get("role") == "anchor"]
    if refs and len(anchors) != 1:
        violations.append("%s anchor 参考图应恰好 1 张，实登记 %d 张" % (tag, len(anchors)))
    seen = {}
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        f, role = ref.get("file"), ref.get("role")
        if f in seen and seen[f] != role:
            violations.append("%s 参考图 %s 兼任两角（%s / %s），违反 Reference Roles"
                              % (tag, f, seen[f], role))
        seen[f] = role
        digest = ref.get("sha256")
        if not digest or not SHA_RE.match(str(digest)):
            violations.append("%s 参考图 %s（%s）未登记合法 sha256" % (tag, f, role))
            continue
        path = str(f) if os.path.isabs(str(f)) else os.path.join(base_dir, str(f))
        if not os.path.exists(path):
            violations.append("%s 参考图文件不存在：%s（解析为 %s）" % (tag, f, path))
            continue
        actual = sha256_of(path)
        if actual.lower() != str(digest).lower():
            violations.append("%s 参考图 %s 哈希不符：登记 %s… 实际 %s…（台账与实物对不上）"
                              % (tag, f, str(digest)[:12], actual[:12]))
    summary = entry.get("reference_roles")
    if isinstance(summary, str) and summary.strip() and refs:
        found = {r for r in ledger_lib.ROLES if r in summary}
        structured = {r.get("role") for r in refs if isinstance(r, dict)}
        if found and found != structured:
            violations.append("%s reference_roles 摘要角色 %s 与结构化登记 %s 不一致"
                              % (tag, sorted(found), sorted(structured)))
        elif not found:
            notes.append("%s reference_roles 摘要串无可识别角色，未做一致性比对" % tag)
    # 预留接口：一图一记录（候选，本轮只校验已登记的，不强制）
    if entry.get("output_file") or entry.get("image_sha256"):
        out, digest = entry.get("output_file"), entry.get("image_sha256")
        if not out or not digest or not SHA_RE.match(str(digest or "")):
            violations.append("%s 已启用一图一记录字段但 output_file/image_sha256 不完整" % tag)
        else:
            path = str(out) if os.path.isabs(str(out)) else os.path.join(base_dir, str(out))
            if not os.path.exists(path):
                violations.append("%s 产物文件不存在：%s" % (tag, out))
            elif sha256_of(path).lower() != str(digest).lower():
                violations.append("%s 产物 %s 哈希与 image_sha256 登记不符" % (tag, out))
    else:
        notes.append("%s 一图一记录：未启用（output_file/image_sha256 接口预留）" % tag)
    return violations, notes


def main(argv=None):
    ap = argparse.ArgumentParser(description="面部一致性校验（anchor 参考图机读核验）")
    ap.add_argument("ledger", help="台账文件路径")
    ap.add_argument("--all", action="store_true", help="包含已退役条目")
    args = ap.parse_args(argv)
    entries, problems, fatal = ledger_lib.load_ledger(args.ledger)
    if fatal:
        print("面部一致性校验：无法判定（降级）—— %s" % fatal)
        return 2
    base_dir = os.path.dirname(os.path.abspath(args.ledger))
    targets = [e for e in entries
               if args.all or e.get("status") in ("已发布", "待发")]
    all_violations, all_notes = [], []
    for p in problems:
        all_notes.append("台账字段缺陷（ledger_lib）：%s" % p)
    for entry in targets:
        v, n = check_entry(entry, base_dir)
        all_violations.extend(v)
        all_notes.extend(n)
    print("面部一致性校验：台账 %s，受检条目 %d 条" % (args.ledger, len(targets)))
    for n in all_notes:
        print("- 注：%s" % n)
    if all_violations:
        print("违规 %d 条：" % len(all_violations))
        for v in all_violations:
            print("- " + v)
        print("结论：违规（身份一致性只靠 anchor 参考图，登记不全/哈希不符即不得放行）")
        return 1
    print("结论：通过（anchor 齐备、参考图存在且哈希与登记一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
