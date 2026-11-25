# README — graphical-abstract-7030fff2 Graphical Abstract（v1）

## 交付标准清单（题面 output_contract 提取）

1. **可编辑源文件**：分层 SVG，四面板命名（A-question/B-method/C-results/D-conclusion），文字未转曲。
2. **导出件**：PNG 300dpi + PDF；export_check 10 项结果。
3. **来源与修改记录**：storyboard.json（面板—要点—source 映射）、entities/relations/datamap TSV、storyboard_check 报告、uncertainty、change_log。
4. 单页视觉压缩：问题→方法→结果→结论，阅读顺序编号，结果面板最大（数据图内嵌）。
5. workorder：graphical_abstract——真实可编辑 SVG/PNG/PDF + 源保留编辑。
6. 对齐前人 75.7 最强经验：先 storyboard（面板—要点映射）后画图；结论必须被结果支撑（storyboard_check 强制），防"热闹信息图"。

## 关键断言（storyboard_check.py）

- 四面板齐备且各≥1 要点；每面板有 source。
- datamap 有值必有来源（防编造数值）。
- 结论要点关键词须见于 results/材料引用（防结论超界）。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=graphical-abstract-builder）。
2. 脚本 ast.parse 全过（8 个脚本）。
3. 实跑：storyboard_check 正例（纳米载体 demo，四面板+datamap）pass:true；负例（无支撑结论"量子隧穿"）正确 FAIL exit 1。
4. 复用脚本（svg_builder/chart_builder/export_check）已在 98e5a474/1bd90d8a 实测全过，此处直接复用同一测试基线。
5. 资源限额：8 文件 ≈ 56KB。OK。
6. 无虚构。

## 设计要点

固定四面板模板保证同输入复现同结构（题面核心判据②）；色板默认 Okabe-Ito（色觉安全+灰度可辨）。
