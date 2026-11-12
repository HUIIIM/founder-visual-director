"""The study drafts, as coordinates.

All drafts are drawn as the WAX IMPRESSION (right-reading, beasts facing
dexter = the viewer's left) on the 12x10 face's net engraving oval
(8.2 x 10.2 mm, long axis vertical). The ring face is this drawing mirrored.

Black = engraved (relief in the wax). Details inside a charge are whites:
metal left standing, a groove in the wax relief.

One sprout runs through every draft (`sprout`): a stem and two unequal
leaves, the left one smaller. In the tiger drafts it is one of the tiger's
own stripes; in the sprout drafts it is the charge; in the ciphers it is the
skeleton.
"""

from __future__ import annotations

from crestlib import (
    R_COUNTER,
    almond,
    compose,
    leaf,
    leaf_rib,
    mirror_x,
    outline,
    round_white,
    stroke,
    taper,
    tstripe,
)
from shapely import affinity
from shapely.ops import unary_union

STRIPE = 0.38  # forehead / body stripe width: spec asks >= 0.35
DETAIL = 0.36  # other white details: counter gate is 0.30


def sprout(base, top, spread, w_stem=STRIPE, w_leaf=0.62, lean=0.0, small=0.82, bow=0.16):
    """The family sprout as a set of shapes: stem from `base` to `top`, two
    leaves from `top`. `spread` is the right leaf's tip offset (dx, dy) from
    `top`; the left leaf is mirrored and scaled by `small`. Returns
    (stem, left_leaf, right_leaf)."""
    bx, by = base
    tx, ty = top
    mid = ((bx + tx) / 2 + lean, (by + ty) / 2)
    stem = stroke([base, mid, top], w_stem)
    dx, dy = spread
    right = leaf(top, (tx + dx, ty + dy), w_leaf, bend=-bow * abs(dx))
    left = leaf(top, (tx - dx * small, ty + dy * small), w_leaf * small, bend=bow * abs(dx) * small)
    return stem, left, right


def _whites(*shapes, r=R_COUNTER):
    return [round_white(s, r) for s in shapes]


# --------------------------------------------------------------------------
# A · 虎纹之苗
# --------------------------------------------------------------------------

def a1_profile_couped():
    """A Bengal tiger's head couped, facing dexter; a forked neck stripe
    grows into the sprout."""
    mass = outline(
        [
            (-3.25, -0.85, "c"),   # nose tip
            (-2.75, -1.45),
            (-2.15, -2.0),         # stop
            (-1.55, -2.75),
            (-0.85, -3.35),
            (-0.05, -3.72),        # crown
            (0.5, -3.8, "c"),      # ear, front root
            (0.85, -4.3),
            (1.4, -4.5),           # ear top (round)
            (1.95, -4.2),
            (2.15, -3.55, "c"),    # ear, back root
            (2.65, -2.75),
            (2.92, -1.7),          # back of the skull
            (2.95, -0.5),          # nape
            (3.0, 0.7),
            (3.0, 2.0),
            (2.8, 3.0),
            (2.45, 3.75, "c"),     # couped, back corner
            (1.0, 4.05),
            (-0.55, 4.2, "c"),     # couped, front corner
            (-0.65, 3.5),
            (-0.7, 2.75, "c"),     # throat under the ruff
            (-1.05, 3.15, "c"),    # ruff tuft 2
            (-1.2, 2.45, "c"),
            (-1.7, 2.7, "c"),      # ruff tuft 1
            (-1.85, 1.95),
            (-2.4, 1.75),
            (-2.8, 1.6),           # chin
            (-3.02, 1.15),
            (-2.85, 0.85, "c"),    # lower lip
            (-2.2, 0.78),
            (-1.45, 0.5, "c"),     # mouth corner
            (-2.0, 0.3),
            (-2.42, 0.22, "c"),    # fang, back root
            (-2.62, 0.52, "c"),    # fang tip
            (-2.86, 0.14, "c"),    # fang, front root
            (-3.22, 0.05, "c"),    # upper lip front
            (-3.42, -0.4),
        ]
    )
    eye = almond(-1.55, -1.55, 1.0, 0.5, rot=-26)
    f1 = tstripe([(-0.95, -2.6), (-0.65, -2.3), (-0.45, -1.9)], 0.42)
    f2 = tstripe([(-0.1, -3.05), (0.2, -2.8), (0.35, -2.45)], 0.42)
    c1 = tstripe([(-0.6, -1.2), (-0.15, -0.35), (-0.2, 0.6)], 0.46)
    c2 = tstripe([(0.6, -1.7), (1.05, -1.0), (1.15, -0.15)], 0.46)
    c3 = tstripe([(1.55, -2.6), (2.1, -1.7), (2.25, -0.65)], 0.46)
    stem, l1, l2 = sprout((0.95, 3.45), (1.0, 1.95), (1.2, -1.2), w_leaf=0.72, lean=0.06, small=0.88)
    n1 = tstripe([(-0.2, 1.65), (-0.12, 2.5), (0.1, 3.35)], 0.44)
    n2 = tstripe([(2.38, 1.6), (2.42, 2.35), (2.15, 3.0)], 0.44)
    whites = _whites(eye, f1, f2, c1, c2, c3, stem, l1, l2, n1, n2)
    return compose(mass, whites)


