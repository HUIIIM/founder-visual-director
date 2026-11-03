# Loop state — founder-visual-director

Updated: 2026-11-01 (loop bootstrap). Facts here are the standing state;
when one changes, the PR that changes it updates this file.

## Direction channel

- Tasks: GitHub Issues labeled `jarvis-task` in this repo.
- Reviews and verdicts: PR comments only.
- Merge owner: Jarvis. External Claude opens PRs from `claude/*` branches.

## Decisions in force

- Release tags mark published skill versions; a merged release PR is
  followed by its version tag on the merge commit
  (auto-tag mechanism, #31; details in `docs/RELEASING.md`).

## Acceptance rules

- CI green on the current head (gitleaks is a required check here).
