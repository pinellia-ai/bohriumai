# challenge-f35e4ca5 阅读02｜科研图表解析 — 交付说明

## 交付标准（从题面提取）
1. 图表读成带单位/精度/误差范围的结构化数据，五步流水线：清点→坐标标定→元素提取→三级解释标注→result.json。
2. 每个数值可回指原图位置与读取依据；读不出/不确定标 unavailable/uncertain，不编造。
3. result.json 含 output_contract 全部字段 + case_id 原样；status: success/partial/failed。
4. 运行时契约：/input/case.json → /app/work 过程 → /app/output 产物；预算 64 请求/900 秒；≤50 文件/2MB。
5. 无像素刻度/裁剪/过曝 → status=partial 如实降级，只报可判读元素。

## 自测记录（2026-11-25）
- [x] YAML frontmatter 可解析（name: scientific-figure-parsing）
- [x] 输出契约逐字段落实（case_id/status/单位/精度/误差/来源定位/uncertainty_notes）
- [x] 数字门槛：无法标定 → partial 显式降级路径
- [x] 异常表覆盖：无刻度/裁剪/过曝/材料缺失/空图
- [x] 资源限额：2 文件 12KB（≤50文件/2MB）
- [x] 无虚构：全程离线语料约束，不声称实时读取
