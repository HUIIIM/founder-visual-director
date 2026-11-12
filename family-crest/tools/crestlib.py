"""Geometry helpers for the family-crest study drafts.

Everything is in millimetres on the net engraving face: origin at the centre
of the oval, x to the viewer's right, y downward. A draft is a shapely
geometry meaning "engraved area" (the cavity in the gold, the relief in the
wax); whatever is not in it stays as polished metal.

The helpers keep three promises the seal rules need:

* outlines are built from points (smooth by default, corners where marked),
  so a draft is a short, reviewable list of coordinates;
* `regularize` closes white features narrower than the gap gate and opens
  black features narrower than the line gate, so no drawing can carry a
  detail the wax cannot hold;
* `svg_path` writes plain polygons (evenodd) in mm with 0.001 mm rounding.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

# Net engraving ovals (semi-axes a = half width, b = half height), mm.
FACE_12x10 = {"face": (10.0, 12.0), "margin": 0.9, "net": (8.2, 10.2)}
FACE_13x11 = {"face": (11.0, 13.0), "margin": 0.9, "net": (9.2, 11.2)}

# Gates from the design-DNA spec (mm).
GATE_MIN_LINE = 0.15
GATE_MIN_GAP = 0.20
GATE_MIN_COUNTER = 0.30
GATE_FILL = (0.80, 0.90)

# Design radii: a little above half of each gate so that rasterised
# measurement (0.005 mm pixels) still reads above the gate.
R_LINE = 0.09      # black features end in a radius >= 0.09  (0.18 mm wide)
R_GAP = 0.12       # white channels end in a radius >= 0.12  (0.24 mm wide)
R_COUNTER = 0.17   # enclosed whites end in a radius >= 0.17 (0.34 mm wide)

Pt = tuple[float, float]


def _catmull(p0, p1, p2, p3, n: int) -> list[Pt]:
    """Centripetal Catmull-Rom segment p1 -> p2 (n points, p2 excluded)."""

    def tj(ti, a, b):
        return ti + math.hypot(b[0] - a[0], b[1] - a[1]) ** 0.5

    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    if t1 == t0 or t2 == t1 or t3 == t2:
        return [p1]
    def lerp(a, b, ta, tb, t):
        w = (t - ta) / (tb - ta)
        return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)

    out = []
    for i in range(n):
        t = t1 + (t2 - t1) * i / n
        a1 = lerp(p0, p1, t0, t1, t)
        a2 = lerp(p1, p2, t1, t2, t)
        a3 = lerp(p2, p3, t2, t3, t)
        b1 = lerp(a1, a2, t0, t2, t)
        b2 = lerp(a2, a3, t1, t3, t)
        out.append(lerp(b1, b2, t1, t2, t))
    return out


def _open_spline(pts: Sequence[Pt], n: int) -> list[Pt]:
    """Smooth curve through pts (open); the end tangents come from mirrored
    phantom points."""
    if len(pts) < 3:
        return list(pts)
    first = (2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])
    last = (2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])
    ext = [first, *pts, last]
    out: list[Pt] = []
    for i in range(1, len(ext) - 2):
        out.extend(_catmull(ext[i - 1], ext[i], ext[i + 1], ext[i + 2], n))
    out.append(pts[-1])
    return out


def curve(pts: Sequence[Sequence], n: int = 16) -> list[Pt]:
    """Open curve through pts. A point written (x, y, 'c') is a corner: the
    curve is smooth on either side of it and breaks at it."""
    runs: list[list[Pt]] = [[]]
    for p in pts:
        xy = (float(p[0]), float(p[1]))
        runs[-1].append(xy)
        if len(p) > 2 and p[2] == "c" and len(runs[-1]) > 1:
            runs.append([xy])
    out: list[Pt] = []
    for run in runs:
        if len(run) < 2:
            continue
        seg = _open_spline(run, n)
        out.extend(seg if not out else seg[1:])
    return out


def outline(pts: Sequence[Sequence], n: int = 16) -> Polygon:
    """Closed outline through pts (corner marks as in `curve`). The list is
    rotated to start at its first corner, or closed smoothly if it has none."""
    pts = list(pts)
    corner = next((i for i, p in enumerate(pts) if len(p) > 2 and p[2] == "c"), None)
    if corner is None:
        m = len(pts)
        xy = [(float(p[0]), float(p[1])) for p in pts]
        out: list[Pt] = []
        for i in range(m):
            out.extend(_catmull(xy[i - 1], xy[i], xy[(i + 1) % m], xy[(i + 2) % m], n))
        return Polygon(out).buffer(0)
    rot = pts[corner:] + pts[:corner]
    first = rot[0]
    rot.append((first[0], first[1], "c"))
    return Polygon(curve(rot, n)).buffer(0)


def mirror_x(pts: Sequence[Sequence]) -> list[tuple]:
    """Right half (x >= 0, top to bottom) -> full closed list, left half
    mirrored. Points on the axis are not duplicated."""
    left = [(-p[0], p[1], *p[2:]) for p in reversed(pts) if abs(p[0]) > 1e-9]
    return [*pts, *left]


def stroke(pts: Sequence[Sequence], w: float, n: int = 16) -> Polygon:
    """Constant-width line with round caps along a smooth curve."""
    return LineString(curve(pts, n)).buffer(w / 2, cap_style="round", join_style="round")


def tstripe(pts: Sequence[Sequence], w_mid: float, w_end: float = 0.34, n: int = 16) -> Polygon:
    """A stripe that swells in the middle: ends w_end wide, middle w_mid."""
    k = len(pts)
    widths = [w_end + (w_mid - w_end) * math.sin(math.pi * i / (k - 1)) for i in range(k)]
    return taper(pts, widths, n)


def taper(pts: Sequence[Sequence], widths: Sequence[float], n: int = 16) -> Polygon:
    """Variable-width stroke with round ends. `widths` are given at the
    control points and interpolated along the curve."""
    line = curve(pts, n)
    ctrl = [(float(p[0]), float(p[1])) for p in pts]
    # arc-length position of each control point on the sampled curve
    def nearest_index(c):
        return min(range(len(line)), key=lambda i: (line[i][0] - c[0]) ** 2 + (line[i][1] - c[1]) ** 2)

    idx = [nearest_index(c) for c in ctrl]
    radii = []
    for i in range(len(line)):
        for k in range(len(idx) - 1):
            if idx[k] <= i <= idx[k + 1]:
                span = max(idx[k + 1] - idx[k], 1)
                t = (i - idx[k]) / span
                radii.append((widths[k] + (widths[k + 1] - widths[k]) * t) / 2)
                break
        else:
            radii.append(widths[-1] / 2)
    parts = []
    for (a, ra), (b, rb) in zip(zip(line, radii), zip(line[1:], radii[1:])):
        parts.append(unary_union([Point(a).buffer(ra, 24), Point(b).buffer(rb, 24)]).convex_hull)
    return unary_union(parts)


def leaf(base: Pt, tip: Pt, width: float, bend: float = 0.0, belly: float = 0.45, n: int = 20) -> Polygon:
    """Leaf blade from base to tip. `width` is the widest part, `belly`
    where along the blade it sits (0..1), `bend` a sideways bow of the midrib
    (mm, positive = to the right when looking from base to tip)."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        # midrib bows as a parabola; half-width as an asymmetric bump
        mid = (bx + dx * t + nx * bend * 4 * t * (1 - t), by + dy * t + ny * bend * 4 * t * (1 - t))
        if t <= belly:
            hw = math.sin(math.pi / 2 * t / belly) ** 0.8
        else:
            hw = math.cos(math.pi / 2 * (t - belly) / (1 - belly)) ** 0.85
        hw *= width / 2
        left.append((mid[0] + nx * hw, mid[1] + ny * hw))
        right.append((mid[0] - nx * hw, mid[1] - ny * hw))
    return Polygon(left + right[::-1]).buffer(0)


