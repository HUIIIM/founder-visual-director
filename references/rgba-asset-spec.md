# 信息图素材规范：直接生成 RGBA 透明素材（M5）
- 信息图装饰素材（图标/飘带/数字徽章/箭头）一律直接生成 RGBA 透明 PNG；
- 退役"生图再抠"流程：不再先生整图再抠图（边缘残留 + 工时浪费）；
- 优先支持原生透明通道的模型（Qwen-Image-2.1 RGBA VAE 等），prompt 显式声明 transparent background；
- 素材入库命名：`asset-<类别>-<编号>.png`，台账登记用途。
