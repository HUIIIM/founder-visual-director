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
1. 手写色值：#RGB / #RGBA / #RRGGBB / #RRGGBBAA、rgb()/rgba()（逗号或空格语法）、hsl()/hsla()
   换算后不在允许色值集内 -> 违规；hwb()/lab()/lch()/oklab()/oklch()/color() 与 CSS 颜色属性里的
   具名颜色无法核对色板 -> 一律违规；
2. 字体：font-family 声明中的非通用族不在允许字体集内，或观察名单字体在文本任意位置出现 -> 违规；
3. 字标：vertciti 的大小写变体（Vertciti / VERTCITI / VertCiti 等）或 vert-citi / vert citi 写法 -> 违规。
退出码：0 通过 / 1 违规 / 2 bundle 或待检文件不可读（无法判定）、用法错误 / 3 内部错误。

用法：python3 scripts/check_brand_lock.py <文本文件> [更多文件...] [--bundle <bundle.json>]
"""
import argparse
import colorsys
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BUNDLE = os.path.join(REPO, "references", "vertciti-brand-bundle.json")
GENERIC_FAMILIES = {"sans-serif", "serif", "monospace", "system-ui", "cursive",
                    "fantasy", "emoji", "math", "fangsong", "inherit", "initial"}


def load_bundle(path):
    """直读 brand bundle，返回 (colors, fonts, wordmark, watchlist)；失败返回 None。"""
    try:
        with open(path, encoding="utf-8") as f:
            bundle = json.load(f)
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
    return f"#{int(r):02X}{int(g):02X}{int(b):02X}"


HEX_RE = re.compile(r"#([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{4}|[0-9A-Fa-f]{3})\b")
NUM = r"([-+]?\d*\.?\d+)(%|deg|grad|rad|turn)?"
SEP = r"\s*[,\s]\s*"
RGB_RE = re.compile(r"rgba?\(\s*" + NUM + SEP + NUM + SEP + NUM, re.IGNORECASE)
HSL_RE = re.compile(r"hsla?\(\s*" + NUM + SEP + NUM + SEP + NUM, re.IGNORECASE)
OTHER_COLOR_FN_RE = re.compile(r"\b(hwb|lab|lch|oklab|oklch|color|color-mix|device-cmyk|light-dark)\(", re.IGNORECASE)
# CSS 颜色属性里的具名颜色（自然语言里的 "red jacket" 不算，只看属性上下文）
NAMED_IN_PROPERTY_RE = re.compile(
    r"\b(?:color|background(?:-color)?|fill|stroke|border(?:-[a-z]+)?-color|outline-color)\s*:\s*([A-Za-z]+)\b",
    re.IGNORECASE)
# CSS Color Module 具名颜色（148 个）；只有属性上下文里出现这些词才算手写色值
_CSS_NAMED_COLOR_WORDS = """
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue blueviolet brown
burlywood cadetblue chartreuse chocolate coral cornflowerblue cornsilk crimson cyan darkblue
darkcyan darkgoldenrod darkgray darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange
darkorchid darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey darkturquoise
darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen fuchsia
gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew hotpink indianred indigo
ivory khaki lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon lightseagreen lightskyblue
lightslategray lightslategrey lightsteelblue lightyellow lime limegreen linen magenta maroon
mediumaquamarine mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue
mediumspringgreen mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen
paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple rebeccapurple red
rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell sienna silver skyblue slateblue
slategray slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet wheat white
whitesmoke yellow yellowgreen
"""
CSS_NAMED_COLORS = frozenset(_CSS_NAMED_COLOR_WORDS.split())


def _channel(value, unit, scale):
    v = float(value)
    return max(0.0, min(255.0, v * 255.0 / 100.0)) if unit == "%" else max(0.0, min(255.0, v * scale))


def hex_rgb_part(token):
    """#RGB / #RGBA / #RRGGBB / #RRGGBBAA -> 归一后的 #RRGGBB（alpha 不改变是否属于色板）。"""
    v = token.lstrip("#")
    if len(v) in (3, 4):
        v = "".join(ch * 2 for ch in v[:3])
    return "#" + v[:6].upper()


