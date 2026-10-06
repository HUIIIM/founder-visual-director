# 冒烟评估 smoke-01：完整 dry-run

> 评估对象：skill `founder-visual-director` v1.0.0
> 评估方式：真实执行（非纸面）。输入真实场景需求，按 SKILL.md 工作流跑完全程，
> 输出三部分交付物，并把 QA 检查表实际走查一遍、轮换检查对照真实台账与实物。

## 输入场景

- 主题/平台：小红书第 10 篇封面
- 场景需求：城市晨跑后拉伸
- 画幅：3:4
- 叙事调性：生活感

## 前置证据（Step 1 轮换预检所用）

**台账**：`~/workspace/vertcity/deliverables/ops/used-visual-ledger.md`
- 状态：滞后。仍记第 8 篇当前版为 v3（"曼哈顿图书馆"），实际已出到 v9（书房夜景实物已目检）；
  第 9 篇 v1/v2/v3 均未登记；第 1–6 篇待补录（台账自注 2026-10-03 前回填）。
- 按 skill 降级规则：以实物为准检查，结论标注"台账待补"。

**近三篇实况**（实物目检 + 台账交叉）：

| 篇 | 场景大类 | 服装/造型 | 依据 |
|---|---|---|---|
| 第 7 篇 | 室内生活摆拍 | 黑T | 实物 post7-01-cover.jpg 目检（台账记当前版 v5-1 为"深夜书房"，未目检，按台账采信） |
| 第 8 篇 | 室内书房（夜景） | 深色针织/眼镜 | 实物 post8-cover-v9.jpg 目检 |
| 第 9 篇 | 户外运动（中央公园晨跑后拉伸） | 黑运动夹克 + 白T | 实物 xhs-post9-cover-v3.jpg 目检，制作时间 2026-10-03 |

## 输出一：生图 prompt

**定调**：清晨城市公园的真实训练瞬间，生活感抓拍美学，0.5 秒抓住"自律的人"。

**脸角度预设**：摆拍——眼神给镜头，身体舒展做拉伸动作，头身夹角 <20°；
视线落点答案：镜头（ deliberate posed portrait）。

**正向 prompt**：

```
Photorealistic full-scene photograph, 3:4 vertical, of an East Asian man in his 30s
with short black hair and thin metal-frame glasses, doing a post-run shoulder stretch
on a park path in the early morning. Deliberate posed portrait: body in a relaxed
stretch pose, one arm across the chest held by the other hand, face turned toward
camera, head-to-torso angle under 20 degrees, eyes looking directly into the lens.
7.5 heads tall, natural adult proportions, no fashion-model elongation.
Shot on 85mm f/1.8 lens, subject 3 meters from camera, eye-level angle,
seamless neck-to-shoulder transition. Single main light source: low warm morning
sun from the left through the trees, soft rim light on hair and shoulder.
Background: city park with bokeh, out-of-focus joggers, a wooden bench and a lamp
post; two lived-in details: a half-finished water bottle on the bench and fallen
leaves on the path. Visible skin pores and fine lines, unretouched skin, natural
facial asymmetry. Subtle film grain in the shadows, slight vignette, blacks lifted
but not crushed. Natural clothing wrinkles following gravity.
```

**固定否定词带**：
```
plastic skin, cgi, perfect skin, symmetrical face, beauty filter,
oversized head, elongated neck, narrow shoulders, floating head, wide-angle distortion
```

**禁用词 grep 结果**：正向 prompt 零残留（见"执行记录"第 3 步：首次全串 grep 误报
`perfect skin`，原因为固定否定词带本就含有该词；修正为仅扫描正向 prompt 后通过）。

**冲突审计结论**：无冲突（early morning + 85mm f/1.8 实拍机位无互斥；单主光源；
摆拍预设与 "posed portrait" 逻辑一致，无抓拍/摆拍拼贴）。

## 输出二：QA 检查表（走查对象：xhs-post9-cover-v3.jpg，同场景现存图）

> 说明：走查在可视分辨率下进行；凡缩略图不可辨的项记"需 100% 复核"，不硬判 pass。

**脸角度三规则**

| # | 项 | 结论 | 依据 |
|---|---|---|---|
| F1 | 头–身夹角 | pass | 身体正对镜头方向拉伸，脸朝镜头，夹角 ≤30° |
| F2 | 视线落点 | pass | 眼睛看镜头；摆拍成立，落点 = 镜头 |
| F3 | 动量一致性 | pass | 拉伸为静态动作，摆拍逻辑自洽，无动量冲突 |

