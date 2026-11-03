# 变更记录 / Changelog

本文件记录本项目的所有重要变更。格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
版本以 git 标签为准（自 v1.1.0 起，发布页附 SBOM、Sigstore 签名与构建来源证明）；1.0.0 未打标签，取自首次提交说明。
Versions follow git tags from v1.1.0 on (releases carry an SBOM, Sigstore signatures and build provenance); 1.0.0 was never tagged and comes from the initial commit.

## [Unreleased]

### Changed
- 机读规则附表升至 v0.2（#42）：B 级触发补英文对译（famous / actor / gala / dinner party 等），文字年龄（thirties / thirty-something / 四十多岁）、面部词「眼神」、禁用词 cinematic 的中文对应「电影感」入表；词形变化逐条列出（smiley / grinning / lifted shadows / brightened 等；不做后缀通配，免得 `grin` 误伤叙事调性 `grind`）；电影质感 / 电影级、连字符与中文数字年龄、中年、目光 / 嘴角 / 笑、红毯 / 宴会 / 颁奖典礼入表；匹配前去零宽字符并 NFKC；白底 / white background / 白墙等 + 人像，以及证件照，按白底标准照拦截（棚拍、白 T 恤、竖构图 portrait orientation 不算）；中年只认作人称、年龄不算他人（两岁的女儿）。34 个绕过探针与 19 个正常场景（含 SKILL.md 叙事调性原词、暗调棚拍）写成回归测试（`tests/test_prompt_rules.py`）。 / Rule table v0.2 closes 34 bypass probes without rejecting the skill's own vocabulary.
- demo 的 QA 检查表改为逐项取自 references（脸角度 3 + 人体比例 10 + 真实感 11 + 背景 5），条数不符按规则读取失败拒绝放行；满足 `evals.json` #7 的断言。 / The demo QA checklist now carries every item from references.

### Fixed
- 面部一致性校验在空台账或全部条目已退役时不再报「通过」，改为「无法判定」（退出码 2）（#23 第 1 项）。 / Face check on an empty or all-retired ledger is "cannot judge", not a pass.
- 轮换报告里调用方提供的值单行化并加「」，伪造不了「- 结论：」行；`demo/run.py` 只认最后一条「- 结论：」行（#23 第 2 项）。 / Candidate text can no longer forge the rotation verdict line.
- 品牌锁补查 `color-mix()` / `device-cmyk()` / `light-dark()` 与 hue 单位 turn / rad / grad 的 `hsl()`（#23 第 4 项）。 / Remaining brand-lock colour bypasses closed.
- 发布流程先核对标签所在提交在 `main` 上，否则不发布（#23 第 6 项）。 / Release refuses a tag whose commit is not on main.

## [1.1.0] - 2026-10-30

### Added (publishing)
- 发布前动作增加替代文本（alt text）要求，QA 检查表增加对应勾选项；README 写明 OpenSSF Scorecard 公开分（2026-10-30 为 6.9 / 10）及未达项。 / Alt-text step before publishing; README states the public Scorecard score.

### Fixed
- 轮换结论进入终判（独立评估 #16 P1-1）：`demo/run.py` 先跑轮换预检再写交付物；轮换违规 = 打回（退出码 3，不给台账条目）；无法判定 / 条件通过 = 终判「条件通过」（新退出码 5，只给「待复核」条目）。此前违规台账照样「终判：通过」、退出码 0。 / The rotation verdict now drives the final verdict and exit code.
- 缺无关字段不再把台账条目踢出轮换比对（#16 P1-2）：每项检查使用具备该项所需字段的全部条目，缺 `model_id`、AI 声明等字段只记不确定性；台账有条目但没有一条可用时为「无法判定」。 / Entries missing unrelated fields still count in rotation checks.
- 平台枚举与别名归一（#16 P1-3）：`platform` 只能是 小红书 / IG / LinkedIn（`XHS`、`Instagram` 等别名归一）；不再从 `theme_platform` 推断平台，非法或缺失即「无法判定」。 / Platform enum with aliases; no fallback to the theme string.
- 「条件通过」不再与「通过」同码（#16 P2-1）：`check_rotation.py` 条件通过退出码 4，候选缺字段时逐项写「无法判定（缺 …）」。 / Conditional pass has its own exit code; affected checks say so.
- 校验脚本崩溃不再冒充「违规」（#16 P2-2）：非对象条目/候选、非 UTF-8 文件按「无法判定」处理；未预期异常走独立退出码（rotation 5，品牌锁/面部 3）。 / Crashes no longer exit as "violation".
- 品牌锁色值检查补全（#16 P2-3）：4/8 位 hex、空格语法与百分比 rgb()、hsl()、hwb/lab/lch/oklab/oklch/color() 与 CSS 属性里的具名颜色均纳入检查。 / Brand-lock colour bypasses closed.
- `uses_standard_portrait` 必须是 JSON 布尔值（#16 P2-4），字符串 "true"/"false" 以退出码 2 拒绝。 / Portrait flag must be a boolean.
- gitleaks 检出不再把 job token 留在 `.git/config`（#16 P2-6）。 / gitleaks checkout drops persisted credentials.

