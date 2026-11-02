#!/usr/bin/env python3
"""Render a real run of the demo as a terminal-style SVG for the README (DOC-5).

Runs `python3 demo/run.py` (into a temporary output directory) and
`bash demo/eval.sh`, takes their actual output, and writes it to
docs/assets/demo-run.svg. Nothing is typed in by hand: re-running this script
is the only way to update the image. SVG text is rendered with the viewer's
fonts, so the Chinese output displays correctly without bundling a CJK font.

Usage: python3 scripts/render_demo_screenshot.py [--out docs/assets/demo-run.svg]
Exits 1 without writing anything if eval.sh fails or run.py rejects the sample
(exit 0 = pass and 5 = conditional pass are both honest demo outcomes and are
shown with their real exit code).
"""
import argparse
import os
import subprocess
import sys
import tempfile
import unicodedata
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_OK = {0: "通过", 5: "条件通过"}  # run.py exit codes, see demo/run.py docstring
LINE_H = 20
PAD = 20
WIDTH = 980
COLS = 112  # monospace columns that fit in WIDTH at 14px; CJK counts as 2
# vertciti brand bundle tokens: background.dark, text.on-dark, teal.base, text.muted
BG, FG, ACCENT, MUTED = "#161C22", "#F5F5F2", "#14B8A6", "#9AA3AF"


def run(cmd, env):
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
    return proc.returncode, (proc.stdout + proc.stderr).rstrip().splitlines()


def commit():
    out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                         capture_output=True, text=True, check=False)
    return out.stdout.strip() or "unknown"


def wrap(text):
    """Split a line at COLS display columns (East Asian wide/fullwidth = 2)."""
    out, cur, width = [], "", 0
    for ch in text:
        w = 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
        if width + w > COLS:
            out.append(cur)
            cur, width = "", 0
        cur += ch
        width += w
    return out + [cur]


def svg(lines):
    lines = [(part, color) for text, color in lines for part in wrap(text)]
    height = PAD * 2 + LINE_H * len(lines)
    rows = []
    for i, (text, color) in enumerate(lines):
        y = PAD + LINE_H * (i + 1) - 5
        rows.append(f'<text x="{PAD}" y="{y}" fill="{color}" xml:space="preserve">{escape(text)}</text>')
    body = "\n".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Real run of demo/run.py and demo/eval.sh">
<rect width="100%" height="100%" rx="8" fill="{BG}"/>
<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, 'Noto Sans Mono CJK SC', monospace" font-size="14">
{body}
</g>
</svg>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "assets", "demo-run.svg"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        rc1, out1 = run(["python3", "demo/run.py"], dict(os.environ, FVD_DEMO_OUT=tmp))
    # eval.sh checks the committed sample itself, so it runs without an output override
    rc2, out2 = run(["bash", "demo/eval.sh"], dict(os.environ))
    if rc1 not in RUN_OK or rc2:
        print("demo run failed; refusing to publish a failed run as proof", file=sys.stderr)
        print("\n".join(out1 + out2), file=sys.stderr)
        return 1

    # run.py prints the absolute temp output dir; keep the image machine-independent
    out1 = [ln.replace(tmp, "<tmp>") for ln in out1]
    out2 = [ln.replace(ROOT + os.sep, "").replace(ROOT, ".") for ln in out2]
    lines = [(f"founder-visual-director · real run at commit {commit()}", MUTED), ("", FG),
             ("$ python3 demo/run.py", ACCENT)] + [(ln, FG) for ln in out1] + [
             (f"exit {rc1}（{RUN_OK[rc1]}）", MUTED), ("", FG), ("$ bash demo/eval.sh", ACCENT)] + [
             (ln, FG) for ln in out2] + [("exit 0", MUTED)]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg(lines))
    print("screenshot written:", os.path.relpath(args.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
