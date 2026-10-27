# 变更记录 / Changelog

本文件记录本项目的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
仓库尚无 git tag；版本号 1.0.0 取自 SKILL.md 与首次提交说明。
All notable changes to this project are documented here. The repo has no git tags yet; version 1.0.0 comes from SKILL.md and the initial commit.

## [Unreleased]

### Added
- AI 标识与声明字段（issue #6 P0）：SKILL.md 交付格式第七节 + `references/rotation-rules.md` 台账条目字段 schema 草案 v0.1（`ai_generated` / `ai_disclosure_text` / `ai_disclosure_method` / `ai_disclosure_basis`），对齐《人工智能生成合成内容标识办法》、小红书 AI 标识规则与 EU AI Act Art. 50。 / AI disclosure fields in the Step 5 delivery format and the draft ledger-entry schema.
- `references/prompt-standards.md` 机读规则附表 v0.1：面部禁词、年龄模式、互斥对、B 级触发词（源规则的机读化转写，供工具直读）。 / Machine-readable rule appendix in prompt-standards.md.
- `docs/PRODUCT.md` 产品一页纸；本 `CHANGELOG.md`。 / Product one-pager and this changelog.
- README：状态说明、`## 安全 / Security`、`## 许可证 / License` 小节。 / README status line, Security and License sections.
- vertciti 工程基线：`.editorconfig`、`CODEOWNERS`、Dependabot（github-actions）、gitleaks 密钥扫描、OpenSSF Scorecard workflow（2026-10-22）。 / Engineering baseline (editorconfig, CODEOWNERS, Dependabot, gitleaks, Scorecard).

### Fixed
- demo 按 skill 规则飞行（issue #6 P0）：`demo/run.py` 运行时直读 references 的强制短语、固定否定词带与禁用词表 v1.0，删除内置的另一套否定词/禁用词副本；冲突审计、面部描述检查、B 级严审均为真判定（原冲突审计为写死的"通过"，原 demo 自身 prompt 含禁用词 `cinematic` 与面部/年龄描述）；`demo/eval.sh` 在 prompt 被打回时真 FAIL（原实现被拒仍打印 PASS），并内置两个"必被拒"回归夹具。 / Demo now loads its rules from references at runtime; eval truly fails on rejection.
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