### Added (review #16)
- `tests/test_checkers.py`：轮换 / 台账 / 品牌锁 / 面部一致性的表驱动单测，含 #16 全部复现（#16 P2-5）；`demo/eval.sh` 新增退出码断言与 P1-1/P1-2/P1-3 回归夹具。 / Unit tests for the checkers.
- 台账格式：平台枚举与别名、可选 `model_consent_status`（expired / revoked = 违规）；SECURITY.md 写明肖像与授权数据在仓库外但属安全范围（#16 P2-8）。 / Platform enum, consent field, SECURITY scope.

- demo 输入校验：非 JSON 对象 / JSON 损坏 / 必填项非字符串一律以退出码 2 拒绝（此前抛 traceback 或放行）。 / Bad input is refused with exit 2 instead of a traceback.
- 输入字段单行化并去掉 `#`，`scene` 里的换行不能再伪造「## 终判：通过」等段落。 / Inputs can no longer forge report sections.
- 场景文字写明白底标准照时直接打回（事故级，不依赖台账或调用者另设 `uses_standard_portrait`）；写明白底/棚拍且未给大类时按「白底棚拍」判定。 / White-background portrait in the scene text is rejected on its own.
- 样例输出不再带本机绝对台账路径、`input.json` 固定日期，`demo/output/` 可在任何机器上逐字复现；`eval.sh` 先比对再重写样例。 / Sample output is reproducible.
- SKILL.md / prompt-standards.md「按年龄写皮肤」与「prompt 模板铁律」1 冲突、rotation-rules.md 白底三禁第 3 条歧义；SKILL.md「管线 403」改为如实说明由外部管线执行。 / Rule contradictions resolved.

### Added
- 发布流程：`release.yml` 在推送 `v*` 标签时先跑与 PR CI 相同的门禁（ruff、单元测试、skill 包校验、demo eval、样例可复现），再生成源码包、可复现的 CycloneDX SBOM（`scripts/make_sbom.py`，序列号取 UUIDv5、时间取标签提交时间）与 SHA256SUMS，逐个用 Sigstore 无密钥签名（`*.sigstore.json`），并附 GitHub 构建来源证明；所有 action 按提交 SHA 固定。`docs/RELEASING.md` 写明发版、校验与回滚步骤。 / Release workflow: CI-equivalent gate, reproducible SBOM, Sigstore signatures and build provenance; release, verify and rollback guide.
- `demo.yml` CI：每个 PR 跑 `demo/eval.sh`、`ruff check`（`requirements-dev.txt` 按哈希安装）并确认样例未被改写；`demo/` 与 `scripts/` 清零 ruff 存量问题（输出逐字不变）；`SECURITY.md`、`docs/PRIVACY.md`；`.gitignore` 忽略仓根台账。 / Demo CI, SECURITY.md, PRIVACY.md.
- 台账真实现（issue #6 P1 ③）：`references/ledger-format.md` 台账正式格式 v1.0（字段沿用 schema 草案 v0.1，定机器可读载体与结构化参考图字段 `references`，附备份说明）；`scripts/check_rotation.py` 轮换预检真读台账（相邻 3 篇 / 14 天同大类 / 冷却期 / S 级月度上限 / 白底三禁，规则数值运行时直读 rotation-rules.md），台账缺失/不可解析只出「无法判定（降级）」不冒充通过；`scripts/ledger_lib.py` 共用解析与字段校验；`demo/run.py` 轮换段接线真读判定（原仅查台账存在性）；样例台账与候选夹具入 `demo/fixtures/`，`demo/eval.sh` 纳为回归断言。 / Real ledger: formal ledger format v1.0, rotation precheck that actually reads the ledger, shared parser/validator, fixtures wired into eval.
- 品牌锁与面部一致性可执行校验（issue #6 P1 ⑤）：`scripts/check_brand_lock.py`（运行时直读 `vertciti-brand-bundle.json`，校验手写色值/偏离字体/字标写法）；`scripts/check_face_consistency.py`（anchor 恰好 1 张、一图不兼两角、参考图存在性与 SHA-256 登记比对；一图一记录字段仅预留接口）。此前两项均只有散文规则、无任何检查。 / Executable brand-lock and face-consistency checkers (were prose-only).
- AI 标识与声明字段（issue #6 P0）：SKILL.md 交付格式第七节 + `references/rotation-rules.md` 台账条目字段 schema 草案 v0.1（`ai_generated` / `ai_disclosure_text` / `ai_disclosure_method` / `ai_disclosure_basis`），对齐《人工智能生成合成内容标识办法》、小红书 AI 标识规则与 EU AI Act Art. 50。 / AI disclosure fields in the Step 5 delivery format and the draft ledger-entry schema.
- `references/prompt-standards.md` 机读规则附表 v0.1：面部禁词、年龄模式、互斥对、B 级触发词（源规则的机读化转写，供工具直读）。 / Machine-readable rule appendix in prompt-standards.md.
- `docs/PRODUCT.md` 产品一页纸；本 `CHANGELOG.md`。 / Product one-pager and this changelog.
- README：状态说明、`## 安全 / Security`、`## 许可证 / License` 小节。 / README status line, Security and License sections.
- vertciti 工程基线：`.editorconfig`、`CODEOWNERS`、Dependabot（github-actions）、gitleaks 密钥扫描、OpenSSF Scorecard workflow（2026-10-22）。 / Engineering baseline (editorconfig, CODEOWNERS, Dependabot, gitleaks, Scorecard).
- `scripts/validate_skill.py` + `tests/`：skill 包校验与单元测试（frontmatter 规范、引用路径存在、SKILL.md 内联强制短语/否定词带与 prompt-standards.md 一致、evals.json 格式）。 / Skill-package validator with unit tests.
- `evals/evals.json`：7 例评测集（skill-creator 格式，带断言）。 / 7-case eval set.
- CI `tests.yml`：每个 PR 跑单元测试与 skill 包校验。 / Unit-test and skill-validation CI.

