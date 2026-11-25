---
name: research-db-query-analysis
description: |
  科研数据库查询与分析（弱项重点题）。查询协议四步闭环：schema 发现（只读探查）→ 查询计划（字段语义接地+连接键推断）→ 受控执行（行数预算+超时）→ 结果对账（行数守恒/连接膨胀检查/独立复算）。交付 SQL+查询日志+schema 卡片+字段解释+跨表分析结论，每个数字可回查到原始查询。
---

# 科研数据库查询与分析 Skill（research-db-query-analysis）

## 1. 用途与适用范围

- 场景：授权 SQLite/数据快照上的查询、结果抽取、字段解释、跨表分析。
- 不做：数据库运维与权限治理、实验设计。
- 判据：查询在授权快照上直接执行；结果可独立复算；字段含义与关联路径可按记录复核。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 抄 order.json）；最小 result.json 先落盘。
2. **只读原则**：连接串强制 `mode=ro`；明确哪些表只读、不执行任何写语句（CREATE/UPDATE/DELETE 一律拒绝）。
3. 数据快照/数据库文件缺失 → failed，不猜连接参数。

## 3. 工作流程（查询协议四步闭环）

### Step 1 schema 发现（防张冠李戴）

```bash
python3 $SKILL_DIR/scripts/db_probe.py <db.sqlite> /app/work
```

产出 schema.tsv（表/列/类型/主键）、row_counts.json（每表行数——后续对账基准）、sample_rows.json（每表前 3 行样例）。写 schema_card.md：每表一段（行数、主键、关键列语义初判、与其他表的候选连接键）。字段语义拿不准（如 status 是样本状态还是实验状态）→ 在 schema_card 标 ambiguous，查询时两个口径都说明取舍。

### Step 2 查询计划（字段语义接地 + 连接键推断）

query_plan.json（执行前写，评审可读）：
```json
[{"id": "q1", "question": "各组样本量与均值", "tables": ["specimens"],
  "sql": "SELECT species, COUNT(*) n, AVG(weight) FROM specimens GROUP BY species",
  "expected_grain": "每 species 一行", "expected_rows_max": 10,
  "join_path": null, "field_semantics": {"weight": "重量(g), 来源 schema_card"}}]
```
规则：跨表查询必须先写 join_path（键+方向），**一对多连接必须预判膨胀**（子表行数>父表时行数会 >父表行数，写进 expected_grain）；聚合粒度与问题匹配（"每组平均"≠"每行平均"）。

### Step 3 受控执行

```bash
python3 $SKILL_DIR/scripts/sql_exec.py /app/work/query_plan.json <db.sqlite> /app/output
```

sql_exec.py 逐条：只读模式连接；写语句拦截（正则拒 CREATE/INSERT/UPDATE/DELETE/DROP/ALTER）；执行留痕 query_log.json（SQL/参数/耗时/返回行数/截断标志）；超 expected_rows_max×3 → 结果标 suspect（防笛卡尔积）；结果集写 results/<qid>.csv + JSON。

### Step 4 结果对账（每个数字可回查）

```bash
python3 $SKILL_DIR/scripts/reconcile.py /app/work/query_log.json /app/output/results /app/work/row_counts.json /app/work/query_plan.json
```

断言：
1. **行数守恒**：GROUP BY 行数≤源表行数；未聚合查询行数≤源表行数；join 查询行数与预判膨胀一致（不符→FAIL）。
2. **独立复算**：结果 CSV 的 COUNT(*)/SUM/AVG 用 db_probe 的行数与 Python 直读复算比对（抽验每个结果集≥1 个聚合值）。
3. **脏数据处理**：结果中的 NULL/重复记录计数并列说明，不静默进入统计。
4. 任一 FAIL → 修 SQL（连接条件/粒度）重跑，≤2 轮。

### Step 5 字段解释与跨表结论