def leaf_rib(base: Pt, tip: Pt, bend: float = 0.0, start: float = 0.12, end: float = 0.8, n: int = 12) -> list[Pt]:
    """Midrib polyline of `leaf` between two fractions of its length."""
    bx, by = base
    dx, dy = tip[0] - bx, tip[1] - by
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    out = []
    for i in range(n + 1):
        t = start + (end - start) * i / n
        out.append((bx + dx * t + nx * bend * 4 * t * (1 - t), by + dy * t + ny * bend * 4 * t * (1 - t)))
    return out


def ellipse(cx: float, cy: float, rx: float, ry: float, rot: float = 0.0) -> Polygon:
    e = affinity.scale(Point(0, 0).buffer(1, 48), rx, ry)
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), cx, cy)


def almond(cx: float, cy: float, length: float, height: float, rot: float = 0.0) -> Polygon:
    """Eye shape: two arcs meeting in points, then rounded by the caller."""
    half = length / 2
    top = [(-half + length * i / 16, -height / 2 * math.sin(math.pi * i / 16) ** 0.85) for i in range(17)]
    bot = [(x, -y) for x, y in reversed(top)]
    p = Polygon(top + bot[1:-1])
    return affinity.translate(affinity.rotate(p, rot, origin=(0, 0)), cx, cy)