### Changed
- SKILL.md frontmatter 改为 Agent Skills 规范字段（name / description / license / compatibility / metadata），原 `version`、`user_invocable`、`triggers`、`requires`、`inputs`、`safety` 移入 `metadata`；版本号 1.1.0 与正文「v1.1 新增三章」对齐（尚未打 tag）。description 补英文触发词。 / Spec-compliant frontmatter; version 1.1.0.
- Step 4 增加重生成上限：同一方案连续 3 次整单打回即停，回 Step 2 改方案并记录次数与成本。 / Regeneration is capped at 3 full rejections per plan.
- `evals/smoke-01.md` 与 `evals/work/*.txt` 删除人物外貌/年龄描述与本地照片文件名（替换为中性说明）。 / Personal appearance details and photo filenames redacted from eval records.

### Fixed
- demo 输入校验：非 JSON 对象 / JSON 损坏 / 必填项非字符串一律以退出码 2 拒绝（此前抛 traceback 或放行）。 / Bad input is refused with exit 2 instead of a traceback.
- 输入字段单行化并去掉 `#`，`scene` 里的换行不能再伪造「## 终判：通过」等段落。 / Inputs can no longer forge report sections.
- 场景文字写明白底标准照时直接打回（事故级，不依赖台账或调用者另设 `uses_standard_portrait`）；写明白底/棚拍且未给大类时按「白底棚拍」判定。 / White-background portrait in the scene text is rejected on its own.
- 样例输出不再带本机绝对台账路径、`input.json` 固定日期，`demo/output/` 可在任何机器上逐字复现；`eval.sh` 先比对再重写样例。 / Sample output is reproducible.
- SKILL.md / prompt-standards.md「按年龄写皮肤」与「prompt 模板铁律」1 冲突、rotation-rules.md 白底三禁第 3 条歧义；SKILL.md「管线 403」改为如实说明由外部管线执行。 / Rule contradictions resolved.
- demo 按 skill 规则飞行（issue #6 P0）：`demo/run.py` 运行时直读 references 的强制短语、固定否定词带与禁用词表 v1.0，删除内置的另一套否定词/禁用词副本；冲突审计、面部描述检查、B 级严审均为真判定（原冲突审计为写死的"通过"，原 demo 自身 prompt 含禁用词 `cinematic` 与面部/年龄描述）；`demo/eval.sh` 在 prompt 被打回时真 FAIL（原实现被拒仍打印 PASS），并内置两个"必被拒"回归夹具。 / Demo now loads its rules from references at runtime; eval truly fails on rejection.
- gitleaks workflow 增加 `pull-requests: read` 权限，避免在 PR 上列取提交时 403。 / gitleaks workflow gains `pull-requests: read` so PR scans don't 403.
- SKILL.md 规则矛盾（issue #6 超出条款 6）：Step 3-5「视线不直视镜头」改为随脸角度预设（摆拍可给镜头）；品牌风格词 "dark cinematic" 与禁用词 `cinematic` 的关系写明（风格词不进 prompt）；「拼版 + 分层 PNG」标明为渲染阶段交付，不替代三部分输出契约。 / Rule contradictions resolved.

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

[Unreleased]: https://github.com/HUIIIM/founder-visual-director/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/HUIIIM/founder-visual-director/releases/tag/v1.1.0
