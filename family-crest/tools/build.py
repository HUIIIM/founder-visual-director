"""Build every draft SVG, the ring-face sheet, the proof sheet and the
measurement table.

    python family-crest/tools/build.py            # writes into family-crest/
    python family-crest/tools/build.py --check    # fails if a file would change

Needs: shapely, numpy, scipy, cairosvg, pillow (not part of the skill's
runtime; the skill itself stays stdlib-only).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crestlib import FACE_12x10, flip_x, svg_path
from drafts import DRAFTS

OUT = Path(__file__).resolve().parent.parent
INK = "#111111"
NET_W, NET_H = FACE_12x10["net"]
FACE_W, FACE_H = FACE_12x10["face"]

TITLES = {
    "A1-huwen-miao-profile-couped": "A1 虎纹之苗 · 侧面虎首 couped",
    "A2-huwen-miao-face-cabossed": "A2 虎纹之苗 · 正面虎首 cabossed",
    "A3-huwen-miao-tyger-couped": "A3 虎纹之苗 · tyger 纹章虎首 couped",
    "B1-potu-two-leaves": "B1 破土 · 双叶裂土",
    "B2-potu-one-line": "B2 破土 · 一苗",
    "K1-kao-two-lines": "K1 花押 · 天地二线",
    "K2-kao-one-stroke": "K2 花押 · 一笔纹形",
    "K3-kao-yi-miao": "K3 花押 · 一苗合文",
}


def face_svg(name: str, geom) -> str:
    """A draft at true size: the net engraving oval is the page."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{NET_W}mm" height="{NET_H}mm" '
        f'viewBox="{-NET_W / 2} {-NET_H / 2} {NET_W} {NET_H}">\n'
        f"<title>{TITLES[name]}（蜡印正读；净刻面 {NET_W}x{NET_H}mm；单位 mm）</title>\n"
        f'<g class="guide" fill="none" stroke="#b9b9b9" stroke-width="0.03" stroke-dasharray="0.18 0.14">'
        f'<ellipse rx="{NET_W / 2 - 0.015}" ry="{NET_H / 2 - 0.015}"/></g>\n'
        f'<path id="charge" fill="{INK}" fill-rule="evenodd" d="{svg_path(geom)}"/>\n'
        f"</svg>\n"
    )


def kao_svg(name: str, geom) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="30mm" height="30mm" viewBox="-15 -15 30 30">\n'
        f"<title>{TITLES[name]}（骨架线稿；画幅 30x30mm）</title>\n"
        f'<path id="charge" fill="{INK}" fill-rule="evenodd" d="{svg_path(geom, 0.01)}"/>\n'
        f"</svg>\n"
    )


def _text(x, y, s, size=1.5, anchor="start", weight="normal", fill="#333"):
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
        f'fill="{fill}" font-family="\'Noto Sans CJK SC\',\'Source Han Sans SC\',\'PingFang SC\',\'Microsoft YaHei\',\'WenQuanYi Zen Hei\',sans-serif">{s}</text>'
    )


