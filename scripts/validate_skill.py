#!/usr/bin/env python3
"""Validate this skill package. Zero dependencies.

Checks:
  1. SKILL.md frontmatter follows the Agent Skills spec (https://agentskills.io/specification):
     only the six allowed top-level fields; name and description constraints; metadata is a
     string-to-string map; the name matches the skill directory.
  2. SKILL.md stays within the spec's size guidance (500 lines).
  3. Every repo-relative path SKILL.md mentions in backticks (references/, scripts/, demo/, evals/) exists.
  4. The rules SKILL.md quotes inline (mandatory phrases, fixed negative band) are identical to the
     single source in references/prompt-standards.md, so the two cannot drift apart.
  5. evals/evals.json is well formed (unique ids, prompts, assertions, existing files).

Usage: python3 scripts/validate_skill.py [SKILL_DIR]
Exit code: 0 valid, 1 invalid.
"""
import json
import os
import re
import sys

ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME, MAX_DESCRIPTION, MAX_COMPATIBILITY, MAX_LINES = 64, 1024, 500, 500


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Parse the YAML subset SKILL.md uses: `key: value` lines and one nested map level.

    Returns (fields, errors). Anything outside that subset is reported, not guessed at.
    """
    errors = []
    if not text.startswith("---\n"):
        return {}, ["SKILL.md must start with a '---' frontmatter line"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, ["frontmatter has no closing '---' line"]
    fields, current = {}, None
    for n, line in enumerate(text[4:end].split("\n"), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        nested = line.startswith((" ", "\t"))
        m = re.match(r"^\s*([A-Za-z0-9_-]+):(?:\s+(.*))?$", line)
        if not m:
            errors.append("frontmatter line %d is not 'key: value'" % n)
            continue
        key, value = m.group(1), m.group(2)
        if nested:
            if current is None or not isinstance(fields.get(current), dict):
                errors.append("frontmatter line %d is indented but has no parent map" % n)
                continue
            fields[current][key] = _unquote(value or "")
        elif value is None or value.strip() == "":
            fields[key], current = {}, key
        else:
            fields[key], current = _unquote(value), None
    return fields, errors


def check_frontmatter(fields, skill_dir):
    errors = []
    extra = sorted(set(fields) - ALLOWED_FIELDS)
    if extra:
        errors.append("unexpected frontmatter fields %s; allowed: %s" % (extra, sorted(ALLOWED_FIELDS)))
    name = fields.get("name")
    if not isinstance(name, str) or not name:
        errors.append("'name' is required")
    else:
        if len(name) > MAX_NAME or not NAME_RE.match(name):
            errors.append("'name' must be 1-%d lowercase letters, digits and single hyphens" % MAX_NAME)
        dirname = os.path.basename(os.path.abspath(skill_dir))
        if dirname != name:
            errors.append("'name' (%s) must match the skill directory name (%s)" % (name, dirname))
    desc = fields.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errors.append("'description' is required")
    elif len(desc) > MAX_DESCRIPTION:
        errors.append("'description' is %d characters; max %d" % (len(desc), MAX_DESCRIPTION))
    comp = fields.get("compatibility")
    if comp is not None and (not isinstance(comp, str) or not 1 <= len(comp) <= MAX_COMPATIBILITY):
        errors.append("'compatibility' must be 1-%d characters" % MAX_COMPATIBILITY)
    meta = fields.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("'metadata' must be a map of string keys to string values")
    for key in ("license", "allowed-tools"):
        if key in fields and not isinstance(fields[key], str):
            errors.append("'%s' must be a string" % key)
    return errors


def check_paths(body, skill_dir):
    errors = []
    for path in sorted(set(re.findall(r"`((?:references|scripts|demo|evals|docs)/[^`\s]+)`", body))):
        if not os.path.exists(os.path.join(skill_dir, path)):
            errors.append("SKILL.md mentions %s, which does not exist" % path)
    return errors


def fenced_block_after(text, heading):
    """Return the first fenced code block after the line that starts with `heading`."""
    i = text.find(heading)
    if i < 0:
        return None
    m = re.search(r"```[^\n]*\n(.*?)```", text[i:], re.S)
    return m.group(1) if m else None


def _norm_items(text):
    return [t.strip() for t in re.split(r"[,\n]", text) if t.strip()]


def check_rule_sync(skill_text, skill_dir):
    """SKILL.md quotes some rules inline; they must equal the single source in prompt-standards.md."""
    errors = []
    path = os.path.join(skill_dir, "references", "prompt-standards.md")
    try:
        with open(path, encoding="utf-8") as f:
            std = f.read()
    except OSError as e:
        return ["cannot read %s: %s" % (path, e)]
    phrases = fenced_block_after(std, "## 强制短语")
    negative = fenced_block_after(std, "## 固定否定词带")
    if phrases is None or negative is None:
        return ["prompt-standards.md is missing the 强制短语 or 固定否定词带 block"]
    m = re.search(r"强制短语（正向必带）：\n(.*?)\n\n", skill_text, re.S)
    inline_phrases = re.findall(r"`([^`]+)`", m.group(1)) if m else []
    source_phrases = [p.strip() for p in phrases.splitlines() if p.strip()]
    if inline_phrases != source_phrases:
        errors.append("SKILL.md mandatory phrases %s differ from prompt-standards.md %s"
                      % (inline_phrases, source_phrases))
    m = re.search(r"固定否定词带（每次必带）：\n`([^`]+)`", skill_text)
    inline_negative = _norm_items(m.group(1)) if m else []
    if inline_negative != _norm_items(negative):
        errors.append("SKILL.md fixed negative band differs from prompt-standards.md")
    return errors


def check_evals(skill_dir):
    path = os.path.join(skill_dir, "evals", "evals.json")
    if not os.path.exists(path):
        return ["evals/evals.json is missing"]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as e:
        return ["evals/evals.json is not valid JSON: %s" % e]
    errors = []
    if not isinstance(data, dict) or not isinstance(data.get("evals"), list) or not data["evals"]:
        return ["evals/evals.json must be an object with a non-empty 'evals' list"]
    seen = set()
    for i, case in enumerate(data["evals"]):
        where = "evals[%d]" % i
        if not isinstance(case, dict):
            errors.append("%s is not an object" % where)
            continue
        cid = case.get("id")
        if cid in seen or not isinstance(cid, int):
            errors.append("%s id %r is missing, not an integer or duplicated" % (where, cid))
        seen.add(cid)
        for key in ("prompt", "expected_output"):
            if not isinstance(case.get(key), str) or not case[key].strip():
                errors.append("%s needs a non-empty '%s'" % (where, key))
        asserts = case.get("assertions")
        if not isinstance(asserts, list) or not asserts or not all(isinstance(a, str) and a for a in asserts):
            errors.append("%s needs a non-empty list of string 'assertions'" % where)
        for fpath in case.get("files", []):
            if not os.path.exists(os.path.join(skill_dir, fpath)):
                errors.append("%s lists missing file %s" % (where, fpath))
    return errors


def validate(skill_dir):
    path = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        return ["cannot read %s: %s" % (path, e)]
    fields, errors = parse_frontmatter(text)
    errors += check_frontmatter(fields, skill_dir)
    lines = text.count("\n") + 1
    if lines > MAX_LINES:
        errors.append("SKILL.md has %d lines; keep it under %d" % (lines, MAX_LINES))
    errors += check_paths(text, skill_dir)
    errors += check_rule_sync(text, skill_dir)
    errors += check_evals(skill_dir)
    return errors


def main(argv):
    skill_dir = argv[1] if len(argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = validate(skill_dir)
    for e in errors:
        print("FAIL: " + e)
    if errors:
        return 1
    print("PASS: skill package valid (%s)" % os.path.abspath(skill_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
