# README — challenge-c0e1e220 统计分析与结果解读（v1）

## 交付标准清单（题面 output_contract 提取）

1. **分析结果**：清洗表 + stats_results.json（描述统计/检验/效应量/CI，每个数字带列名/组/n/计算式）+ interpretation.json（逐条结论）。
2. **质量与复现证据**：数据快照 sha256、清洗规则+日志、脚本 sha256、random_seed=42、p_method 显式标注、decision_basis 方法选择依据。
3. **异常说明**：功效不足/方差为零/缺失过高/单位不明 → 停止推断并记录，不硬算。
4. 七类情形覆盖：缺失值（keep_missing 标记）/异常值（flag）/重复记录（主键去重）/统计假设（JB+方差比）/图表选择（可视化题联动）/代码运行（stats_kit 实跑）/数据库字段（db_probe schema 发现）。
5. 数据源：UCI Concrete(1030)/Iris(150 bezdek)/Wine(178) 快照或 SQLite（组织方修订案例）。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=statistical-analysis-interpretation）。
2. 脚本 ast.parse 全过（clean/stats_kit/db_probe/qa_stats）。
3. 实跑链路：
   - clean.py 脏表（缺失 token 3 类、主键重复 1 行、单位换算 mg/L→μg/mL、日期标准化、物理限 outlier flag）→ 6 动作留痕，qa_report 对账 pass。
   - stats_kit.py 两组（Ctrl 6 vs Trt 7）→ JB（n<8 标注功效不足）→方差比判定→Welch t（p=1e-6 下限，p_method 正态近似）、Cohen's d=-2.975、bootstrap CI seed=42 [14.5714,17.4286]。
   - db_probe.py 建表 SQLite → schema.tsv/row_counts.json 正确。
   - qa_stats.py：正例（真实数字解释）pass；负例（"证明有效"+编造 9.99）正确双杀 exit 1。
4. 资源限额：8 文件 ≈ 62KB。OK。
5. 无虚构。

## 设计要点

选择树决策依据（decision_basis）写进输出可回放；p 值近似方法显式（正态近似在小样本偏保守，注明建议 scipy 复核）；效应量与 CI 绑定每条结论；解释措辞黑名单（"证明有效"等）由脚本强制。
