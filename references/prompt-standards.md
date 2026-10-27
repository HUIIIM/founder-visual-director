# 生图 prompt 标准：越做越真的七规范

> 来源提炼：本项目创始人视觉规范（生成标准与人体比例硬标准相关条款）+ 禁用词表 v1.0。
> 工艺铁律：人物、背景、光影、透视一次成像；**严禁"脸部抠图贴背景"**。

## 七规范

1. **单主光源**：只定一个主光源 + 方向 + 质感（如"左侧暖黄钨丝台灯主光、右侧远处冷蓝夜景轮廓光"）；禁用"电影感灯光"类空话。
2. **点名机身/镜头**：85mm f/1.8、iPhone、Kodak Portra 400 等，借它的天然缺陷（暗角、色散、颗粒）。
3. **皮肤诚实**：按年龄写具体质感（可见毛孔、法令纹），明写"不磨皮、unretouched"。
4. **生活细节**：场景放 2–3 个有存在理由的生活细节；背景过分整洁或糊成一片 = 重做。
5. **抓拍进行时**：视线不直视镜头；拒绝摆拍微笑 stock 感。
6. **冲突审计**：prompt 不许互斥指令（"夜景" + "正午烈日"、"手机自拍" + "85mm 镜头"之类）。
7. **后处理**：暗部加颗粒、轻微暗角、黑部提起（黑不死黑）；忌过 HDR、过锐化、过饱和；设备故事与后期一致（说 iPhone 就得是手机味后期）。

## 强制短语（正向必带）

```
7.5 heads tall, natural adult proportions, no fashion-model elongation
shot on 85mm f/1.8 lens, subject 3 meters from camera, eye-level angle
seamless neck-to-shoulder transition
```

注意：只写焦距不够，必须写清拍摄距离（subject 3 meters from camera），防广角近景畸变。

## 固定否定词带（每次必带）

```
plastic skin, cgi, perfect skin, symmetrical face, beauty filter,
oversized head, elongated neck, narrow shoulders, floating head, wide-angle distortion
```

## 禁用词表 v1.0（prompt 审查红线）

写完 prompt 必须全词 grep，零残留才算过。新增禁用词须经评审提案与终审确认。

```
cinematic / cinematic lighting / 提亮暗部 / lift shadows / brighten /
HDR / 过饱和 / oversaturated / 电影感灯光 / 完美皮肤 / perfect skin / flawless skin
```

## 机读规则附表（工具直读，v0.1）

> 本节是上文与 SKILL.md 规则的机读化转写，供 demo / 工具在运行时直读判定。
> 口径以上文与 SKILL.md 为准；本节只做格式转写，不新增规则。新增/修改条目须与源规则同步评审。
> 来源：面部禁词与年龄模式 ← SKILL.md「prompt 模板铁律」1（禁写面部特征词：眼/鼻/笑/年龄感等）；
> 互斥对 ← SKILL.md Step 3-6 与上文七规范 6；B 级触发 ← SKILL.md Step 2-1（真实可识别人物转 B 级严审）。

```text
[face_words]
eye, eyes, eyebrow, eyebrows, nose, nostril, lips, smile, smiling, grin,
眼睛, 眼睑, 鼻子, 鼻梁, 嘴唇, 笑容, 微笑, 年龄感
[age_patterns]
\b\d{2}s\b
\b\d+\s*years?\s*old\b
\b\d+\s*岁
middle-aged
[conflict_pairs]
夜景|夜晚|夜间|night <> 正午烈日|正午|烈日|midday|noon
自拍|selfie|手机自拍 <> 85mm
[b_level_triggers]
名人, 合影, 晚宴, 政治名媛, celebrity, red carpet
```

## 一体化构图要求

巨型标题与照片是同一张设计——标题压图、眉题 / 证据条 / 页脚同一视觉语言；
图和字分开做的，一律打回。版式：眉题 → 主标题 ≤12 字 → 证据条；对比度 ≥4.5:1；标题不侵安全边距。