result.json 的 field_interpretation 每字段：含义/取值范围/单位/口径来源（schema_card 或数据字典）；跨表结论每条附 qid 与行数证据。结论措辞守则：行数=0 写"未查询到"，不写"不存在"。

## 4. 输出契约

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "connection": {"mode": "readonly", "db": "...", "tables": 0},
  "schema_card": "/app/work/schema_card.md",
  "query_plan": "/app/work/query_plan.json",
  "query_log": "/app/work/query_log.json",
  "results": [{"qid": "q1", "csv": "...", "rows": 0, "sql": "..."}],
  "reconcile": {"pass": true, "checks": ["row conservation", "recompute", "NULL/dup counts"]},
  "field_interpretation": [{"field": "...", "meaning": "...", "unit": "...", "source": "schema_card"}],
  "cross_table_findings": [{"finding": "...", "qid": "q2", "evidence_rows": 0}],
  "uncertainty": [], "change_log": []
}
```

题面三大交付：分析结果（查询结果表）/质量与复现证据（SQL+日志+快照版本+对账）/异常说明（空结果/权限/字段歧义）。

## 5. 数字门槛

- 100% 查询真实执行（query_log 有返回行数，无手填表）；reconcile 全 PASS；每个结果数字能回查到 SQL 与源表。
- join 预判膨胀与实际一致；NULL/重复计数显式。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 空结果 | 记录查询条件，写"未查询到"，核查条件是否过严 |
| SQL 报错 | 错误原文进 query_log，定位（表名/列名/语法）后改写，≤2 轮 |
| 权限不足 | failed（只读模式下一般不出现写权限问题） |
| 字段歧义 | 两个口径都算并说明取舍 |
| 连接膨胀 | reconcile FAIL → 改 join 键或先聚合再连 |
| 类型不一致（文本数字） | CAST 显式转换并记录 |

## 7. 自查清单

- [ ] 只读连接；无写语句
- [ ] schema_card + query_plan 先于执行
- [ ] query_log 逐条留痕（含报错）
- [ ] reconcile 三断言过；NULL/重复计数显式
- [ ] 结论有 qid+行数证据；不夸大措辞

## 8. 效率约束

先最小 result；SQL 一次成型+最多修 2 轮；≤50 文件。

## 9. 最小示例

建表 SQLite → db_probe 发现 → 计划 2 查询（分组聚合+跨表 join）→ sql_exec 留痕 → reconcile 行数守恒+复算 pass（见 README 自测记录）。


## 附录 A 全流程命令序列（评测时按序执行）

```bash
# Step 0 识别（手动：读 /input/case.json 抄 output_contract 到 order.json）
mkdir -p /app/work /app/output
# Step 1-N 主链路（$SKILL_DIR 为本 skill 安装目录）
ls $SKILL_DIR/scripts/        # 确认脚本齐备
# 各 Step 的具体命令见 §3；校验脚本 FAIL 时按 §6 异常表处置后重跑（≤2 轮）
python3 $SKILL_DIR/scripts/export_check.py --help   # 查看参数
```

## 附录 B 常见失败 ↔ 处置对照

| 失败现象 | 根因 | 处置 |
|---|---|---|
| 校验脚本 exit 1 有 FAIL 项 | 见其输出 detail 字段 | 按 detail 修 spec/数据后重跑 |
| PNG 打开是白图/方框 | 无 CJK 字体 | FIG_CJK_FONT=/path/to/font.ttf 后重跑渲染 |
| result.json 字段缺失 | 跳过 Step 6 模板 | 按 §3 末模板逐字段补齐 |
| 预算接近上限 | 前面步骤耗时过多 | 立即交 partial（status 如实），已产文件照常评分 |
| 材料与预期类型不符 | 题面材料变化 | 按 Step 0 盘点结果走 §6 对应行 |

## 附录 C 与本赛道的边界对照（不做的事，避免越界扣分）

- workorder 类型: `db_query_task`；spec 文件命名: `query_plan.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
