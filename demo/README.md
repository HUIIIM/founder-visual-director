# founder-visual-director demo

最小可运行切片（30 秒内跑完，零外部依赖）。

## 输入
`input.json`：主题/平台、场景需求、画幅、叙事调性（与 SKILL.md 输入契约一致）。

## 运行
```bash
python3 demo/run.py            # 可跟自定义 input.json 路径
bash demo/eval.sh              # 输出 PASS/FAIL；可跟自定义 input.json（被打回即 FAIL）
```

`run.py` 退出码：0 通过 / 2 输入缺项 / 3 规则打回 / 4 规则读取失败。
规则（强制短语、固定否定词带、禁用词表、面部禁词、互斥对、B 级触发词）在运行时直读
`references/prompt-standards.md`，demo 内不存副本；规则集不完整时拒绝放行（退出码 4）。
`eval.sh` 除结构校验外，内置"必被拒"回归夹具（B 级场景、禁用词，及 P1 台账/品牌锁/面部
一致性夹具），夹具未被拒即 FAIL。
输出目录可用 `FVD_DEMO_OUT` 覆盖，台账路径可用 `FVD_LEDGER_PATH` 覆盖。
`input.json` 除输入契约四项外可带结构化候选字段（`platform` / `post_no` / `date` /
`scene_category` / `outfit` / `styling` / `asset_id` / `asset_grade` /
`uses_standard_portrait`），供轮换预检真读判定；`date` 缺省取当天。

## 轮换预检（真读台账）与校验脚本（issue #6 P1）

`run.py` 的轮换段调用 `scripts/check_rotation.py`：真读台账条目判定相邻 3 篇 /
14 天同大类 / 冷却期 / S 级月度上限 / 白底三禁，台账格式见
`references/ledger-format.md`（v1.0）；台账缺失/不可解析时输出「无法判定（降级）」，
绝不以存在性冒充通过。另有独立校验脚本（仓根 `scripts/`）：

```bash
python3 scripts/check_rotation.py --ledger <台账.md> --candidate <候选.json>
python3 scripts/check_brand_lock.py <prompt/交付物文本>   # 色值/字体/字标 vs brand bundle
python3 scripts/check_face_consistency.py <台账.md>       # anchor 齐备 + 参考图哈希比对
```

样例台账与自测夹具在 `demo/fixtures/`（见该目录 README）。

## 输出（demo/output/）
- `prompt.txt`：终版生图 prompt（含正向 prompt＋固定否定词带＋禁用词 grep 结果＋面部描述检查＋冲突审计结论＋B 级严审检查＋AI 标识与声明＋终判）
- `checklist.md`：QA 检查表骨架（脸角度三规则→人体比例十项→真实感→背景专项）
- `rotation.md`：轮换合规检查结论（通过/条件通过/违规＋处置建议）

## 诚实边界
本 demo 只到 **prompt 级**：验证输入契约→三部分交付物的链路可运行。
真实图片渲染走 media 生图管线（需真人目检，不在 30 秒 demo 范围内）。
轮换检查真读本地素材台账 `used-visual-ledger.md`（不在本仓库内，格式见
`references/ledger-format.md`）；台账缺失时按 skill 降级规则标注"无法判定（台账待补）"，
不冒充通过。品牌锁与面部一致性校验是文本/登记级机读核验，不替代全尺寸目检与质检终审。
