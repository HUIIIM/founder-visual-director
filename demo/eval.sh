#!/bin/bash
# founder-visual-director eval: 一键 PASS/FAIL，零外部依赖
set -u
DEMO="$(cd "$(dirname "$0")" && pwd)"
python3 "$DEMO/run.py" || { echo "FAIL: run.py 执行失败"; exit 1; }
ok=1
[ -f "$DEMO/output/prompt.txt" ] || ok=0
[ -f "$DEMO/output/checklist.md" ] || ok=0
[ -f "$DEMO/output/rotation.md" ] || ok=0
grep -q "正向 prompt" "$DEMO/output/prompt.txt" || ok=0
grep -q "固定否定词" "$DEMO/output/prompt.txt" || ok=0
grep -q "禁用词 grep 结果" "$DEMO/output/prompt.txt" || ok=0
for s in "脸角度三规则" "人体比例十项" "真实感" "背景专项"; do
  grep -q "$s" "$DEMO/output/checklist.md" || ok=0
done
grep -Eq "通过|违规" "$DEMO/output/rotation.md" || ok=0
if [ "$ok" = 1 ]; then echo "PASS: 三部分交付物齐全，契约字段完整"; exit 0
else echo "FAIL: 交付物缺失或契约字段不全"; exit 1; fi
