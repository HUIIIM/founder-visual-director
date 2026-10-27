# 样例台账（违规）— P1 自测夹具，非真实登记

与 candidate-violation.json 配套，预置三类违规（对候选 2026-10-26 / 小红书）：
- 相邻 3 篇服装重复：xhs-2026-010（2026-10-25）与候选同服装；
- 相邻 3 篇造型重复：xhs-2026-008（2026-10-23）与候选同造型；
- 14 天同场景大类：xhs-2026-006（2026-10-20，户外运动）距候选 6 天（不在最近 3 篇内，单独命中 14 天检查）；
- 冷却期：候选复用 asset-s-001，上次使用 xhs-2026-004（2026-10-10，S 级冷却 30 天）仅隔 16 天。

```json
[
  {
    "ledger_id": "xhs-2026-010",
    "platform": "小红书",
    "post_no": "第 10 篇",
    "date_made": "2026-10-25",
    "date_published": "2026-10-25",
    "scene_category": "城市街景",
    "outfit": "黑色速干T恤+短裤",
    "styling": "侧分短发",
    "asset_grade": "A",
    "asset_id": "xhs-asset-010",
    "model_id": "miao-v1",
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  },
  {
    "ledger_id": "xhs-2026-009b",
    "platform": "小红书",
    "post_no": "第 9 篇·补",
    "date_made": "2026-10-24",
    "date_published": "2026-10-24",
    "scene_category": "旅行度假",
    "outfit": "沙滩衬衫",
    "styling": "棒球帽",
    "asset_grade": "B",
    "asset_id": "xhs-asset-009b",
    "model_id": "miao-v1",
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  },
  {
    "ledger_id": "xhs-2026-008",
    "platform": "小红书",
    "post_no": "第 8 篇",
    "date_made": "2026-10-23",
    "date_published": "2026-10-23",
    "scene_category": "室内书房",
    "outfit": "灰色卫衣",
    "styling": "素颜短发",
    "asset_grade": "B",
    "asset_id": "xhs-asset-008",
    "model_id": "miao-v1",
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  },
  {
    "ledger_id": "xhs-2026-006",
    "platform": "小红书",
    "post_no": "第 6 篇",
    "date_made": "2026-10-20",
    "date_published": "2026-10-20",
    "scene_category": "户外运动",
    "outfit": "白色跑步套装",
    "styling": "运动发带",
    "asset_grade": "A",
    "asset_id": "xhs-asset-006",
    "model_id": "miao-v1",
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  },
  {
    "ledger_id": "xhs-2026-004",
    "platform": "小红书",
    "post_no": "第 4 篇",
    "date_made": "2026-10-10",
    "date_published": "2026-10-10",
    "scene_category": "商务场合",
    "outfit": "深灰西装",
    "styling": "侧分短发",
    "asset_grade": "S",
    "asset_id": "asset-s-001",
    "model_id": "miao-v1",
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》"
  }
]
```
