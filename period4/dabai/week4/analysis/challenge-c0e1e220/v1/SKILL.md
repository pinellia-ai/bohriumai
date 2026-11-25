---
name: statistical-analysis-interpretation
description: |
  统计分析与结果解读。统计检验选择树自动执行（Jarque-Bera 正态性→方差齐→t/ANOVA 或非参数），效应量与 95%CI 绑定到每个结论，p 值近似方法显式标注，多重比较 Bonferroni 校正；输出 stats_results.json（每个数字带列名/组/n/计算式）+ 结果解释（区分统计显著与实际意义）。数据源为 UCI 快照或 SQLite 数据库。
---

# 统计分析与结果解读 Skill（statistical-analysis-interpretation）

## 1. 用途与适用范围

- 场景：实验测量记录/临床随访/组学表/问卷导出/数据库查询结果 + 具体统计问题（两组有无差异、差异多大、多确定）。
- 数据源：CSV 快照（UCI Concrete/Iris/Wine 等）或 SQLite 数据库（先用 db_probe.py 发现 schema）。
- 不做：实验设计、样本量估算、论文写作。
- 铁律：缺失不当 0、重复先去重、先验假设后检验、p=0.04 不得写成"证明有效"。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 抄 order.json）；最小 result.json 先落盘。
2. 读数据字典/字段语义 + 统计问题清单（task.md）。单位不明→先问清或标 unverified，**不硬算**。
3. 数据源盘点：
   - CSV：快照+sha256（同清洗题 snapshot 流程）。
   - SQLite：`python3 $SKILL_DIR/scripts/db_probe.py <db.sqlite> /app/work` → schema.tsv + row_counts.json（防张冠李戴表名/字段名）。
4. 缺失值/重复记录在统计前用 clean.py 处理（规则外置+留痕），缺失行**整行标记不删除不填补**，样本量如实。

## 3. 工作流程

### Step 1 描述统计与数据体检

stats_spec.json 第一个 test 固定为 descriptive：n/mean/sd/median/q1/q3/min/max + missing 计数。先看：缺失比例>20% 的列 → 标 uncertainty（统计效力存疑）；组内方差=0 → 停止该组推断，写 anomalies。

### Step 2 假设检验选择树（自动执行，依据写入输出）

```bash
python3 $SKILL_DIR/scripts/stats_kit.py /app/work/clean.csv /app/work/stats_spec.json /app/output/stats_results.json
```

选择树（stats_kit.py 内置，决策依据写进输出 decision_basis）：
1. 正态性：Jarque-Bera（p=exp(-JB/2)，chi2(2) 精确公式；n<8 标"功效不足"）。
2. 两组独立：JB 全过→方差比 0.5-2 视为齐→Student t；不齐→Welch t；非正态→Mann-Whitney U（含并列修正）。
3. 配对：正态→paired t；非正态→Wilcoxon signed-rank。
4. 多组：正态→one-way ANOVA（eta² 效应量）；非正态→Kruskal-Wallis；组间两两 Welch+Bonferroni。
5. **p 值近似方法显式标注**（p_method 字段）；小样本正态近似偏保守，如需精确值注明"建议 scipy 复核"。

### Step 3 效应量与置信区间（绑定结论）

- 两组：Cohen's d（附计算式）；均值 95%CI：bootstrap 2000 次 seed=42（输出含 seed）。
- 多组：eta² = SSB/(SSB+SSW)。
- CI 解读规则写进 result：区间是"参数估计的可信范围"，**不是个体取值范围**。

### Step 4 结果解释（逐条）

interpretation 数组，每条：
```json
{"claim": "Trt 组均值 15.0 vs Ctrl 10.7 (差 4.3)",
 "test": "welch-t", "stat": "t=..., df=..., p=...",
 "effect": "d=-2.98 (大效应)", "ci": "95%CI [...]",
 "verdict": "统计显著且实际意义明确 | 统计显著但效应小 | 不显著",
 "caution": "样本量小, p 为正态近似", "source": "stats_results.json#tests[0]"}
```
规则：不显著→写"未能检测到差异"，不写"无差异"；多重比较只引用校正后 p。

### Step 5 对账与 result.json

```bash
python3 $SKILL_DIR/scripts/qa_stats.py /app/output/stats_results.json /app/output/interpretation.json
```
断言：解释中每个数字能回查到 stats_results.json；CI 与检验结论一致方向；无"证明有效"类措辞。

```json
{
  "case_id": "<原样>", "status": "...",
  "data_snapshot": {"sha256": "...", "rows": 0, "missing_handled": "keep_missing"},
  "stats_results": "/app/output/stats_results.json",
  "interpretation": "/app/output/interpretation.json",
  "method_selection": {"normality": "JB", "chosen": "welch-t", "basis": "..."},
  "environment": {"python": "...", "random_seed": 42, "scripts_sha256": "..."},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

题面三大交付：分析结果（统计结果 JSON+解释）/质量与复现证据（快照+规则+代码+seed+环境）/异常说明。output_contract 逐字段落实。

## 5. 数字门槛

- 每个检验：统计量+df+p+效应量+CI 五件套齐（缺一标 partial 项）。
- 方法选择依据可回放（decision_basis）；p_method 显式；随机过程有 seed。
- 解释数字 100% 回查一致（qa_stats）。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 样本量不足（组 n<8） | 描述统计照给，推断检验标"功效不足"，不硬算 p |
| 组内方差为 0 | 停止推断，anomalies 记录 |
| 缺失比例过高（>40%） | 结果标 unreliable，建议人工确认 |
| 字段单位不明 | 停下追问/标 unverified，不硬算 |
| 非正态+小样本 | 用非参数，注明近似 |
| 数据库连接失败/表为空 | db_probe 报错位置，failed |

## 7. 自查清单

- [ ] 快照+去重+缺失处置留痕；样本量如实
- [ ] 选择树依据写入；p_method 标注；多重比较校正
- [ ] 效应量+CI 绑定每条结论；CI 解读正确
- [ ] qa_stats 数字回查全过；无过度措辞
- [ ] seed 与环境已记

## 8. 效率约束

先最小 result；一次成型；≤50 文件。

## 9. 最小示例

两组 6v7 数值 → JB(功效不足标注)→方差比判定→Welch t p=1e-6(下限)、d=-2.98、bootstrap CI seed=42（见 README 自测记录）。


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

- workorder 类型: `statistical_task`；spec 文件命名: `stats_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
