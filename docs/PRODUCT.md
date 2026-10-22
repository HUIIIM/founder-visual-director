# founder-visual-director — 产品一页纸

> 状态：active（early）· 版本：1.0.0 · 更新：2026-10-22
> 所属：[vertciti](https://vertciti.com) — 一家公司，一个人生。

## 一句话
创始人（Miao）的内容生产流程用它把一条场景需求变成三件套：可执行的生图 prompt、全尺寸真实感 QA 检查表、素材轮换合规结论——在出图和发布之前把关。

*One line (EN):* A Claude skill that turns a founder-photo scene brief into an executable image prompt, a photorealism QA checklist and a rotation-compliance verdict, before anything ships.

## 解决什么问题
- 痛点：AI 生成的创始人配图反复以三种方式失败——脸部失真、物理错误（手、反光、光源方向）、视觉重复（相邻帖子同服装/同造型/同背景）。每篇小红书 / IG / LinkedIn 封面都会遇到；一旦发出，损失的是人设可信度。发布频率与代价的量化：未确认（TBD）。
- 现在的替代做法：直接描述场景让模型自由发挥，靠人凭记忆检查。问题是模型默认输出训练数据的"平均脸/平均场景"，而人会忘记最近发过什么——`evals/smoke-01.md` 的真实 dry-run 就拦下了一次与第 9 篇同场景大类、14 天内重复的违规。

## 给谁
- 首要用户：Miao 本人（SKILL.md 明确以"创始人（Miao）"为服务对象），以及在其工作区内调用该 skill 的 Claude agent。
- 不是给谁：需要通用人像/商业摄影生成的团队；需要真正渲染图片的人（本 skill 只到 prompt 与检查表，渲染走外部生图管线）；涉及真实可识别人物（名人合影、晚宴等）的场景——SKILL.md 规定一律转 B 级严审，不在本 skill 内放行。

## 怎么用（三步）
1. 准备场景需求，满足输入契约：主题/平台、场景需求、画幅、叙事调性（缺项时 skill 会先问，不脑补）。示例见 `demo/input.json`。
2. 在 Claude 中调用 skill（或运行最小切片 `python3 demo/run.py`，零外部依赖），得到 `prompt.txt`、`checklist.md`、`rotation.md` 三件套。
3. 按结论处置：轮换"违规"则换场景大类或推迟；QA 任一红线 fail 则整张重生成；发布前仍需全尺寸人工目检。

## 为什么是我们（差异化）
| 维度 | 我们 | 常见替代 |
|---|---|---|
| 重复检测 | 对照素材台账查相邻 3 篇、14 天冷却、白底头像禁令，给出 通过/条件通过/违规 | 凭记忆 |
| 真实感 QA | 脸角度三规则 → 人体比例十项 → 真实感 → 背景专项，逐项判定；红线 fail = 整张重来 | 看缩略图"感觉还行"，局部修补 |
| 输入纪律 | 缺项先问，不许脑补 | 模型自行补全场景 |
| prompt 规范 | 固定否定词带 + 禁用词 grep（限正向 prompt）+ 冲突审计 | 自由文本 prompt |

## 证据
- 测试：无单元测试套件。`demo/eval.sh` 为一键 PASS/FAIL 契约检查（三件套文件齐全 + 必需字段存在），2026-10-22 本地运行结果：`PASS`。CI 中未运行该检查（现有 workflow 仅 gitleaks 与 OpenSSF Scorecard）。
- 真实运行：`demo/output/`（样例输入产出的三件套）；`evals/smoke-01.md`（2026-10-03 一次完整 dry-run 记录，结论为"skill 本体 pass、输入场景违规被拦下"）。
- 不能证明的：生成图片的真实感提升幅度、对发布效果的影响、误判率——均无数据，未确认（TBD）。demo 不渲染图片；轮换检查依赖本地台账 `used-visual-ledger.md`，仓库内不含该台账，缺失时 demo 按降级规则输出"台账待补"。

## 边界与风险
- 不做：图片渲染；真实可识别人物场景（转 B 级严审）；替代人类艺术指导——全尺寸人工目检仍是发布红线。
- 已知限制：仅 1 份冒烟评估；demo 只到 prompt 级；依赖伴生 skill `founder-visual-studio` 与视觉规范 v1.6/v1.7（不在本仓库内）；`demo/README.md` 提到的 `demo/run.sh` 在仓库中不存在（应使用 `python3 demo/run.py`）。
- 安全与隐私：skill 本身不上传数据；输入场景与台账均为本地文件，由调用者的 Claude 环境读取。所用模型/生图服务的数据处理取决于调用者自己的配置，未确认（TBD）。CI 中有 gitleaks 密钥扫描。

## 与其他 vertciti 产品的组合
- 与 `founder-visual-studio`：SKILL.md 将其列为依赖（requires），负责分镜/拍摄规划，本 skill 负责导演把关与 QA。具体分工细节：未确认（TBD）。
- 其他组合：未确认（TBD）。

## 路线图
| 阶段 | 内容 | 退出标准 |
|---|---|---|
| Now | `evals/` 冒烟评估扩充，加入并排相似度判断 | 未确认（TBD） |
| Next | 轮换台账自动化：新需求与已发布素材日志机器比对 | 未确认（TBD） |
| Later | 平台扩展规则（TikTok）并入轮换合规 | 未确认（TBD） |

（内容取自 README Roadmap；退出标准尚未定义。）

## 衡量指标
- 北极星：未确认（TBD）。候选：发布前被拦下的轮换/真实感事故数。
- 护栏：未确认（TBD）。候选：`demo/eval.sh` 持续 PASS；发布后发现的重复/失真事故数为 0。
