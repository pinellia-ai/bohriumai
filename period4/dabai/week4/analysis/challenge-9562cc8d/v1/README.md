# README — challenge-9562cc8d 科研数据可视化（v1）

## 交付标准清单（题面 output_contract 提取）

1. **分析结果**：图表文件（SVG 可编辑源 + PNG 300dpi + PDF）+ 绘图代码 + 独立可读图注（fig_note.txt）。
2. **质量与复现证据**：数据快照 sha256、chart_spec（含 data_policy 口径）、图型选择规则（chosen+rejected+理由）、annotate_check 10 项、export_check 10 项。
3. **异常说明**：缺失列/量纲/类别过多/字体/空结果集处置表。
4. 检查点覆盖：缺失值（data_policy）/异常值/重复/统计假设（误差线含义+显著性标注联动统计题）/图表选择（规则库）/代码运行（chart_builder 实跑）/数据库字段（db_probe）。
5. 数据源：UCI 快照或 SQLite。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=research-data-visualization）。
2. 脚本 ast.parse 全过（9 个脚本：clean/stats_kit/db_probe/chart_builder/core_g/raster/export_check/annotate_check + 规则内置于 SKILL）。
3. 实跑：3 组柱图（y 轴含单位、SD 误差线、n=3）→ annotate_check 10/10 pass → export_check pass → fig_note.txt 图注生成正确（含误差线含义、n、数据源、基线声明、色板说明）。SVG data-value/data-row 映射（verify_map 在 1bd90d8a 已实测 3/3）。
4. 资源限额：9 文件 ≈ 66KB。OK。
5. 无虚构。

## 设计要点

同源双渲染：SVG 与 PNG 用同一 X()/Y() 映射函数，位图与矢量永不一致；图注由脚本从 spec 自动拼装保证与图一致；图型规则库要求 rejected+理由（评分点：说明不推荐原因）。
