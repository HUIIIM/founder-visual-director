# 台账正式格式 / Ledger Format v1.0

> 地位：本文件是素材使用台账的**正式格式定义**（2026-10-27，issue #6 P1 落地）。
> 字段名全部沿用 `references/rotation-rules.md` 的 schema 草案 v0.1（其注记要求
> 「字段名不得另起一套」），v1.0 只做三件事：定机器可读载体、补结构化参考图字段、
> 定校验与降级语义。判定规则（相邻 3 篇 / 14 天 / 冷却期 / 白底三禁 / S 级上限）
> 仍以 `rotation-rules.md` 为唯一来源，工具运行时直读，不在本文件复写数值。

## 1. 文件与载体

- 台账文件：`used-visual-ledger.md`，由调用方在本地维护（不在本仓库内）；
  路径可经环境变量 `FVD_LEDGER_PATH` 指定。工具亦接受 `.json` 文件（条目数组本体）。
- 机器可读区：markdown 文件中**唯一**一个 ` ```json ` 代码块，内容为条目对象数组；
  代码块之外的文字是人读注记，工具忽略。无代码块 / JSON 不可解析 = 整本无法判定（见 §5）。
- 编码 UTF-8；日期一律 `YYYY-MM-DD`；每次使用后 24h 内登记（SKILL.md 红线），
  先登记候选条目为「待发」，发布后改「已发布」并补 `date_published`。

## 2. 条目字段（v1.0）

沿用 v0.1 字段（名与语义不变）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `ledger_id` | string | 是 | 条目唯一 ID（如 `xhs-2026-010`） |
| `platform` | string | 是 | 平台（小红书 / IG / LinkedIn 等） |
| `post_no` | string | 是 | 篇号 / 发布序号 |
| `date_made` | date | 是 | 制作日期 |
| `date_published` | date | 状态=已发布时必填 | 发布日期；生效日期取制作/发布孰早 |
| `scene_category` | string | 是 | 场景大类（取值见 rotation-rules.md 大类表，新大类先登记） |
| `outfit` | string | 是 | 服装 |
| `styling` | string | 是 | 造型 |
| `asset_grade` | enum | 是 | S / A / B |
| `asset_id` | string | 是 | 素材资产 ID（冷却期按此 ID 计算） |
| `model_id` | string | 是 | 模特资产版本（如 `miao-v1`），无则填 `none` |
| `reference_roles` | string | 否 | 参考图角色摘要（人读，如 `anchor=path, style=path`） |
| `status` | enum | 是 | 已发布 / 待发 / 已退役（轮换判定只计已发布+待发） |
| `ai_generated` | bool | 是 | AI 标识组：是否为 AI 生成合成内容 |
| `ai_disclosure_text` | string | ai_generated=true 时必填 | 声明文本 |
| `ai_disclosure_method` | enum | 是 | `platform_declaration` / `c2pa` / `caption` / `none` |
| `ai_disclosure_basis` | string | ai_generated=true 时必填 | 口径指针（规则/法规名） |

v1.0 新增字段（补全机读所需，不改 v0.1 字段名）：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `references` | array | 涉及参考图的生成必填 | 结构化参考图登记，每项 `{file, role, sha256}`：`file` 为路径（相对台账文件所在目录或绝对路径），`role` ∈ anchor/style/layout/negative，`sha256` 为文件 SHA-256（64 位十六进制）。面部一致性校验（scripts/check_face_consistency.py）以此为据：每条恰好 1 张 anchor、一图不兼两角、文件须存在且哈希一致 |
| `output_file` | string | 否（预留） | **一图一记录候选的接口预留**：产物文件路径。与 `image_sha256` 成对出现时，校验工具按参考图同一方式验其存在性与哈希；本版不强制登记 |
| `image_sha256` | string | 否（预留） | 同上，产物文件的 SHA-256 |

## 3. 候选字段（轮换预检的待检对象）

预检对象是「本次候选交付」，以 JSON 对象提供（`scripts/check_rotation.py --candidate`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `platform` / `date` | string / date | 平台与候选日期（制作/计划发布孰早） |
| `scene_category` / `outfit` / `styling` | string | 与条目同名同义 |
| `asset_id` / `asset_grade` | string / enum | 候选拟用资产 |
| `uses_standard_portrait` | bool | 是否使用白底标准照作内容配图（true = 事故级违规） |

## 4. 机器校验（已实现）

- `scripts/check_rotation.py`：轮换预检真读台账——相邻 3 篇 / 14 天同大类 / 冷却期 /
  S 级月度上限 / 白底三禁，逐项出证据行；规则数值运行时直读 rotation-rules.md。
- `scripts/check_face_consistency.py`：anchor 齐备与唯一、一图不兼两角、参考图存在性
  与 sha256 登记比对、`reference_roles` 摘要与结构化登记一致性。
- `scripts/ledger_lib.py`：两脚本共用的解析与字段校验（本文件 §2 的必填/枚举/日期规则）。
- 样例与自测夹具在 `demo/fixtures/`（合规/违规台账各一、候选各一、面部违规台账一），
  `demo/eval.sh` 已把关键夹具纳为回归断言。

## 5. 降级语义（诚实规则）

- 台账缺失或不可解析：结论只能是「无法判定（降级）」，检查不执行，**不得输出「通过」**；
  按 SKILL.md 降级规则标注「台账待补」并留人工判定痕迹。
- 条目字段有缺陷：缺陷条目逐条列出并排除出判定，结论上限为「条件通过」并标注不确定性。
- 候选字段不全：受影响检查标注无法判定，结论上限为「条件通过」。
- 凡「已发布」的图永久退役，绝不二次使用（含裁剪、调色、跨平台复用）——此为登记纪律，
  由轮换预检的相邻/冷却检查与人工复核共同把守。

## 6. 备份说明（OPS）

台账是本产品唯一状态（issue #6 OPS-1）。它仍是单文件、由调用方本地维护：
调用方应把台账文件纳入其自有备份节奏（如随工作区周备份），并在迁移/换机时
先恢复台账再出图；台账丢失时按 §5 降级处理、先按实物重建登记再恢复自动判定。
本仓库内的 `demo/fixtures/` 只是格式样例，不是实物台账的备份。
