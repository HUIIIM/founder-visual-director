# 样例台账（合规）— P1 自测夹具，非真实登记

格式见 references/ledger-format.md（v1.0）。本文件同时用作轮换预检「通过」例
与面部一致性校验「通过」例（references 哈希与 refs/ 下字节夹具实测一致）。

```json
[
  {
    "ledger_id": "xhs-2026-009",
    "platform": "小红书",
    "post_no": "第 9 篇",
    "date_made": "2026-10-24",
    "date_published": "2026-10-24",
    "scene_category": "城市街景",
    "outfit": "藏青西装外套+白衬衫",
    "styling": "侧分短发",
    "asset_grade": "A",
    "asset_id": "xhs-asset-009",
    "model_id": "miao-v1",
    "reference_roles": "anchor=refs/anchor-fixture.txt, style=refs/style-fixture.txt",
    "references": [
      {"file": "refs/anchor-fixture.txt", "role": "anchor", "sha256": "415a58256d2d8e93295b0a89fbb6c3062c1f578336b697f24b450f0975e0fa07"},
      {"file": "refs/style-fixture.txt", "role": "style", "sha256": "b6fa047e6409a5d0d4bdf63851bb79c47dc20b51c79e457b526aefb82233c5c4"}
    ],
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》；小红书 AI 生成内容标识规则"
  },
  {
    "ledger_id": "xhs-2026-007",
    "platform": "小红书",
    "post_no": "第 7 篇",
    "date_made": "2026-10-05",
    "date_published": "2026-10-05",
    "scene_category": "咖啡馆餐饮",
    "outfit": "米色针织衫",
    "styling": "清爽短发",
    "asset_grade": "B",
    "asset_id": "xhs-asset-007",
    "model_id": "miao-v1",
    "reference_roles": "anchor=refs/anchor-fixture.txt, layout=refs/layout-fixture.txt",
    "references": [
      {"file": "refs/anchor-fixture.txt", "role": "anchor", "sha256": "415a58256d2d8e93295b0a89fbb6c3062c1f578336b697f24b450f0975e0fa07"},
      {"file": "refs/layout-fixture.txt", "role": "layout", "sha256": "d3ef30fee15b9fe2fbcf5ba9529b44c62f7585e1b3dfca76e2df4ab554e5d430"}
    ],
    "status": "已发布",
    "ai_generated": true,
    "ai_disclosure_text": "本图由 AI 生成",
    "ai_disclosure_method": "platform_declaration",
    "ai_disclosure_basis": "《人工智能生成合成内容标识办法》；小红书 AI 生成内容标识规则"
  },
  {
    "ledger_id": "xhs-2026-003",
    "platform": "小红书",
    "post_no": "第 3 篇",
    "date_made": "2026-09-18",
    "date_published": "2026-09-18",
    "scene_category": "室内书房",
    "outfit": "灰色衬衫",
    "styling": "居家短发",
    "asset_grade": "B",
    "asset_id": "xhs-asset-003",
    "model_id": "miao-v1",
    "reference_roles": "anchor=refs/anchor-fixture.txt",
    "references": [
      {"file": "refs/anchor-fixture.txt", "role": "anchor", "sha256": "415a58256d2d8e93295b0a89fbb6c3062c1f578336b697f24b450f0975e0fa07"}
    ],
    "status": "已发布",
    "ai_generated": false,
    "ai_disclosure_text": "",
    "ai_disclosure_method": "none",
    "ai_disclosure_basis": ""
  }
]
```
