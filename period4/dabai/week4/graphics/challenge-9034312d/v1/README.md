# README — challenge-9034312d 实验装置与技术路线图（v1）

## 交付标准清单（题面 output_contract 提取）

1. **可编辑源文件**：分层 SVG，节点=部件/步骤（带编号与来源），边=连接/流向。
2. **导出件**：PNG 300dpi + PDF + export_check 10 项检查结果。
3. **来源与修改记录**：parts/connections/steps/flows 四 TSV（每行 source_location）、qa_check/numbering_check 报告、uncertainty（含 inferred 连接）、change_log。
4. 六类要素覆盖：科学实体（部件）/空间关系（接口对齐、区室）/数据编码（线型=介质）/图例标注/可编辑源文件/导出格式。
5. workorder：apparatus_and_technical_route——真实可编辑 SVG/PNG/PDF + 源保留编辑。

## 关键断言

- qa_check：悬空端点=0、断头箭头=0、凭空连接=0（推断须显式标 inferred）、来源全覆盖。
- numbering_check：spec 编号集合=正文清单集合；非回流边不得使编号倒退。
- export_check：文字未转曲/图元带 id+data-source/分层/字体/图例数/PNG 尺寸/PDF。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=apparatus-route-diagram）。
2. 脚本 ast.parse 全过（8 个脚本）。
3. 实跑（3 部件装置+3 步骤流程 demo）：qa_check pass → numbering_check pass → svg_builder → export_check pass（legend-n 1）。产物 svg/png(300dpi)/pdf 全生成。
4. 资源限额：8 文件 ≈ 53KB。OK。
5. 无虚构。

## 设计要点

结构化中间表示（实体—连接—步骤—流向四表）先于布图：布局是四表的确定性投影，检查在表级完成，避免"画完才发现错"。
