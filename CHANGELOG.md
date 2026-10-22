# 变更记录 / Changelog

本文件记录本项目的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
仓库尚无 git tag；版本号 1.0.0 取自 SKILL.md 与首次提交说明。
All notable changes to this project are documented here. The repo has no git tags yet; version 1.0.0 comes from SKILL.md and the initial commit.

## [Unreleased]

### Added
- `docs/PRODUCT.md` 产品一页纸；本 `CHANGELOG.md`。 / Product one-pager and this changelog.
- README：状态说明、`## 安全 / Security`、`## 许可证 / License` 小节。 / README status line, Security and License sections.
- vertciti 工程基线：`.editorconfig`、`CODEOWNERS`、Dependabot（github-actions）、gitleaks 密钥扫描、OpenSSF Scorecard workflow（2026-10-22）。 / Engineering baseline (editorconfig, CODEOWNERS, Dependabot, gitleaks, Scorecard).

### Fixed
- gitleaks workflow 增加 `pull-requests: read` 权限，避免在 PR 上列取提交时 403。 / gitleaks workflow gains `pull-requests: read` so PR scans don't 403.

## 2026-10-14

### Changed
- README Author 小节：以 N=1 标准表述替换已停用的采购定位。 / Author section: retired procurement positioning replaced with the N=1 line.

## 2026-10-07

### Changed
- README 重构：首屏 slogan 与导航、Demo 区、使用场景表、FAQ、License 白话表。 / README restructure: hook, nav, demo, scenarios, FAQ, plain-language license table.

## [1.0.0] - 2026-10-06

### Added
- 首次公开发布：`SKILL.md`（导演协议、输入/输出契约、红线）。 / Initial public release of the skill.
- `demo/`：零依赖最小切片 `run.py`、`eval.sh`（PASS/FAIL）、样例输入与三件套输出。
- `references/`：脸角度、人体比例、真实感、背景物理、轮换规则、prompt 规范等参考文档。
- `evals/smoke-01.md`：一次完整 dry-run 冒烟评估。
- MIT `LICENSE`。
