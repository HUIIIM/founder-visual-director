# founder-visual-director

A vertciti skill that turns a scene brief for AI-generated founder photography into an executable image
prompt, a full-size photorealism QA checklist and a rotation-compliance verdict, for founders publishing on
Xiaohongshu, Instagram and LinkedIn.

| | |
|---|---|
| Status | active · early — v1.1.0 in `SKILL.md` metadata, not yet tagged (first release 1.0.0 on 2026-10-06); the runnable demo stops at prompt level (no image rendering); `evals/` holds one smoke run and a 7-case eval set |
| Type | vertciti skill (agent skill defined in [SKILL.md](SKILL.md)) |
| Install / use | Load `SKILL.md` as a skill in your agent; try the zero-dependency demo with `python3 demo/run.py` |
| Licence | MIT ([LICENSE](LICENSE)), Copyright (c) 2026 Jiahui Miao |
| Languages | README in English · skill text, references and demo output in 简体中文 |
| Contact | Security: see [Security](#security) · Product: [vertciti.com](https://vertciti.com) |

## Overview

AI-generated founder imagery fails in repeatable ways: faces and anatomy that look wrong, physics that do
not hold (hands, reflections, light direction), and visual repetition across consecutive posts (same
outfit, styling or background). This skill makes the checks explicit. Given a scene brief, it produces three
deliverables, and any red-line failure in the QA checklist means the image is regenerated rather than
patched.

Product one-pager: [docs/PRODUCT.md](docs/PRODUCT.md) · Changelog: [CHANGELOG.md](CHANGELOG.md)

## Capabilities

| Deliverable | What it contains |
|---|---|
| Image prompt | Executable positive prompt, fixed negative-token block, banned-word grep result, conflict audit (brief vs. standing rules) |
| QA checklist | Face-angle rules, 10-point proportion check, photorealism pass (anatomy / physics / global consistency), background physics |
| Rotation compliance | Check against the asset ledger (last 3 posts, cooldown periods, white-background avatar ban, adjacent-post outfit/styling duplication). Verdict: pass / conditional / violation, with remediation |

Typical uses: a Xiaohongshu cover for the next post, an Instagram daily illustration that must not repeat an
outfit, a LinkedIn professional portrait, or the first post of a new visual series.

## Quick start

```bash
git clone https://github.com/HUIIIM/founder-visual-director && cd founder-visual-director
python3 demo/run.py    # reads demo/input.json, writes demo/output/{prompt.txt,checklist.md,rotation.md}
bash demo/eval.sh      # prints PASS / FAIL for the three deliverables
```

No external dependencies beyond Python 3. A worked output set is committed in
[`demo/output/`](demo/output/). See [`demo/README.md`](demo/README.md) for the scope of the demo.

## Input contract

The skill does not invent a brief. The caller supplies at minimum:

| Field | Example |
|---|---|
| Theme / platform / content line | Xiaohongshu post 10 / IG daily / LinkedIn industry take |
| Scene | Post-run stretching on a city balcony |
| Mood | Calm, cinematic |
| Rotation context | Last 3 posts' outfits, scenes, backgrounds |

Missing fields are asked for, not filled in. Declared dependencies (from `SKILL.md`): the companion
`founder-visual-studio` skill, visual spec v1.6/v1.7 and the asset rotation rules in
[`references/`](references/).

## Repository layout

```
SKILL.md      the skill: director protocol, input contract, red lines
demo/         prompt-level slice: input.json -> output/ (prompt.txt, checklist.md, rotation.md)
references/   visual spec, photorealism checklist, rotation rules, model notes
scripts/      rule checkers (rotation, brand lock, face consistency) and validate_skill.py
tests/        unit tests: python3 -m unittest discover -s tests
evals/        smoke run (smoke-01.md) and eval set (evals.json, skill-creator format)
docs/         product one-pager
```

## Safety rules

- The white-background standard avatar is never used as a content illustration.
- Every image is inspected at full size before release; thumbnails do not count.
- The same outfit or styling in adjacent posts counts as a duplicate and is rejected.
- Generated backgrounds must differ visibly from recent ones.

## Status and limitations

- The demo validates the chain from input contract to the three deliverables at prompt level only. Image
  rendering runs in a separate media pipeline and requires human inspection.
- The rotation check expects an asset ledger; when it is missing, the skill marks the ledger as pending
  instead of assuming compliance.
- `evals/` contains one smoke evaluation; further evaluations are planned, not done.
- The skill does not replace a human art director. Full-size human inspection remains a release
  requirement.

## Security

See [SECURITY.md](SECURITY.md) to report a security issue; do not open a public issue. Data handling,
including the founder-likeness assets the skill refers to, is described in [docs/PRIVACY.md](docs/PRIVACY.md). CI runs the demo eval, gitleaks secret scanning, dependency review and OpenSSF Scorecard.

## Contributing

Issues and pull requests are welcome. Visual-quality claims need full-size before/after evidence.

## Licence

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Jiahui Miao.

Built by vertciti — https://vertciti.com
