# founder-visual-director demo

最小可运行切片（30 秒内跑完，零外部依赖）。

## 输入
`input.json`：主题/平台、场景需求、画幅、叙事调性（与 SKILL.md 输入契约一致）。

## 运行
```bash
bash demo/run.sh   # 或 python3 demo/run.py
bash demo/eval.sh  # 输出 PASS/FAIL
```

## 输出（demo/output/）
- `prompt.txt`：终版生图 prompt（含正向 prompt＋固定否定词＋禁用词 grep 结果＋冲突审计结论）
- `checklist.md`：QA 检查表骨架（脸角度三规则→人体比例十项→真实感→背景专项）
- `rotation.md`：轮换合规检查结论（通过/条件通过/违规＋处置建议）

## 诚实边界
本 demo 只到 **prompt 级**：验证输入契约→三部分交付物的链路可运行。
真实图片渲染走 media 生图管线（需真人目检，不在 30 秒 demo 范围内）。
轮换检查对照 `deliverables/ops/used-visual-ledger.md`；台账缺失时按 skill 降级规则标注"台账待补"。