def ring_sheet(name: str, geom, lead: str) -> str:
    """Ring-face drawing at 5:1 on an A5-landscape sheet (210 x 148 mm):
    the gold face (mirrored, as cut), the wax impression (right-reading),
    a 1:1 pair, and a schematic section through the cut."""
    k = 5.0
    d_wax = svg_path(geom)
    d_gold = svg_path(flip_x(geom))
    a, b = FACE_W / 2, FACE_H / 2
    na, nb = NET_W / 2, NET_H / 2

    def face(cx, cy, d, scale, label, guides=True):
        g = [f'<g transform="translate({cx} {cy}) scale({scale})">']
        g.append(f'<ellipse rx="{a}" ry="{b}" fill="#fff" stroke="#111" stroke-width="{0.25 / scale}"/>')
        if guides:
            g.append(
                f'<ellipse rx="{na}" ry="{nb}" fill="none" stroke="#999" stroke-width="{0.12 / scale}" '
                f'stroke-dasharray="{0.9 / scale} {0.7 / scale}"/>'
            )
        g.append(f'<path fill="{INK}" fill-rule="evenodd" d="{d}"/>')
        g.append("</g>")
        g.append(_text(cx, cy + b * scale + 6, label, 3.2, "middle", "bold", "#111"))
        return "\n".join(g)

    def dim_h(cx, cy, half, y, label):
        x0, x1 = cx - half * k, cx + half * k
        return (
            f'<path d="M{x0},{y}H{x1}M{x0},{y - 1.2}V{y + 1.2}M{x1},{y - 1.2}V{y + 1.2}" stroke="#555" '
            f'stroke-width="0.15" fill="none"/>' + _text(cx, y - 1.0, label, 2.4, "middle")
        )

    def dim_v(cx, cy, half, x, label):
        y0, y1 = cy - half * k, cy + half * k
        return (
            f'<path d="M{x},{y0}V{y1}M{x - 1.2},{y0}H{x + 1.2}M{x - 1.2},{y1}H{x + 1.2}" stroke="#555" '
            f'stroke-width="0.15" fill="none"/>'
            + f'<g transform="translate({x - 1.0} {cy}) rotate(-90)">{_text(0, 0, label, 2.4, "middle")}</g>'
        )

    gx, gy = 48, 62     # gold face centre
    wx, wy = 122, 62    # wax impression centre
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="148mm" viewBox="0 0 210 148">',
        f"<title>R1 尾戒戒面雕刻图稿 · 12x10mm · {lead}（5:1；单位 mm）</title>",
        '<rect width="210" height="148" fill="#fff"/>',
        _text(8, 10, f"R1 尾戒戒面雕刻图稿 · 椭圆 12x10mm · 主纹 {lead}", 3.6, weight="bold", fill="#111"),
        _text(8, 15.5, "学习稿，喂给雕刻师的输入，不替代大师终稿。比例 5:1；虚线为净刻面边界（构造线，不入刻）；面上无框线。", 2.4),
        face(gx, gy, d_gold, k, "金面正视（反刻 · 实际下刀的样子）"),
        face(wx, wy, d_wax, k, "蜡印（正读 · 验收面 · 虎朝 dexter）"),
        dim_h(gx, gy, a, gy - b * k - 4, "面宽 10.0"),
        dim_h(gx, gy, na, gy + b * k + 11, "净刻面宽 8.2（边距 0.9）"),
        dim_v(gx, gy, b, gx - a * k - 5, "面长 12.0"),
        dim_v(wx, wy, nb, wx + a * k + 6, "净刻面长 10.2"),
        # 1:1 pair
        face(176, 40, d_gold, 1.0, "", guides=False),
        face(192, 40, d_wax, 1.0, "", guides=False),
        _text(184, 28, "1:1 实寸", 2.6, "middle", "bold", "#111"),
        _text(176, 50, "金面", 2.2, "middle"),
        _text(192, 50, "蜡印", 2.2, "middle"),
        _text(184, 55, "按 100% 打印后目视读图", 2.0, "middle"),
    ]
    # schematic section (not to scale horizontally): face thickness, cut depth, sloped walls
    sx, sy, sc = 150, 86, 9.0
    t = 2.3 * sc
    depth = 0.4 * sc
    sec = [
        f'<g transform="translate({sx} {sy})">',
        _text(0, -4, "刻口截面（示意，放大 9:1）", 2.6, weight="bold", fill="#111"),
        f'<path d="M0,0H8L9.2,{depth}H15.5L16.7,0H22L23,{depth}H26L27,0H38V{t}H0Z" fill="#e9d9a6" stroke="#111" stroke-width="0.2"/>',
        f'<path d="M41,0V{depth}M40,0H42M40,{depth}H42" stroke="#555" stroke-width="0.15" fill="none"/>',
        _text(41, -1.6, "刻深 0.3–0.5", 2.2, "middle"),
        f'<path d="M-3,0V{t}M-4,0H-2M-4,{t}H-2" stroke="#555" stroke-width="0.15" fill="none"/>',
        f'<g transform="translate(-4.2 {t / 2}) rotate(-90)">{_text(0, 0, "面厚 ≥ 2.3", 2.2, "middle")}</g>',
        _text(0, t + 4.5, "斜壁（上宽下窄），蜡才脱得出；底面平整。", 2.2),
        _text(0, t + 8, "最小线 0.15 · 最小间隙 0.20 · 内部负空间 ≥ 0.30", 2.2),
        "</g>",
    ]
    parts += sec
    notes = [
        "1. 材质：18K 黄金纯金面；手工印章刻；镜像反刻；不做锡色、不做旧。",
        "2. 主纹占净刻面高 80–90%，不触边距；本稿读数见同名 .md。",
        "3. 黑＝下刀处（蜡印上凸起）；主纹内的白线＝留金不刻（蜡印上是凸起里的沟）。",
        "4. 面上无字、无框、无冠、无环铭。格言只在内圈：始于一苗 · AB UNO GERMINE · 001。",
        "5. 戴法左手小指；主纹顶朝指尖（待裁项，见 README）。",
    ]
    for i, n in enumerate(notes):
        parts.append(_text(8, 121 + i * 5.0, n, 2.5))
    parts.append("</svg>\n")
    return "\n".join(parts)


