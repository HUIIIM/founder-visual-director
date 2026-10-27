# 样例台账（面部一致性违规）— P1 自测夹具，非真实登记

与 check_face_consistency.py 配套，预置两类违规：
- xhs-2026-101：只登记了 style 参考图，无 anchor -> anchor 缺失；
- xhs-2026-102：登记了 anchor 但 sha256 与实物不符（全零占位）-> 哈希不符。

```json
[
  {
    "ledger_id": "xhs-2026-101",
    "platform": "小红书",
    "post_no": "夹具 101",
    "date_made": "2026-10-25",
    "scene_category": "城市街景",
    "outfit": "黑色速干T恤+短裤",
    "styling": "素颜短发",
    "asset_grade": "A",
    "asset_id": "xhs-asset-101",
    "model_id": "miao-v1",
    "reference_roles": "style=refs/style-fixture.txt",
    "references": [
      {"file": "refs/style-fixture.txt", "role": "style", "sha256": "b6fa047e6409a5d0d4bdf63851bb79c47dc20b51c79e457b526aefb82233c5c4"}
    ],
    "status": "待发",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  },
  {
    "ledger_id": "xhs-2026-102",
    "platform": "小红书",
    "post_no": "夹具 102",
    "date_made": "2026-10-25",
    "scene_category": "室内书房",
    "outfit": "灰色卫衣",
    "styling": "侧分短发",
    "asset_grade": "B",
    "asset_id": "xhs-asset-102",
    "model_id": "miao-v1",
    "reference_roles": "anchor=refs/anchor-fixture.txt",
    "references": [
      {"file": "refs/anchor-fixture.txt", "role": "anchor", "sha256": "0000000000000000000000000000000000000000000000000000000000000000"}
    ],
    "status": "待发",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  }
]
```
