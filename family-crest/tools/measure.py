"""Measure a draft against the seal gates, from its rendered SVG.

The measurement does not reuse the geometry that drew the draft: the SVG is
rasterised by CairoSVG at 200 px/mm (0.005 mm pixels) and every reading comes
from that bitmap.

Readings
--------
* fill: charge height / net-face height (gate 0.80-0.90) and width ratio;
* clearance: smallest distance from the charge to the net-oval edge
  (the charge must not enter the margin, so this must be > 0);
* min line: narrowest engraved (black) feature;
* min gap: narrowest unengraved (white) channel open to the field;
* min counter: narrowest white area fully enclosed by the charge;
* centroid: offset of the charge's centre of mass from the oval centre
  (negative y = above centre).

Width of a feature = the diameter of the largest disc that can reach every
part of it (morphological opening). Thin necks, hairlines and sharp corners
all lower the reading, which is what wax does to them too. Readings are
capped at 0.60 mm ("0.6" means "0.6 or more").

Usage: python measure.py draft.svg [--net 8.2x10.2] [--json]
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage

PX_PER_MM = 200
GATES = {"min_line": 0.15, "min_gap": 0.20, "min_counter": 0.30, "fill": (0.80, 0.90)}


def rasterise(svg_path: str, px_per_mm: int = PX_PER_MM) -> tuple[np.ndarray, tuple[float, float]]:
    """Black mask of the SVG (True = engraved) and its size in mm. The SVG
    must declare width/height in mm."""
    text = Path(svg_path).read_text(encoding="utf-8")

    m = re.search(r'<svg[^>]*\swidth="([\d.]+)mm"[^>]*\sheight="([\d.]+)mm"', text)
    if not m:
        raise SystemExit(f"{svg_path}: <svg> needs width/height in mm")
    w_mm, h_mm = float(m.group(1)), float(m.group(2))
    # guides are not part of the charge
    text = re.sub(r'<g[^>]*class="guide".*?</g>', "", text, flags=re.DOTALL)
    png = cairosvg.svg2png(
        bytestring=text.encode("utf-8"),
        output_width=round(w_mm * px_per_mm),
        output_height=round(h_mm * px_per_mm),
        background_color="white",
    )
    img = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    return img < 128, (w_mm, h_mm)


def _min_width(mask: np.ndarray, hi_px: float = 0.6 * PX_PER_MM) -> tuple[float, tuple[int, int]]:
    """Narrowest feature of `mask`, in pixels, and where (row, col).

    The reading is the diameter of the largest disc that can reach every
    part of the mask (a morphological opening leaves the mask unchanged).
    A part the disc cannot reach -- a thin neck, a hairline, a corner
    sharper than the disc -- is a part the wax cannot hold. Two pixels of
    slack absorb rasterisation."""
    if not mask.any():
        return float("inf"), (0, 0)
    d_in = ndimage.distance_transform_edt(mask)

    def residual(r: float):
        core = d_in > r
        if not core.any():
            return np.inf, np.unravel_index(np.argmax(d_in), d_in.shape)
        d_core = ndimage.distance_transform_edt(~core)
        miss = np.where(mask, d_core - r, 0.0)
        k = np.unravel_index(np.argmax(miss), miss.shape)
        return float(miss[k]), k

    slack = 2.0
    lo, hi = 0.0, hi_px / 2
    where = (0, 0)
    if residual(hi)[0] <= slack:
        return 2 * hi, where
    for _ in range(8):
        mid = (lo + hi) / 2
        miss, k = residual(mid)
        if miss <= slack:
            lo = mid
        else:
            hi, where = mid, k
    return 2 * lo, (int(where[0]), int(where[1]))


def measure(svg_path: str, net: tuple[float, float] = (8.2, 10.2)) -> dict:
    black, _size = rasterise(svg_path)
    h, w = black.shape
    s = PX_PER_MM
    cx, cy = w / 2, h / 2
    yy, xx = np.indices(black.shape)
    inside = ((xx + 0.5 - cx) / (net[0] / 2 * s)) ** 2 + ((yy + 0.5 - cy) / (net[1] / 2 * s)) ** 2 <= 1.0

    rows = np.where(black.any(axis=1))[0]
    cols = np.where(black.any(axis=0))[0]
    height_mm = (rows[-1] - rows[0] + 1) / s
    width_mm = (cols[-1] - cols[0] + 1) / s

    # clearance to the net-oval edge (negative = the charge is in the margin)
    d_in = ndimage.distance_transform_edt(inside)
    if (black & ~inside).any():
        clearance = -float(ndimage.distance_transform_edt(~inside)[black & ~inside].max()) / s
    else:
        clearance = float(d_in[black].min()) / s

    # whites: field (touches the frame) vs counters (enclosed by the charge)
    white = ~black
    labels, _ = ndimage.label(white)
    edge = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    field = np.isin(labels, edge[edge > 0])
    counters = white & ~field

    line_px, line_at = _min_width(black)
    gap_px, gap_at = _min_width(field)
    cnt_px, cnt_at = _min_width(counters)

    ys, xs = np.nonzero(black)
    cen = ((xs.mean() - cx) / s, (ys.mean() - cy) / s)

    def at(rc):
        return [round((rc[1] - cx) / s, 2), round((rc[0] - cy) / s, 2)]

    def mm(v):
        return None if not np.isfinite(v) else round(v / s, 3)

    n_counters = int(ndimage.label(counters)[1])
    out = {
        "file": svg_path.replace("\\", "/").split("/")[-1],
        "net_face_mm": list(net),
        "charge_height_mm": round(height_mm, 2),
        "charge_width_mm": round(width_mm, 2),
        "fill_height": round(height_mm / net[1], 3),
        "fill_width": round(width_mm / net[0], 3),
        "clearance_to_net_edge_mm": round(clearance, 3),
        "min_line_mm": mm(line_px),
        "min_line_at": at(line_at),
        "min_gap_mm": mm(gap_px),
        "min_gap_at": at(gap_at),
        "counters": n_counters,
        "min_counter_mm": mm(cnt_px),
        "min_counter_at": at(cnt_at),
        "centroid_offset_mm": [round(float(cen[0]), 2), round(float(cen[1]), 2)],
        "engraved_share_of_net_area": round(float(black.sum()) / float(inside.sum()), 3),
    }
    g = GATES
    out["gates"] = {
        "fill_80_90": bool(g["fill"][0] <= out["fill_height"] <= g["fill"][1]),
        "inside_net_face": bool(clearance > 0),
        "min_line_0.15": out["min_line_mm"] is None or out["min_line_mm"] >= g["min_line"],
        "min_gap_0.20": out["min_gap_mm"] is None or out["min_gap_mm"] >= g["min_gap"],
        "min_counter_0.30": out["min_counter_mm"] is None or out["min_counter_mm"] >= g["min_counter"],
        "centroid_at_or_above_centre": out["centroid_offset_mm"][1] <= 0.0,
    }
    out["gates"] = {k: bool(v) for k, v in out["gates"].items()}
    out["pass"] = all(out["gates"].values())
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("svg", nargs="+")
    ap.add_argument("--net", default="8.2x10.2", help="net engraving oval, WxH in mm")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    net = tuple(float(v) for v in a.net.split("x"))
    results = [measure(p, net) for p in a.svg]
    if a.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            flags = " ".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in r["gates"].items())
            print(
                f"{r['file']}: h={r['charge_height_mm']} ({r['fill_height']:.0%}) w={r['charge_width_mm']} "
                f"clear={r['clearance_to_net_edge_mm']} line={r['min_line_mm']}@{r['min_line_at']} "
                f"gap={r['min_gap_mm']}@{r['min_gap_at']} counter={r['min_counter_mm']}@{r['min_counter_at']} "
                f"centroid={r['centroid_offset_mm']} | {flags}"
            )
    return 0 if all(r["pass"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
