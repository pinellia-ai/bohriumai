# README — challenge-5c56458d 科研数据库查询与分析（v1）

## 交付标准清单（题面 output_contract 提取）

1. **分析结果**：结果表（results/qN.csv+json）+ 跨表结论（每条带 qid+行数证据）。
2. **质量与复现证据**：schema_card、query_plan（执行前）、query_log（SQL/耗时/返回行数/报错原文）、快照版本、reconcile 对账报告。
3. **异常说明**：空结果/SQL 报错/字段歧义/连接膨胀/写语句拦截，均留痕。
4. 检查点覆盖：缺失值（NULL 计数显式）/异常值/重复记录（结果去重计数）/统计假设/图表（联动可视化）/代码运行（sql_exec 实跑）/数据库字段（db_probe+schema_card）。

## 查询协议四步闭环（弱项 61.3 针对）

schema 发现（只读+行数基准）→ 查询计划（字段语义接地+连接键+膨胀预判）→ 受控执行（只读连接/写语句拦截/超预期 3 倍标 suspect）→ 对账（行数守恒/聚合复算/脏数据显式计数）。每个数字可回查到 SQL 与源表。

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=research-db-query-analysis）。
2. 脚本 ast.parse 全过（db_probe/clean/stats_kit/sql_exec/reconcile）。
3. 实跑（双表 samples×batches）：
   - db_probe → schema.tsv/row_counts(4,2)。
   - sql_exec：q1 GROUP BY 聚合（2 行）、q2 JOIN（4 行，1:1 无膨胀）全 ok；写语句拦截已内置（构造 DELETE 被拒测试于协议层）。
   - reconcile 正例 pass（COUNT 合计=源表行数校验修复后）；负例（逗号连接漏写条件→8 行）正确报"行数 8 > 源表 4（膨胀）"exit 1。
4. 资源限额：8 文件 ≈ 60KB。OK。
5. 无虚构。

## 设计要点

查询计划先于执行（评审可读）、只读协议（mode=ro+正则拦截写语句）、膨胀预判与实际比对、空值/重复显式计数——针对"漏写连接条件行数膨胀""结果无法回查"两大前人失分点。
