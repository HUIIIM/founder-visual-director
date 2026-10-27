# P1 自测夹具（issue #6 P1）

全部为构造样例，非真实登记/素材。`demo/eval.sh` 已把下列关键断言纳为回归夹具。

| 夹具 | 用途 | 期望 |
|---|---|---|
| `ledger-compliant.md` | 轮换预检 + 面部一致性（双用） | 轮换：结论「通过」；面部：通过（anchor 齐备、哈希一致） |
| `ledger-violation.md` | 轮换预检违规例 | 结论「违规」：相邻 3 篇服装重复、相邻 3 篇造型重复、14 天同大类、冷却期未满 |
| `ledger-face-violation.md` | 面部一致性违规例 | 退出码 1：xhs-2026-101 anchor 缺失；xhs-2026-102 哈希不符 |
| `candidate-compliant.json` | 配 `ledger-compliant.md` 的候选 | — |
| `candidate-violation.json` | 配 `ledger-violation.md` 的候选 | — |
| `brandlock-bad.txt` | 品牌锁违规例 | 退出码 1：手写色值 #FF6B35 / #123456、字体 Arial、已淘汰字体 Noto Sans SC、字标 Vertciti |
| `brandlock-good.txt` | 品牌锁合规例 | 退出码 0 |
| `refs/*.txt` | 参考图字节夹具 | 仅供 SHA-256 存在性/一致性核验的字节占位，**不是图片**、不作任何交付素材 |

手动复跑：

```bash
python3 scripts/check_rotation.py --ledger demo/fixtures/ledger-violation.md --candidate demo/fixtures/candidate-violation.json
python3 scripts/check_rotation.py --ledger demo/fixtures/ledger-compliant.md --candidate demo/fixtures/candidate-compliant.json
python3 scripts/check_brand_lock.py demo/fixtures/brandlock-bad.txt
python3 scripts/check_face_consistency.py demo/fixtures/ledger-face-violation.md
```
