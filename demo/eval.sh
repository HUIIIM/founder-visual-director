#!/bin/bash
# founder-visual-director eval: PASS/FAIL 必须反映 demo 的真实判定。
# - run.py 拒绝（退出码非 0：缺项 2 / 打回 3 / 规则读取失败 4）-> eval 立即 FAIL。
# - 默认模式另跑两个"必被拒"回归夹具（B 级场景 / 禁用词），夹具未被拒 -> FAIL。
# 用法：bash demo/eval.sh [input.json]（给了自定义输入时，输出写入临时目录，不污染 demo/output）
set -u
DEMO="$(cd "$(dirname "$0")" && pwd)"
INPUT="${1:-$DEMO/input.json}"
TMPD=""
if [ "$INPUT" != "$DEMO/input.json" ]; then
  TMPD="$(mktemp -d)"
  export FVD_DEMO_OUT="$TMPD/out"
fi
OUTDIR="${FVD_DEMO_OUT:-$DEMO/output}"

python3 "$DEMO/run.py" "$INPUT"
rc=$?
if [ $rc -ne 0 ]; then
  echo "FAIL: run.py 退出码 $rc（输入缺项/规则打回/规则读取失败），见上方终判"
  [ -n "$TMPD" ] && rm -rf "$TMPD"
  exit 1
fi

ok=1
note() { echo "FAIL: $1"; ok=0; }
[ -f "$OUTDIR/prompt.txt" ] || note "prompt.txt 缺失"
[ -f "$OUTDIR/checklist.md" ] || note "checklist.md 缺失"
[ -f "$OUTDIR/rotation.md" ] || note "rotation.md 缺失"
P="$OUTDIR/prompt.txt"
for s in "正向 prompt" "固定否定词带" "禁用词 grep 结果" "面部描述检查结果" "冲突审计结论" "B 级严审检查" "AI 标识与声明" "终判：通过"; do
  grep -q "$s" "$P" || note "prompt.txt 缺字段/结论：$s"
done
# 规则直读证据：强制短语与固定否定词带必须与 references/prompt-standards.md 原文一致
grep -qF "7.5 heads tall, natural adult proportions, no fashion-model elongation" "$P" || note "强制短语 1 未逐字出现"
grep -qF "shot on 85mm f/1.8 lens, subject 3 meters from camera, eye-level angle" "$P" || note "强制短语 2 未逐字出现"
grep -qF "seamless neck-to-shoulder transition" "$P" || note "强制短语 3 未逐字出现"
grep -qF "plastic skin, cgi, perfect skin, symmetrical face, beauty filter, oversized head, elongated neck, narrow shoulders, floating head, wide-angle distortion" "$P" || note "固定否定词带与 references 原文不一致"
grep -q "无命中 -> 通过" "$P" || note "存在未通过的检查项"
if grep -q "打回" "$P"; then note "prompt.txt 含打回字样但 run.py 未拒绝（判定不一致）"; fi
# AI 标识/声明字段（交付格式第七节，台账同名字段）
for f in "ai_generated" "ai_disclosure_text" "ai_disclosure_method" "ai_disclosure_basis"; do
  grep -q "$f" "$P" || note "prompt.txt 缺 AI 声明字段：$f"
  grep -q "$f" "$OUTDIR/rotation.md" || note "rotation.md 台账条目缺字段：$f"
done
for s in "脸角度三规则" "人体比例十项" "真实感" "背景专项"; do
  grep -q "$s" "$OUTDIR/checklist.md" || note "checklist.md 缺小节：$s"
done
if grep -q "结论：违规" "$OUTDIR/rotation.md"; then note "轮换结论为违规"; fi

# 回归夹具（仅默认模式）：以下输入必须被 run.py 拒绝，否则判定链失效
if [ -z "$TMPD" ]; then
  FIX="$(mktemp -d)"
  cat > "$FIX/bad-b.json" <<'EOF'
{"aspect":"3:4","mood":"生活感","scene":"绝密 晚宴 与名人合影","theme_platform":"小红书第 10 篇封面"}
EOF
  cat > "$FIX/bad-cinematic.json" <<'EOF'
{"aspect":"3:4","mood":"cinematic 氛围","scene":"城市晨跑后拉伸","theme_platform":"小红书第 10 篇封面"}
EOF
  for f in bad-b bad-cinematic; do
    FVD_DEMO_OUT="$FIX/out-$f" python3 "$DEMO/run.py" "$FIX/$f.json" > "$FIX/$f.log" 2>&1
    frc=$?
    if [ $frc -eq 0 ]; then note "回归夹具 $f 未被拒绝（run.py 退出码 0）"; fi
    grep -q "终判：打回" "$FIX/$f.log" || note "回归夹具 $f 输出无打回终判"
  done
  rm -rf "$FIX"
fi

[ -n "$TMPD" ] && rm -rf "$TMPD"
if [ "$ok" = 1 ]; then echo "PASS: 三部分交付物齐全，规则直读校验与回归夹具全过"; exit 0
else echo "FAIL: 见上方逐项"; exit 1; fi