def colors_in_line(line):
    """返回 [(原文, 归一 hex 或 None)]；None 表示该写法无法换算到色板（一律按偏离处理）。"""
    found = []
    for m in HEX_RE.finditer(line):
        found.append((m.group(0), hex_rgb_part(m.group(0))))
    for m in RGB_RE.finditer(line):
        r, g, b = (_channel(m.group(i), m.group(i + 1), 1.0) for i in (1, 3, 5))
        found.append((m.group(0) + ")", rgb_to_hex(round(r), round(g), round(b))))
    for m in HSL_RE.finditer(line):
        hue_scale = {"turn": 360.0, "rad": 180.0 / 3.141592653589793, "grad": 0.9}.get(m.group(2), 1.0)
        h = float(m.group(1)) * hue_scale % 360 / 360.0
        sat = float(m.group(3)) / (100.0 if m.group(4) == "%" or float(m.group(3)) > 1 else 1.0)
        lig = float(m.group(5)) / (100.0 if m.group(6) == "%" or float(m.group(5)) > 1 else 1.0)
        r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, lig)), max(0.0, min(1.0, sat)))
        found.append((m.group(0) + ")", rgb_to_hex(round(r * 255), round(g * 255), round(b * 255))))
    for m in OTHER_COLOR_FN_RE.finditer(line):
        found.append((m.group(0) + "…)", None))
    for m in NAMED_IN_PROPERTY_RE.finditer(line):
        if m.group(1).lower() in CSS_NAMED_COLORS:
            found.append((m.group(0), None))
    return found


class UnreadableFile(Exception):
    """待检文件无法读取：结果是「无法判定」，不是「违规」也不是「通过」。"""


def check_file(path, colors, fonts, wordmark, watchlist):
    """返回违规字符串列表（每条含 文件:行 与命中内容）。"""
    violations = []
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise UnreadableFile(f"{path}：文件不可读或不是 UTF-8 文本（{exc.__class__.__name__}）") from exc
    for lineno, line in enumerate(lines, 1):
        where = f"{path}:{lineno}"
        # 1. 手写色值：hex（3/4/6/8 位）、rgb()/rgba()（逗号或空格语法、百分比）、hsl()/hsla()，
        #    其他颜色函数与 CSS 属性里的具名颜色无法核对色板，一律按偏离处理（独立评估 #16 P2-3）
        for raw, value in colors_in_line(line):
            if value is None:
                violations.append(f"{where} 手写色值 {raw} 无法核对品牌锁色板（请改用 bundle 内的 hex 色值）")
            elif value not in colors:
                violations.append(f"{where} 手写色值 {raw}（={value}）不在品牌锁色板内"
                                  f"（bundle 允许 {len(colors)} 个色值）")
        # 2a. font-family 声明
        for m in re.finditer(r"font-family\s*:\s*([^;}{]+)", line, re.IGNORECASE):
            for fam in m.group(1).split(","):
                name = fam.strip().strip("'\"")
                if not name or name.lower() in GENERIC_FAMILIES:
                    continue
                if name not in fonts:
                    violations.append("{} 字体 {!r} 不在品牌锁字体集内（允许：{}）".format(where, name, " / ".join(sorted(fonts))))
        # 2b. 偏离字体观察名单（任意位置出现即偏离，如已淘汰的旧字体名）
        for name in sorted(watchlist):
            if name and name in line:
                violations.append(f"{where} 出现已淘汰/待替换字体 {name!r}（品牌锁偏离）")
        # 3. 字标写法
        for m in re.finditer(r"(?i)vertciti", line):
            if m.group(0) != wordmark:
                violations.append(f"{where} 字标写法 {m.group(0)!r} 偏离品牌锁（应为全小写 {wordmark!r}）")
        if re.search(r"(?i)vert[-\s]citi", line):
            violations.append(f"{where} 字标出现分隔写法（vert-citi / vert citi），应为 {wordmark!r}")
    return violations


def main(argv=None):
    ap = argparse.ArgumentParser(description="品牌锁校验（色值/字体/字标）")
    ap.add_argument("files", nargs="+", help="待检文本文件（prompt / 交付物）")
    ap.add_argument("--bundle", default=DEFAULT_BUNDLE, help="brand bundle 路径")
    args = ap.parse_args(argv)
    loaded = load_bundle(args.bundle)
    if loaded is None:
        print(f"品牌锁读取失败：{args.bundle} 不可读或色值/字体/字标不完整，拒绝放行")
        return 2
    colors, fonts, wordmark, watchlist = loaded
    print(f"品牌锁源：{args.bundle}（允许色值 {len(colors)} / 字体 {len(fonts)} / "
          f"字标 {wordmark!r} / 观察名单 {len(watchlist)}）")
    all_violations = []
    for path in args.files:
        try:
            all_violations.extend(check_file(path, colors, fonts, wordmark, watchlist))
        except UnreadableFile as exc:
            print(f"品牌锁校验：无法判定 —— {exc}")
            return 2
    if all_violations:
        print(f"品牌锁校验：违规 {len(all_violations)} 条")
        for v in all_violations:
            print("- " + v)
        print("结论：违规（偏离品牌锁的生成结果直接废弃，SKILL.md Brand Lock）")
        return 1
    print(f"品牌锁校验：{len(args.files)} 个文件全部通过（无手写色值、无偏离字体、字标写法正确）")
    print("结论：通过")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 -- 内部错误不得冒充「违规」(1)
        print(f"内部错误：{exc.__class__.__name__}: {exc}", file=sys.stderr)
        sys.exit(3)