**人体比例十项**

| # | 项 | 结论 | 依据 |
|---|---|---|---|
| P1 | 头身比 | n/a | 半身构图，不适用全身测量 |
| P2 | 头占画面比 | pass（下限边缘） | 头高约 19% 画面高度；半身像区间 28–35%，偏差 9pp < 10pp |
| P3 | 眼睛垂直位置 | pass（初步） | 眼线约在头顶–下巴中点 |
| P4 | 三庭 | pass（初步） | 大致三等分 |
| P5 | 眼间距与鼻宽 | pass（初步） | 比例正常 |
| P6 | 肩宽 | 需 100% 复核 | 拉伸姿势手臂遮挡肩部，难测 |
| P7 | 颈部 | pass（初步） | 颈–肩衔接自然，无浮头 |
| P8 | 耳朵 | pass（初步） | 双耳可见、对称 |
| P9 | 透视畸变 | pass（初步） | 鼻子比例自然 |
| P10 | 对称与完整 | pass（初步） | 衣领–颈–肩过渡连续 |

**真实感 100% 放大项**

| # | 项 | 结论 | 依据 |
|---|---|---|---|
| A1 | 皮肤 | 需 100% 复核 | 毛孔不可辨（分辨率限制） |
| A2 | 眼睛 catchlight | 需 100% 复核 | 反光点不可辨 |
| A3 | 牙齿 | n/a | 闭嘴微笑 |
| A4 | 手 | pass（初步，需 100% 复核关节） | 双手交叉，手指数量正常、弯曲合理 |
| A5 | 眼镜 | 需 100% 复核 | 镜腿连接看似合理，镜片反光一致性待放大查 |
| A6 | 头发 | pass（初步） | 发丝自然，发际线正常 |
| B7 | 光影一致性 | **疑问** | 背景主光源 = 左后方树林晨光（逆光轮廓）；脸部受光偏正面柔和。脸上的光与背景是否为同一光源，存疑 |
| B8 | 反射一致性 | 需 100% 复核 | 眼镜轻微反光，内容待放大核对 |
| B9 | 透视与功能 | pass（初步） | 长椅/路灯/跑者功能合理 |
| C10 | 不过完美 | **疑问** | 脸部偏光滑对称，有轻微"平均脸"感 |
| C11 | 可控瑕疵 | 需 100% 复核 | 暗部颗粒不可辨（分辨率限制） |

**背景物理项**

| # | 项 | 结论 | 依据 |
|---|---|---|---|
| E12 | 存在理由 | pass | 树木/长椅/跑者/路灯，拒绝样板间 |
| E13 | 虚化物理 | pass（初步） | 光斑圆形，背景跑者虚化有梯度 |
| E14 | 背景光影一致 | **疑问** | 同 B7：背景逆光 vs 脸部正面光，是否为同一光源存疑 |
| E15 | 物体逻辑 | 需 100% 复核 | 虚化中跑者四肢难辨 |
| E16 | 拒绝假大空 | pass | 无硬堆奢华元素 |

**QA 小结**：脸角度三规则全 pass；比例十项 8 pass（初步）+ 1 边缘 pass + 1 待复核；
实质疑问 1 个（B7/E14 光源一致性，C10 为伴随疑问）。按"存疑即打回"纪律：
**打回做 100% 放大复核**，重点查脸部受光方向与背景晨光的对应关系。

## 输出三：轮换合规检查

| 检查项 | 结论 |
|---|---|
| 相邻 3 篇（7/8/9）场景大类 | 第 9 篇 = 户外运动；输入 = 户外运动（城市晨跑后拉伸）→ **重复** |
| 同一场景大类 14 天 | 第 9 篇 v3 制作于 2026-10-03，输入若执行 → **14 天内重复** |
| 服装/造型 | 第 9 篇黑运动夹克 + 白T；输入未指定，默认延续 → 高重复风险 |
| 白底禁令 | 不涉及 → pass |
| 台账状态 | 滞后（第 8 篇 v9、第 9 篇 v1–v3 未登记）→ 记"台账待补"，本次按实物判定 |

**结论：违规。**

