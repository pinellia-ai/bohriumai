# README — challenge-1bd90d8a 科研数据图表生成与编辑（v1）

## 交付标准清单（题面 output_contract 提取）

1. **可编辑源文件**：SVG 分层可编辑（文字 `<text>` 未转曲），图例/系列/数据映射正确。
2. **导出件**：PNG 300dpi（≥1500px）+ PDF，附 export_check 10 项检查结果。
3. **来源与修改记录**：data.raw.csv 快照+sha256、fieldmap.tsv（图元↔列/行/单位）、verify_map 抽验结果、change_log。
4. 六类检查点覆盖：科学实体/空间关系/数据编码/图例标注/可编辑源文件/导出格式（SKILL Step3 表格逐项断言）。
5. workorder：source_value_chart——图表数值可回溯源数据行列；基线不截断；误差线含义必标。
6. result.json：output_contract 逐字段 + case_id 原样 + status 如实。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=source-value-chart）。
2. 脚本 ast.parse 全过：core_g/svg_builder/raster/chart_builder/export_check/snapshot/verify_map。
3. 实跑链路：test_chart.csv(3行) → snapshot.py 快照(sha256/缺失计数) → chart_builder 柱图（data-value/data-row 写入 SVG）→ export_check pass:true → verify_map 3/3 全 match（pass:true）。全部真实执行通过。
4. 负例：verify_map 对不一致 CSV 报 mismatch 并 exit 1（构造 1 行改值验证）。
5. 资源限额：8 文件 ≈ 48KB。OK。
6. 无虚构：示例均标注示意。

## 弱项针对（前人 63.7）

本版重点补：① 图元↔源数据双向映射（data-value/data-row + verify_map 抽验）② 误差线含义与单位强制 ③ 基线完整性断言 ④ 快照 sha256 保证复跑同一张图。