def a2_cabossed():
    """A Bengal tiger's face (cabossed); the forehead stripes are the
    sprout: stem and two leaves, a bar on each side."""
    half = [
        (0.0, -3.45),
        (0.7, -3.55, "c"),     # ear, inner root
        (1.05, -4.1),
        (1.75, -4.3),          # ear top
        (2.4, -3.95),
        (2.7, -3.2, "c"),      # ear, outer root
        (2.95, -2.3),
        (3.1, -1.3),
        (3.3, -0.5),
        (3.7, 0.35, "c"),      # ruff, tuft 1
        (3.25, 0.5),
        (3.2, 1.0, "c"),
        (3.55, 1.75, "c"),     # ruff, tuft 2
        (3.0, 1.85),
        (2.8, 2.3, "c"),
        (2.85, 3.05, "c"),     # ruff, tuft 3
        (2.2, 3.0),
        (1.5, 3.55),
        (0.8, 4.1),
        (0.0, 4.3),
    ]
    mass = outline(mirror_x(half))
    whites = []
    sides = []
    for s in (1, -1):
        eye = almond(s * 1.45, -0.75, 1.25, 0.56, rot=-s * 16)
        side = tstripe([(s * 1.02, -1.85), (s * 1.65, -2.1), (s * 2.3, -1.95)], 0.48, 0.42)
        ch1 = tstripe([(s * 2.85, -0.2), (s * 2.35, 0.0), (s * 2.0, 0.4)], 0.44)
        ch2 = tstripe([(s * 2.8, 1.2), (s * 2.4, 1.15), (s * 2.05, 1.4)], 0.44)
        mouth = stroke([(0.0, 2.4), (s * 0.5, 2.7), (s * 0.95, 2.9), (s * 1.3, 2.92)], DETAIL)
        whites += [eye, ch1, ch2, mouth]
        sides.append(side)
    nose = outline([(-0.8, 1.2, "c"), (0.0, 1.12), (0.8, 1.2, "c"), (0.35, 1.72), (0.0, 1.95, "c"), (-0.35, 1.72)])
    philtrum = stroke([(0.0, 1.85), (0.0, 2.4)], DETAIL)
    stem, l1, l2 = sprout((0.0, -0.1), (0.0, -1.95), (1.4, -1.05), w_stem=0.44, w_leaf=0.78, small=1.0)
    whites += [nose.union(philtrum)]
    forehead = _whites(stem.union(l1).union(l2), r=0.195) + _whites(*sides, r=0.195)
    return compose(mass, _whites(*whites) + forehead)