- 证据：第 9 篇 v3（`your_files/founder-visual-batch-2026-10-03/xhs-post9-cover-v3.jpg`，
  2026-10-03 制作）已占用"户外运动 / 城市晨跑后拉伸"场景大类；第 10 篇与第 9 篇相邻，
  同场景大类重复违反"相邻 3 篇不重复"；且同场景 14 天内重复违反冷却规则。
- 处置建议：更换场景大类。A 级替代候选（避开近三篇已占用的室内生活摆拍 / 室内书房 / 户外运动）：
  1. 城市街头清晨散步（城市街景大类，grind 叙事）；
  2. 游艇甲板（旅行度假大类，配奋斗/建造叙事，奢品镜头回答"他凭什么"）；
  3. 名表 / 工作细节特写（商务配饰大类，教育性 caption）。
  另：小红书一天一篇，第 10 篇排期须与第 9 篇错开至少 1 天。
- prompt 处置：输出一的 prompt 标注"待场景确认"，不作为可投产版本交付。

## 执行记录

| 时间 (EDT 2026-10-03) | 动作 | 结果 |
|---|---|---|
| 00:42 | 定位内容源 4 份（视觉规范 v1.6 / 真实感标准 v1.2–v1.3 / 资产策划案 / 大师计划 v1.1 + 脸角度亲研笔记） | 4 份齐 |
| 00:43 | 查近三篇实况：your_files 实物 + used-visual-ledger.md + memory 交叉 | 发现台账滞后（第 8 篇 v9、第 9 篇未登记） |
| 00:43 | 目检第 7 篇封面（post7-01-cover.jpg）、第 9 篇 v3（xhs-post9-cover-v3.jpg）、第 8 篇 v9（post8-cover-v9.jpg） | 三篇场景大类确认 |
| 00:44 | 按 skill Step 2 写脸角度预设（摆拍，视线落点 = 镜头） | 完成 |
| 00:44 | 按 skill Step 3 写正向 prompt + 固定否定词带 | 完成 |
| 00:44 | 禁用词 grep（首次：全串扫描，含否定词带） | 误报 `perfect skin`——固定否定词带本就含该词 |
| 00:44 | 修正：grep 范围限定为正向 prompt；强制短语 / 否定词带逐项核对 | 正向零残留；强制短语 4/4；否定词带 10/10 |
| 00:44 | 冲突审计（人工四项） | 无冲突 |
| 00:45 | QA 检查表走查 xhs-post9-cover-v3.jpg（脸角度 3 + 比例 10 + 真实感 11 + 背景 5 = 29 项） | 1 个实质疑问（光源一致性）→ 按纪律打回 100% 复核 |
| 00:45 | 轮换检查：场景大类判定 + 相邻三篇 + 14 天规则 | **违规**：与第 9 篇 v3 同场景大类 |
| 00:45 | 形成处置建议（3 个 A 级替代场景 + 排期提醒 + prompt 标注待确认） | 完成 |

**环境插曲**：首次 grep 时 `/tmp` 512M tmpfs 写满导致 heredoc 截断、检查误报 MISS；
改用 home 分区（`evals/work/`）重做后全部通过。此为已知环境特性（AGENTS.md 已有记录），
非 skill 缺陷。

## 判定

- **skill 本体：pass**。输入 → 三部分输出全程可跑通；prompt 含全部强制机制且检查项真实执行；
  QA 检查表 29 项逐项可判定；轮换检查基于真实台账 + 实物目检给出结论。
- **本次 dry-run 输入场景：fail（违规）**——这正是 skill 存在的价值：
  若没有 Step 1 轮换预检，"城市晨跑后拉伸"将与 2026-10-03 刚制作的第 9 篇 v3 同场景连发，
  违反"相邻 3 篇不重复"与"同一场景 14 天不重复"两条铁律。
- **关键发现**（已回写 skill）：
  1. 禁用词 grep 必须限定在正向 prompt 范围（固定否定词带含禁用词是故意为之）——
     SKILL.md Step 3 已修正措辞。
  2. used-visual-ledger.md 滞后（第 8 篇 v9、第 9 篇 v1–v3 未登记）——记台账补录待办，
     skill 内已含"台账滞后降级规则"。
  3. QA 走查在第 9 篇 v3 上发现 1 个实质疑问（脸部正面光 vs 背景逆光是否为同一光源）——
     按"存疑即打回"纪律打回 100% 放大复核；该疑问与 v2 事故同属"光的诚实"范畴，
     建议纳入下次质检必查。