def proof_sheet(geoms: dict) -> str:
    """A4 portrait proof: every face draft at 1:1 (on the 12x10 face), at
    32 px equivalent, as a filled silhouette, and at 4:1."""
    rows = [n for n, (_, kind) in DRAFTS.items() if kind == "face"]
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297">',
        "<title>校样单 · 家徽学习稿 2026-11（按 100% 打印；单位 mm）</title>",
        '<rect width="210" height="297" fill="#fff"/>',
        _text(10, 12, "校样单 · 家徽学习稿 2026-11", 4.2, weight="bold", fill="#111"),
        _text(10, 18, "按 100% 打印（不缩放）。左起：戒面实寸 12x10 · 剪影实寸 · 32px 等效（8.5mm 高）剪影 · 4:1 线稿 · 4:1 剪影。", 2.5),
        '<path d="M150,14H170M150,13V15M170,13V15" stroke="#111" stroke-width="0.2"/>',
        _text(160, 12, "校尺 20mm", 2.4, "middle"),
    ]
    y = 44.0
    step = 42.0
    for n in rows:
        g = geoms[n]
        d = svg_path(g)
        sil = svg_path(g.buffer(0.2).buffer(-0.2).buffer(0)) if False else svg_path(_silhouette(g))
        out.append(_text(10, y - 17, TITLES[n], 2.8, weight="bold", fill="#111"))
        # 1:1 on the face
        out.append(
            f'<g transform="translate(22 {y})"><ellipse rx="{FACE_W / 2}" ry="{FACE_H / 2}" fill="#fff" stroke="#111" '
            f'stroke-width="0.12"/><path fill="{INK}" fill-rule="evenodd" d="{d}"/></g>'
        )
        out.append(f'<g transform="translate(42 {y})"><path fill="{INK}" d="{sil}"/></g>')
        s32 = 8.47 / NET_H
        out.append(f'<g transform="translate(60 {y}) scale({s32})"><path fill="{INK}" d="{sil}"/></g>')
        out.append(
            f'<g transform="translate(104 {y}) scale(3.6)"><ellipse rx="{NET_W / 2}" ry="{NET_H / 2}" fill="none" '
            f'stroke="#bbb" stroke-width="0.04" stroke-dasharray="0.2 0.15"/>'
            f'<path fill="{INK}" fill-rule="evenodd" d="{d}"/></g>'
        )
        out.append(f'<g transform="translate(160 {y}) scale(3.6)"><path fill="{INK}" d="{sil}"/></g>')
        y += step
    out.append("</svg>\n")
    return "\n".join(out)


def _silhouette(g):
    """The charge with every interior line filled in."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    polys = [g] if isinstance(g, Polygon) else list(g.geoms)
    return unary_union([Polygon(p.exterior) for p in polys])


def build() -> dict[str, str]:
    files: dict[str, str] = {}
    geoms = {}
    for name, (fn, kind) in DRAFTS.items():
        g = fn()
        geoms[name] = g
        files[f"{name}.svg"] = face_svg(name, g) if kind == "face" else kao_svg(name, g)
        if kind == "face":
            files[f"proof/{name}-silhouette.svg"] = face_svg(name, _silhouette(g)).replace(
                "（蜡印正读", "（剪影：内部线全灭；蜡印正读"
            )
    lead = "A1-huwen-miao-profile-couped"
    files["R1-ring-face-12x10.svg"] = ring_sheet(lead, geoms[lead], "A1 侧面虎首 couped")
    files["proof/proof-sheet-2026-11.svg"] = proof_sheet(geoms)
    return files


def main(argv: list[str]) -> int:
    check = "--check" in argv
    files = build()
    changed = []
    for rel, text in files.items():
        p = OUT / rel
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            changed.append(rel)
            if not check:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8")
    if check:
        if changed:
            print("out of date:", ", ".join(changed))
            return 1
        print(f"{len(files)} files up to date")
        return 0

    from measure import measure

    table = [measure(str(OUT / f"{n}.svg")) for n, (_, kind) in DRAFTS.items() if kind == "face"]
    (OUT / "measurements.json").write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in table:
        bad = [k for k, v in r["gates"].items() if not v]
        print(
            f"{r['file']:<40} fill={r['fill_height']:.3f} clear={r['clearance_to_net_edge_mm']:.2f} "
            f"line={r['min_line_mm']} gap={r['min_gap_mm']} counter={r['min_counter_mm']} "
            f"cen_y={r['centroid_offset_mm'][1]:+.2f} {'PASS' if r['pass'] else 'FAIL ' + ','.join(bad)}"
        )
    print(f"wrote {len(changed)} changed file(s) of {len(files)}")
    return 0 if all(r["pass"] for r in table) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
