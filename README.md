# founder-visual-director

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](SKILL.md)

**AI founder photos that look cheap destroy credibility. This skill is the director on set: it turns a scene brief into an executable image prompt, a photorealism QA checklist, and a rotation-compliance verdict — before anything ships.**

[Quick start](#30-second-quick-start) · [What it delivers](#what-it-delivers) · [Demo](#demo) · [FAQ](#faq)

A [Vertciti Skill Pack](https://vertciti.com) for director-level control over AI-generated founder photography. One scene brief in, three-part deliverable out — covering Xiaohongshu, Instagram, and LinkedIn founder covers and illustrations.

Built for [Miao](https://vertciti.com) (Jiahui Miao) — N=1 founder IP infrastructure.

## The real problem it solves

AI-generated founder imagery fails in three repeatable ways: uncanny faces and broken physics (hands, reflections, light direction), and visual repetition (same outfit, same styling, same background two posts in a row — the audience notices before you do). founder-visual-director mechanizes the guardrails: full-size photorealism checks where any red-line fail means full regenerate, and rotation compliance against an asset ledger with cooldown rules.

## What it delivers

Every run produces three parts:

1. **Image prompt** — Executable positive prompt + fixed negative-token block + banned-word grep result + conflict audit (brief vs. standing rules).
2. **QA checklist** — Face-angle rules → 10-point proportion check → photorealism pass (anatomy / physics / global consistency) → background physics. Any red-line fail = full regenerate, no patching.
3. **Rotation compliance** — Checked against the asset ledger (last 3 posts, cooldown periods, white-background avatar ban, adjacent-post outfit/styling duplication rule). Verdict: **pass** / **conditional** / **violation** + remediation.

## 30-second quick start

```bash
cd demo
python3 run.py < input.json
# Output lands in demo/output/ (prompt.txt, checklist.md, rotation.md)
```

See `demo/README.md` for the minimal runnable slice (zero external dependencies).

## Demo

A complete worked output set ships in `demo/output/`:

- `prompt.txt` — the executable image prompt from the sample brief
- `checklist.md` — the full photorealism QA checklist as produced
- `rotation.md` — the rotation-compliance verdict from the sample asset ledger

> Demo recording/screenshot of the three-part deliverable being used in a real release: 待补（占位）——output files above are already real; a visual walkthrough is planned.

## When to use it

| Scenario | What it produces |
|---|---|
| Xiaohongshu cover for the next post | Executable prompt + QA checklist tuned for the platform |
| IG daily illustration, outfit must differ | Rotation verdict blocks same-styling repeats |
| LinkedIn professional portrait | Credibility-first direction, no influencer look |
| Launching a new visual series | Background/scene/contrast differentiation against the ledger |

## Repo layout

```
founder-visual-director/
  SKILL.md      # the skill itself: director protocol, input contract, red lines
  demo/         # 30-second slice: input.json → output/(prompt.txt, checklist.md, rotation.md)
  references/   # visual spec v1.6/v1.7, asset rotation rules
  evals/        # smoke evaluations (in progress)
``` A complete worked output set ships in `demo/output/`.

## Input contract

The skill refuses to hallucinate a brief. The caller must supply (at minimum):

| Field | Example |
|---|---|
| Theme / platform / content line | 小红书第 10 篇 / IG daily / LinkedIn industry take |
| Scene need | Post-morning-run stretching, city balcony |
| Mood | Calm confidence, cinematic |
| Rotation context | Last 3 posts' outfits, scenes, backgrounds |

Missing fields are asked for, not invented. Requires the companion `founder-visual-studio` skill (shot planning) and visual spec v1.6/v1.7; rotation rules live in `references/`.

## Safety red lines

- The white-background standard avatar is **never** used as content illustration.
- Every image gets full-size visual inspection before release — thumbnails don't count.
- Same outfit / same styling in adjacent posts = duplicate (rejected).
- Generated backgrounds must differ visibly from recent ones — no lazy reskins.

## Roadmap

- `evals/` smoke evaluations with side-by-side similarity judgments (in progress).
- Rotation ledger automation: machine-diff new briefs against posted-asset log.
- Platform expansion rules (TikTok now in standing release schedule) folded into rotation compliance.

## FAQ

**Why not just describe the scene and let the model decide?**
Models default to the average of their training data — same gray suit, same office window. The director's job is to force difference: background, light, framing, mood all specified, all checked against what already shipped.

**What does "red-line fail = full regenerate" mean in practice?**
Hands wrong, reflection impossible, light direction inconsistent — any of these means start over. Patching a generated image with "just fix the hand" destroys global consistency; the QA checklist enforces this mechanically.

**How does rotation compliance know what's been posted?**
Against the asset ledger: last 3 posts' outfits, scenes, backgrounds plus cooldown rules. Same outfit / same styling in adjacent posts = duplicate, rejected. The ledger is the memory the model doesn't have.

**Does it replace a human art director?**
No. It replaces the "forgot to check" part. Full-size human inspection is still a red line before release — the skill makes sure the inspection has something real to inspect.

## Contributing

Issues and PRs welcome. Visual-quality claims need before/after evidence at full size, not adjectives.

## License

| Module | License | Plain meaning |
|---|---|---|
| All files | MIT | Commercial use OK, modify OK, attribution required |

See [LICENSE](LICENSE).

## Author

**Jiahui Miao** — Founder, [vertciti](https://vertciti.com). Building procurement infrastructure for AI agents. Participates in 3GPP working on 6G core network standards.