def a3_tyger():
    """A tyger's head couped, facing dexter: hooked tusk on the nose, two
    pointed ears, tufts on jaw and nape. The tyger has no stripes, so the
    sprout can only live in the tufts: two nape tufts are drawn as its two
    leaves, and a stem is left standing on the neck below them."""
    head = outline(
        [
            (-2.6, -1.3, "c"),     # nose
            (-1.9, -1.9),
            (-1.1, -2.6),
            (-0.4, -3.0),          # brow
            (0.5, -3.2),           # crown
            (1.4, -2.9),
            (2.0, -2.1),           # back of the skull
            (2.2, -1.0),
            (2.25, 0.2),
            (2.3, 1.6),
            (2.4, 2.8),
            (2.4, 3.85, "c"),      # couped, back corner
            (0.9, 4.2),
            (-0.9, 4.1, "c"),      # couped, front corner
            (-0.85, 3.2),
            (-1.0, 2.4),
            (-1.3, 1.9, "c"),      # jaw angle
            (-2.0, 1.7),
            (-2.75, 1.25, "c"),    # lower jaw tip
            (-2.0, 1.0),
            (-1.2, 0.55, "c"),     # mouth corner
            (-2.0, 0.25),
            (-2.75, -0.05, "c"),   # upper lip front
            (-2.9, -0.6),
        ]
    )
    tusk = taper([(-2.5, -1.1), (-3.1, -0.95), (-3.45, -0.4), (-3.32, 0.25)], [0.7, 0.55, 0.4, 0.24])
    ear1 = leaf((0.55, -2.95), (0.95, -4.4), 0.9, bend=-0.1)
    ear2 = leaf((1.45, -2.7), (2.0, -3.85), 0.85, bend=-0.12)
    beard = leaf((-1.5, 1.7), (-1.55, 2.95), 0.6)
    leaf_a = leaf((2.0, 0.55), (3.3, -1.3), 1.15, bend=-0.22)
    leaf_b = leaf((2.0, 0.75), (3.65, 0.65), 1.05, bend=0.14)
    tuft_c = leaf((2.2, 2.3), (3.15, 2.7), 0.8, bend=0.08)
    mass = unary_union([head, tusk, ear1, ear2, beard, leaf_a, leaf_b, tuft_c])
    eye = almond(-0.75, -1.7, 1.0, 0.5, rot=-24)
    rib_a = stroke(leaf_rib((2.0, 0.55), (3.3, -1.3), bend=-0.22, start=0.34, end=0.64), 0.34)
    rib_b = stroke(leaf_rib((2.0, 0.75), (3.65, 0.65), bend=0.14, start=0.34, end=0.64), 0.34)
    stem = stroke([(1.3, 3.3), (1.45, 2.1), (1.8, 1.05)], STRIPE)
    return affinity.translate(compose(mass, _whites(eye, stem) + _whites(rib_a, rib_b, r=0.16)), 0, -0.3)


# --------------------------------------------------------------------------
# B · 破土
# --------------------------------------------------------------------------

def _sprout_charge(base, top, spread, w_stem, w_leaf, small=0.84, lean=0.0, bow=0.22):
    """The sprout as a charge: black stem and leaves, a white midrib in
    each leaf."""
    stem, l1, l2 = sprout(base, top, spread, w_stem=w_stem, w_leaf=w_leaf, small=small, lean=lean, bow=bow)
    black = unary_union([stem, l1, l2])
    tx, ty = top
    dx, dy = spread
    whites = [
        stroke(leaf_rib(top, (tx + dx, ty + dy), bend=-bow * abs(dx), start=0.24, end=0.7), DETAIL),
        stroke(leaf_rib(top, (tx - dx * small, ty + dy * small), bend=bow * abs(dx) * small, start=0.26, end=0.68), DETAIL),
    ]
    return black, whites


def b1_two_leaves_broken_ground():
    """A seedling of two leaves issuant from a mount, the mount broken
    where the stem comes through."""
    black, whites = _sprout_charge((0.0, 3.5), (0.0, 0.5), (2.3, -4.55), w_stem=0.6, w_leaf=1.95, bow=-0.2)
    right = outline(
        [(0.6, 3.45, "c"), (1.2, 3.3), (1.8, 3.5), (2.2, 3.8, "c"), (1.45, 4.05), (0.6, 4.2, "c")]
    )
    left = outline(
        [(-0.6, 3.55, "c"), (-1.15, 3.4), (-1.7, 3.55), (-2.1, 3.85, "c"), (-1.4, 4.05), (-0.6, 4.2, "c")]
    )
    root = stroke([(0.0, 3.4), (0.0, 4.2)], 0.62)
    gap_r = stroke([(0.5, 3.1), (0.48, 3.5), (0.56, 3.8)], 0.34)
    gap_l = stroke([(-0.5, 3.2), (-0.48, 3.55), (-0.56, 3.8)], 0.34)
    mass = unary_union([black, right, left, root])
    return compose(mass, _whites(*whites) + [gap_r, gap_l])


def b2_one_line():
    """The sprout on a single ground line ("一"), its first root below."""
    black, whites = _sprout_charge((0.0, 2.6), (0.0, 0.45), (2.3, -4.45), w_stem=0.62, w_leaf=1.95, bow=-0.2)
    ground = stroke([(-2.75, 2.65), (2.75, 2.65)], 0.56)
    root = taper([(0.0, 2.8), (0.05, 3.4), (-0.1, 3.9), (0.0, 4.3)], [0.6, 0.46, 0.34, 0.22])
    side = taper([(0.02, 3.25), (0.5, 3.55), (0.85, 3.95)], [0.34, 0.28, 0.2])
    mass = unary_union([black, ground, root, side])
    return compose(mass, _whites(*whites))


