# README — challenge-9ec929fe 科研代码生成与执行（v1）

## 交付标准清单（题面 output_contract 提取）

1. **分析结果**：analysis.py（FIELDS 字段常量区+显式缺失处理）+ result.json。
2. **质量与复现证据**：env.json（python/包版本）、runs/run_NNN.json（命令行/stdout/stderr/退出码/耗时）、代码 sha256、verify_results 报告（行数对照/数值复算/AST 静默扫描）。
3. **异常说明**：依赖缺失降级、超时截断、失败现场保留（run json 不覆盖）。
4. 检查点覆盖：缺失值/异常值/重复/统计假设/图表（联动可视化）/代码运行（run_guard 实跑）/数据库（db_probe）。
5. 静默错误四模式：缺失当0风险 / groupby 未去重 / ttest 无假设检查 / 硬编码路径。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=research-code-execution）。
2. 脚本 ast.parse 全过（clean/stats_kit/db_probe/run_guard/verify_results）。
3. 实跑全链：analysis_demo.py（字段常量+显式 float 转换）→ run_guard env 快照 → run_guard run（exit 0, 7.5s 留痕 run_002.json）→ verify_results：行数对照 13 ✓、mean 复算 match ✓、AST 四模式 pass ✓。
4. 资源限额：8 文件 ≈ 62KB。OK。
5. 无虚构。

## 设计要点

"跑通≠正确"落地为三类脚本断言；失败现场（每次 run 独立 JSON 编号递增不覆盖）保证失败可定位恢复——针对题面"出错后换代码瞎试"的痛点。
