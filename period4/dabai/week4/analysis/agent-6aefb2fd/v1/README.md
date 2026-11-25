# README — agent-6aefb2fd 多步骤数据分析 Agent（v1）

## 交付标准清单（题面 output_contract 提取）

1. **分析结果**：五段产物齐（清洗表/统计结果 JSON/图表 SVG+PNG/报告 report.md），同一环境串通。
2. **质量与复现证据**：stage_N checkpoint（输入 sha256/输出/断言/秒数）、fieldmap、rules、seed、快照。
3. **异常说明**：fail-fast 失败段现场 + 重试记录 + partial 交付已完成段。
4. 检查点覆盖：缺失/异常/重复（Stage2）/统计假设（Stage3）/图表选择（Stage4）/代码运行（pipeline 实跑）/数据库字段（db_probe）。
5. 报告数字程序化回填（report_builder 占位符→stats_results 取值），backfill 审计文件记录每个数字来源路径。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=multi-step-analysis-pipeline）。
2. 脚本 ast.parse 全过（10 个脚本）。
3. 实跑三段流水线（clean→stats→report）：全 done，exit 0；report.md 数字由脚本回填（含 NA 处理）；--resume 续跑正确跳过已 done 段（skipped(done)）。
4. fail-fast 验证：构造 stats 崩溃场景（组 n<2）→ stage_2 status=failed、pipeline exit 1、checkpoint 保留现场；修复后全通过（防护也已加入 stats_kit）。
5. 资源限额：11 文件 ≈ 76KB。OK。
6. 无虚构。

## 设计要点

checkpoint+resume（失败不从头重来）；fail-fast（口径走偏即停）；报告数字只允许脚本回填（防手抄不一致）——分别针对题面三个痛点：失败恢复、过程可复核、数字同源。
