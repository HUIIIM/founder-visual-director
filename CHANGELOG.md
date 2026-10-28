# 变更记录 / Changelog

本文件记录本项目的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
仓库尚无 git tag；版本号 1.0.0 取自 SKILL.md 与首次提交说明。
All notable changes to this project are documented here. The repo has no git tags yet; version 1.0.0 comes from SKILL.md and the initial commit.

## [Unreleased]

### Added
- 台账真实现（issue #6 P1 ③）：`references/ledger-format.md` 台账正式格式 v1.0（字段沿用 schema 草案 v0.1，定机器可读载体与结构化参考图字段 `references`，附备份说明）；`scripts/check_rotation.py` 轮换预检真读台账（相邻 3 篇 / 14 天同大类 / 冷却期 / S 级月度上限 / 白底三禁，规则数值运行时直读 rotation-rules.md），台账缺失/不可解析只出「无法判定（降级）」不冒充通过；`scripts/ledger_lib.py` 共用解析与字段校验；`demo/run.py` 轮换段接线真读判定（原仅查台账存在性）；样例台账与候选夹具入 `demo/fixtures/`，`demo/eval.sh` 纳为回归断言。 / Real ledger: formal ledger format v1.0, rotation precheck that actually reads the ledger, shared parser/validator, fixtures wired into eval.
- 品牌锁与面部一致性可执行校验（issue #6 P1 ⑤）：`scripts/check_brand_lock.py`（运行时直读 `vertciti-brand-bundle.json`，校验手写色值/偏离字体/字标写法）；`scripts/check_face_consistency.py`（anchor 恰好 1 张、一图不兼两角、参考图存在性与 SHA-256 登记比对；一图一记录字段仅预留接口）。此前两项均只有散文规则、无任何检查。 / Executable brand-lock and face-consistency checkers (were prose-only).
- AI 标识与声明字段（issue #6 P0）：SKILL.md 交付格式第七节 + `references/rotation-rules.md` 台账条目字段 schema 草案 v0.1（`ai_generated` / `ai_disclosure_text` / `ai_disclosure_method` / `ai_disclosure_basis`），对齐《人工智能生成合成内容标识办法》、小红书 AI 标识规则与 EU AI Act Art. 50。 / AI disclosure fields in the Step 5 delivery format and the draft ledger-entry schema.
- `references/prompt-standards.md` 机读规则附表 v0.1：面部禁词、年龄模式、互斥对、B 级触发词（源规则的机读化转写，供工具直读）。 / Machine-readable rule appendix in prompt-standards.md.
- `docs/PRODUCT.md` 产品一页纸；本 `CHANGELOG.md`。 / Product one-pager and this changelog.
- README：状态说明、`## 安全 / Security`、`## 许可证 / License` 小节。 / README status line, Security and License sections.
- vertciti 工程基线：`.editorconfig`、`CODEOWNERS`、Dependabot（github-actions）、gitleaks 密钥扫描、OpenSSF Scorecard workflow（2026-10-22）。 / Engineering baseline (editorconfig, CODEOWNERS, Dependabot, gitleaks, Scorecard).

### Fixed
- demo 按 skill 规则飞行（issue #6 P0）：`demo/run.py` 运行时直读 references 的强制短语、固定否定词带与禁用词表 v1.0，删除内置的另一套否定词/禁用词副本；冲突审计、面部描述检查、B 级严审均为真判定（原冲突审计为写死的"通过"，原 demo 自身 prompt 含禁用词 `cinematic` 与面部/年龄描述）；`demo/eval.sh` 在 prompt 被打回时真 FAIL（原实现被拒仍打印 PASS），并内置两个"必被拒"回归夹具。 / Demo now loads its rules from references at runtime; eval truly fails on rejection.
- gitleaks workflow 增加 `pull-requests: read` 权限，避免在 PR 上列取提交时 403。 / gitleaks workflow gains `pull-requests: read` so PR scans don't 403.
- SKILL.md 规则矛盾（issue #6 超出条款 6）：Step 3-5「视线不直视镜头」改为随脸角度预设（摆拍可给镜头）；品牌风格词 "dark cinematic" 与禁用词 `cinematic` 的关系写明（风格词不进 prompt）；「拼版 + 分层 PNG」标明为渲染阶段交付，不替代三部分输出契约。 / Rule contradictions resolved.

### Changed
- SKILL.md frontmatter 改为 Agent Skills 规范字段（name / description / license / compatibility / metadata），原 `version`、`user_invocable`、`triggers`、`requires`、`inputs`、`safety` 移入 `metadata`；版本号 1.1.0 与正文「v1.1 新增三章」对齐（尚未打 tag）。description 补英文触发词。 / Spec-compliant frontmatter; version 1.1.0.
- Step 4 增加重生成上限：同一方案连续 3 次整单打回即停，回 Step 2 改方案并记录次数与成本。 / Regeneration is capped at 3 full rejections per plan.
- `evals/smoke-01.md` 与 `evals/work/*.txt` 删除人物外貌/年龄描述与本地照片文件名（替换为中性说明）。 / Personal appearance details and photo filenames redacted from eval records.

### Added (tests, evals)
- `scripts/validate_skill.py` + `tests/`：skill 包校验与单元测试（frontmatter 规范、引用路径存在、SKILL.md 内联强制短语/否定词带与 prompt-standards.md 一致、evals.json 格式）。 / Skill-package validator with unit tests.
- `evals/evals.json`：7 例评测集（skill-creator 格式，带断言）。 / 7-case eval set.
- CI `tests.yml`：每个 PR 跑单元测试与 skill 包校验。 / Unit-test and skill-validation CI.

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