# --------------------------------------------------------------------------
# K · 花押（线稿；不受戒面门约束，画幅 30 x 30 mm）
# --------------------------------------------------------------------------

def k1_two_lines():
    """明朝体骨架: a line above and a line below ("天地二线"), the sprout
    between them, its stem standing on the lower line."""
    top = taper([(-6.0, -11.2), (0.0, -11.9), (5.5, -11.3)], [1.2, 2.0, 1.0])
    bottom = taper([(-11.5, 10.6), (-2.0, 9.7), (12.0, 10.9)], [1.3, 2.5, 1.2])
    stem = taper([(0.3, 9.8), (-0.7, 5.2), (0.2, 1.2)], [2.2, 1.7, 1.6])
    right = taper([(0.2, 1.2), (3.6, 0.2), (6.8, -3.2), (8.4, -7.6)], [1.6, 3.3, 2.6, 0.6])
    left = taper([(0.2, 1.2), (-2.9, 0.4), (-5.5, -2.4), (-6.7, -5.9)], [1.6, 2.8, 2.2, 0.6])
    return unary_union([top, bottom, stem, right, left])


def k2_one_stroke():
    """纹形花押: one continuous stroke. It starts as the ground, turns up
    as the stem, throws the left leaf, loops, throws the right leaf; three
    short bars cross the stem (the tiger's stripes)."""
    line = taper(
        [
            (-11.0, 9.5), (-4.0, 10.6), (0.0, 9.0), (0.6, 3.0), (-0.4, -1.5),
            (-3.4, -5.2), (-6.6, -6.4), (-5.2, -2.6), (-0.4, -1.4),
            (4.0, -3.4), (7.4, -7.2), (9.2, -10.6),
        ],
        [0.6, 1.6, 1.9, 1.4, 1.2, 1.7, 0.9, 1.3, 1.2, 2.1, 1.5, 0.45],
        n=24,
    )
    bars = [
        taper([(-2.4, 4.0 + i * 1.9), (0.3, 3.5 + i * 1.9), (2.9, 4.2 + i * 1.9)], [0.5, 1.05, 0.5])
        for i in range(3)
    ]
    return unary_union([line, *bars]).buffer(0.22)


def k3_yi_miao():
    """二合体: 「一」 and 「苗」 fused. The two leaves stand where 艹 does,
    the field (田) is one closed loop with the stem as its upright, and the
    bottom stroke is 「一」."""
    yi = taper([(-10.5, 10.6), (-1.0, 9.9), (11.0, 10.9)], [1.2, 2.4, 1.3])
    field = taper(
        [(-5.2, -0.6), (-5.8, 3.6), (-4.6, 6.6), (0.2, 7.2), (4.8, 6.4), (5.6, 3.0), (5.0, -0.8), (0.0, -1.5), (-5.2, -0.6)],
        [1.4, 1.6, 1.5, 1.7, 1.5, 1.6, 1.4, 1.6, 1.4],
        n=24,
    )
    cross = taper([(-5.3, 3.0), (0.0, 2.6), (5.3, 3.1)], [1.0, 1.3, 1.0])
    stem = taper([(0.1, 7.0), (-0.2, 2.5), (0.1, -3.2)], [1.5, 1.4, 1.5])
    right = taper([(0.1, -3.2), (3.2, -4.4), (5.9, -7.4), (7.2, -10.8)], [1.5, 2.9, 2.2, 0.6])
    left = taper([(0.1, -3.2), (-2.6, -4.2), (-4.9, -6.7), (-5.9, -9.5)], [1.5, 2.5, 1.9, 0.6])
    return unary_union([yi, field, cross, stem, right, left])


DRAFTS = {
    "A1-huwen-miao-profile-couped": (a1_profile_couped, "face"),
    "A2-huwen-miao-face-cabossed": (a2_cabossed, "face"),
    "A3-huwen-miao-tyger-couped": (a3_tyger, "face"),
    "B1-potu-two-leaves": (b1_two_leaves_broken_ground, "face"),
    "B2-potu-one-line": (b2_one_line, "face"),
    "K1-kao-two-lines": (k1_two_lines, "kao"),
    "K2-kao-one-stroke": (k2_one_stroke, "kao"),
    "K3-kao-yi-miao": (k3_yi_miao, "kao"),
}

__all__ = ["DRAFTS"]
