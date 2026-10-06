# founder-visual-director

**Founder visual production, directed.** A skill that provides director-level guidance for AI-generated founder photography: executable image-generation prompts, full-size photorealism QA checklists, and asset-rotation compliance verdicts.

Built for [Miao](https://vertciti.com) (Jiahui Miao) — N=1 founder IP infrastructure. Input a scene brief, get back a three-part deliverable covering Xiaohongshu, Instagram, LinkedIn founder covers and illustrations.

## What it delivers

Every run produces three parts:

1. **Image prompt** — Positive prompt + fixed negative-token block + banned-word grep result + conflict audit.
2. **QA checklist** — Face-angle rules → 10-point proportion check → photorealism (anatomy/physics/global) → background physics. Any red-line fail = full regenerate.
3. **Rotation compliance** — Check against the asset ledger (last 3 posts, cooldown periods, white-background ban). Verdict: pass / conditional / violation + remediation.

## Quick start

```bash
cd demo
python3 run.py < input.json
# Output lands in demo/output/
```

See `demo/README.md` for the minimal runnable slice (30 seconds, zero external dependencies).

## Requirements

- `founder-visual-studio` (companion skill for shot planning)
- Visual spec v1.6/v1.7; asset rotation rules in `references/`

## Safety red lines

- The white-background standard avatar is **never** used as content illustration.
- Every image gets full-size visual inspection before release.
- Same outfit / same styling in adjacent posts = duplicate (rejected).

## License

MIT — see [LICENSE](LICENSE).

## Author

**Jiahui Miao** — Founder, [vertciti](https://vertciti.com). Building procurement infrastructure for AI agents. Participates in 3GPP working on 6G core network standards.