def flip_x(g):
    """Mirror left-right (wax impression <-> what is cut in the gold)."""
    return affinity.scale(g, -1, 1, origin=(0, 0))


def round_white(g, r: float = R_COUNTER):
    """Round a white detail so no part of it is narrower than 2r."""
    return g.buffer(-r).buffer(r)


def regularize(g, r_line: float = R_LINE, r_gap: float = R_GAP, r_counter: float = R_COUNTER):
    """Close whites narrower than 2*r_gap, open blacks narrower than
    2*r_line (twice, so the second pass sees what the first one moved), then
    round every enclosed white to 2*r_counter or fill it. The result cannot
    hold a feature below any of the three gates."""
    for _ in range(2):
        g = g.buffer(r_gap).buffer(-r_gap)
        g = g.buffer(-r_line).buffer(r_line)
    polys = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    out = []
    for p in polys:
        holes = [Polygon(i).buffer(-r_counter).buffer(r_counter) for i in p.interiors]
        shell = Polygon(p.exterior)
        holes = [h for h in holes if not h.is_empty]
        out.append(shell.difference(unary_union(holes)) if holes else shell)
    return unary_union(out).buffer(0)


def compose(mass, whites: Iterable = (), blacks: Iterable = ()):
    """Engraved area = mass minus white details, plus black details that
    sit inside whites; regularized."""
    g = mass
    w = [x for x in whites if x is not None and not x.is_empty]
    if w:
        g = g.difference(unary_union(w))
    b = [x for x in blacks if x is not None and not x.is_empty]
    if b:
        g = g.union(unary_union(b))
    return regularize(g)


def net_oval(net=(8.2, 10.2)) -> Polygon:
    return ellipse(0, 0, net[0] / 2, net[1] / 2)


def _ring(coords, tol: float) -> str:
    pts = list(LineString(coords).simplify(tol).coords)[:-1]
    return "M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in pts) + "Z"


def svg_path(g, tol: float = 0.004) -> str:
    """Path data for a (multi)polygon; use with fill-rule="evenodd"."""
    polys = [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    if isinstance(g, MultiPolygon):
        polys = list(g.geoms)
    out = []
    for p in polys:
        out.append(_ring(p.exterior.coords, tol))
        out.extend(_ring(i.coords, tol) for i in p.interiors)
    return "".join(out)
