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

# P1 回归夹具：台账真读判定 + 品牌锁/面部一致性校验（scripts/，issue #6 P1）
# 全部在临时目录跑，不污染 demo/output。任一断言失败 -> FAIL。
FIXP="$DEMO/fixtures"
SCRIPTS="$(dirname "$DEMO")/scripts"
FX="$(mktemp -d)"
# 轮换违规例：run.py 接违规台账 -> rotation.md 必须逐项命中且结论为违规
cat > "$FX/cand-violation.json" <<'EOF'
{"aspect":"3:4","mood":"生活感","scene":"城市晨跑后拉伸","theme_platform":"小红书第 11 篇封面","platform":"小红书","post_no":"第 11 篇","date":"2026-10-26","scene_category":"户外运动","outfit":"黑色速干T恤+短裤","styling":"素颜短发","asset_id":"asset-s-001","asset_grade":"S"}
EOF
FVD_DEMO_OUT="$FX/out-v" FVD_LEDGER_PATH="$FIXP/ledger-violation.md" python3 "$DEMO/run.py" "$FX/cand-violation.json" > "$FX/v.log" 2>&1
grep -q "结论：违规" "$FX/out-v/rotation.md" || note "P1 轮换违规例：rotation.md 结论非违规"
for s in "相邻 3 篇内服装重复" "相邻 3 篇内造型重复" "14 天同大类" "冷却期未满"; do
  grep -q "$s" "$FX/out-v/rotation.md" || note "P1 轮换违规例：缺违规明细：$s"
done
# 轮换合规例：接合规台账 -> rotation.md 结论必须为通过
cat > "$FX/cand-compliant.json" <<'EOF'
{"aspect":"3:4","mood":"生活感","scene":"城市晨跑后拉伸","theme_platform":"小红书第 11 篇封面","platform":"小红书","post_no":"第 11 篇","date":"2026-10-26","scene_category":"户外运动","outfit":"黑色速干T恤+短裤","styling":"运动短发","asset_id":"xhs-asset-new-run","asset_grade":"A"}
EOF
FVD_DEMO_OUT="$FX/out-c" FVD_LEDGER_PATH="$FIXP/ledger-compliant.md" python3 "$DEMO/run.py" "$FX/cand-compliant.json" > "$FX/c.log" 2>&1
grep -q "结论：通过" "$FX/out-c/rotation.md" || note "P1 轮换合规例：rotation.md 结论非通过"
# 台账缺失必须降级为无法判定，绝不冒充通过
FVD_DEMO_OUT="$FX/out-m" FVD_LEDGER_PATH="$FX/no-ledger.md" python3 "$DEMO/run.py" "$FX/cand-compliant.json" > "$FX/m.log" 2>&1
grep -q "结论：无法判定" "$FX/out-m/rotation.md" || note "P1 台账缺失例：未降级为无法判定"
# 品牌锁：违规夹具必须被拒、合规夹具必须通过
python3 "$SCRIPTS/check_brand_lock.py" "$FIXP/brandlock-bad.txt" > "$FX/bl-bad.log" 2>&1
[ $? -eq 1 ] || note "P1 品牌锁违规例：未以退出码 1 拒绝"
grep -q "#FF6B35" "$FX/bl-bad.log" || note "P1 品牌锁违规例：未列出手写色值"
python3 "$SCRIPTS/check_brand_lock.py" "$FIXP/brandlock-good.txt" > "$FX/bl-good.log" 2>&1
[ $? -eq 0 ] || note "P1 品牌锁合规例：未通过"
# 面部一致性：anchor 缺失/哈希不符必须被拒、合规台账必须通过
python3 "$SCRIPTS/check_face_consistency.py" "$FIXP/ledger-face-violation.md" > "$FX/fc-bad.log" 2>&1
[ $? -eq 1 ] || note "P1 面部违规例：未以退出码 1 拒绝"
grep -q "anchor 参考图应恰好 1 张" "$FX/fc-bad.log" || note "P1 面部违规例：未报 anchor 缺失"
grep -q "哈希不符" "$FX/fc-bad.log" || note "P1 面部违规例：未报哈希不符"
python3 "$SCRIPTS/check_face_consistency.py" "$FIXP/ledger-compliant.md" > "$FX/fc-good.log" 2>&1
[ $? -eq 0 ] || note "P1 面部合规例：未通过"
rm -rf "$FX"

[ -n "$TMPD" ] && rm -rf "$TMPD"
if [ "$ok" = 1 ]; then echo "PASS: 三部分交付物齐全，规则直读校验与回归夹具全过"; exit 0
else echo "FAIL: 见上方逐项"; exit 1; fi
