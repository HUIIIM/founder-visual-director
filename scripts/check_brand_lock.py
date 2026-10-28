#!/usr/bin/env python3
"""品牌锁可执行校验：SKILL.md「Brand Lock」章的机器实现。

品牌锁源 = references/vertciti-brand-bundle.json（DTCG 格式），运行时直读：
- 允许色值 = bundle 内全部 $type=color 的 $value；
- 允许字体 = bundle 内全部 $type=fontFamily 的 $value（另加 CSS 通用族关键字，
  bundle 自身的 fallback 声明即含 system-ui / sans-serif）；
- 字标 = bundle wordmark 的 $value（全小写 vertciti）；
- 偏离字体观察名单 = bundle 元数据中被替换/待替换的旧字体名（replaces / prod-status），
  它们出现在交付物中即为品牌锁偏离。

检查对象（prompt / 交付物文本文件，可多个）：
1. 手写色值：#RGB / #RRGGBB 与 rgb()/rgba() 字面量，不在允许色值集内 -> 违规逐条列出；
2. 字体：font-family 声明中的非通用族不在允许字体集内，或观察名单字体在文本任意位置出现 -> 违规；
3. 字标：vertciti 的大小写变体（Vertciti / VERTCITI / VertCiti 等）或 vert-citi / vert citi 写法 -> 违规。
退出码：0 通过 / 1 违规 / 2 bundle 读取失败或用法错误。

用法：python3 scripts/check_brand_lock.py <文本文件> [更多文件...] [--bundle <bundle.json>]
"""
import argparse, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BUNDLE = os.path.join(REPO, "references", "vertciti-brand-bundle.json")
GENERIC_FAMILIES = {"sans-serif", "serif", "monospace", "system-ui", "cursive",
                    "fantasy", "emoji", "math", "fangsong", "inherit", "initial"}


def load_bundle(path):
    """直读 brand bundle，返回 (colors, fonts, wordmark, watchlist)；失败返回 None。"""
    try:
        bundle = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    colors, fonts, watchlist = set(), set(), set()

    def walk(node):
        if isinstance(node, dict):
            t, v = node.get("$type"), node.get("$value")
            if t == "color" and isinstance(v, str):
                colors.add(normalize_hex(v))
            elif t == "fontFamily" and isinstance(v, str):
                fonts.add(v.strip())
            ext = node.get("$extensions", {})
            if isinstance(ext, dict):
                for sub in ext.values():
                    if isinstance(sub, dict):
                        for key in ("replaces", "prod-status"):
                            raw = sub.get(key)
                            if isinstance(raw, str) and raw:
                                name = re.split(r"[（(]", raw)[0].strip()
                                name = re.sub(r"\s+(Regular|Bold|Light|Medium|Thin|Black|"
                                              r"Heavy|SemiBold|ExtraBold|Italic)$", "", name)
                                if name and name not in fonts:
                                    watchlist.add(name)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(bundle)
    wordmark = None
    wm = bundle.get("wordmark", {})
    if isinstance(wm, dict) and isinstance(wm.get("$value"), str):
        wordmark = wm["$value"]
    if not colors or not fonts or not wordmark:
        return None
    return colors, fonts, wordmark, watchlist


def normalize_hex(value):
    v = value.strip().lstrip("#")
    if len(v) == 3:
        v = "".join(ch * 2 for ch in v)
    return "#" + v.upper()


def rgb_to_hex(r, g, b):
    return "#%02X%02X%02X" % (int(r), int(g), int(b))


def check_file(path, colors, fonts, wordmark, watchlist):
    """返回违规字符串列表（每条含 文件:行 与命中内容）。"""
    violations = []
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError as exc:
        return ["%s：文件不可读（%s）" % (path, exc)]
    for lineno, line in enumerate(lines, 1):
        where = "%s:%d" % (path, lineno)
        # 1. 手写色值（hex）
        for m in re.finditer(r"#[0-9A-Fa-f]{6}\b|#[0-9A-Fa-f]{3}\b", line):
            value = normalize_hex(m.group(0))
            if value not in colors:
                violations.append("%s 手写色值 %s 不在品牌锁色板内（bundle 允许 %d 个色值）"
                                  % (where, m.group(0), len(colors)))
        # 1b. 手写色值（rgb/rgba）
        for m in re.finditer(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", line):
            value = rgb_to_hex(m.group(1), m.group(2), m.group(3))
            if value not in colors:
                violations.append("%s 手写色值 %s（=%s）不在品牌锁色板内"
                                  % (where, m.group(0) + ")", value))
        # 2a. font-family 声明
        for m in re.finditer(r"font-family\s*:\s*([^;}{]+)", line, re.I):
            for fam in m.group(1).split(","):
                name = fam.strip().strip("'\"")
                if not name or name.lower() in GENERIC_FAMILIES:
                    continue
                if name not in fonts:
                    violations.append("%s 字体 %r 不在品牌锁字体集内（允许：%s）"
                                      % (where, name, " / ".join(sorted(fonts))))
        # 2b. 偏离字体观察名单（任意位置出现即偏离，如已淘汰的旧字体名）
        for name in sorted(watchlist):
            if name and name in line:
                violations.append("%s 出现已淘汰/待替换字体 %r（品牌锁偏离）" % (where, name))
        # 3. 字标写法
        for m in re.finditer(r"(?i)vertciti", line):
            if m.group(0) != wordmark:
                violations.append("%s 字标写法 %r 偏离品牌锁（应为全小写 %r）"
                                  % (where, m.group(0), wordmark))
        if re.search(r"(?i)vert[-\s]citi", line):
            violations.append("%s 字标出现分隔写法（vert-citi / vert citi），应为 %r"
                              % (where, wordmark))
    return violations


def main(argv=None):
    ap = argparse.ArgumentParser(description="品牌锁校验（色值/字体/字标）")
    ap.add_argument("files", nargs="+", help="待检文本文件（prompt / 交付物）")
    ap.add_argument("--bundle", default=DEFAULT_BUNDLE, help="brand bundle 路径")
    args = ap.parse_args(argv)
    loaded = load_bundle(args.bundle)
    if loaded is None:
        print("品牌锁读取失败：%s 不可读或色值/字体/字标不完整，拒绝放行" % args.bundle)
        return 2
    colors, fonts, wordmark, watchlist = loaded
    print("品牌锁源：%s（允许色值 %d / 字体 %d / 字标 %r / 观察名单 %d）"
          % (args.bundle, len(colors), len(fonts), wordmark, len(watchlist)))
    all_violations = []
    for path in args.files:
        all_violations.extend(check_file(path, colors, fonts, wordmark, watchlist))
    if all_violations:
        print("品牌锁校验：违规 %d 条" % len(all_violations))
        for v in all_violations:
            print("- " + v)
        print("结论：违规（偏离品牌锁的生成结果直接废弃，SKILL.md Brand Lock）")
        return 1
    print("品牌锁校验：%d 个文件全部通过（无手写色值、无偏离字体、字标写法正确）" % len(args.files))
    print("结论：通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
