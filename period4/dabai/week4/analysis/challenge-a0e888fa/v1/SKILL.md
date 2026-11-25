---
name: research-data-cleaning
description: |
  科研数据清洗与处理（聚合表转录+注入故障场景）。按数据字典逐字段执行清洗 workorder：缺失/异常/重复/格式/单位五类规则外置为 rules.json，处理动作留痕（逐字段逐行号日志），质量报告数字与结果表对账一致。硬约束：不填补缺失与无效值、不推断群体统计、不覆盖原始文件；每个处理决定带字典依据。
---

# 科研数据清洗 Skill（research-data-cleaning）

## 1. 用途与适用范围

- 场景（组织方修订）：公开发表聚合表的转录数据，含显式注入的存储/编码故障；附数据字典与逐指标单位/QC 规则和明确清洗工单。
- 硬边界：**不做填补（impute 禁止）**、不推断群体统计、不覆盖原文件；"未检测 / 低于检出限 / 录入缺失 / 真值 0"四类必须区分并保持原样标记。
- 核心判据：每字段处理有规则和依据；清洗表直接支撑下游统计；全程可按记录复跑并逐字段核对。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 全字段抄 /app/work/order.json）；最小 result.json 先落盘。
2. 找四样东西：数据表（可多份）、数据字典（字段语义/单位/取值范围）、清洗工单（workorder：明确要求做哪几类）、QC 规则（逐指标）。缺字典 → 列 missing_dictionary 并按表头原样处理，units 标 unverified。
3. 快照：`snapshot.py`（原样副本+sha256+行数）。**后续全部操作只读快照副本。**

## 3. 工作流程

### Step 1 字段级规则推导（字典先行）

逐字段写 /app/work/rules.json（生成依据记进 rule_basis.tsv：`field, rule, dictionary_quote, source_location`）：

- missing_tokens：从字典/表内枚举值收集（空串/NA/N/A/-999/空格/未检出/<LOD 等）。**区分四类缺失**：`<LOD`/未检出 → 标记为 below_lod（保留原文本到 _raw 列）；录入缺失 → 空值；**不混淆为 0**。
- numeric_cols / date_cols：按字典类型。
- units：字典给出单位与目标单位 → 换算因子（如 mg/L→μg/mL ×1000）；换算保留 _raw_<col> 原值列，转换可逆。字典没写的单位 → 不换算，标 unverified。
- dedup.keys：按字典主键（样品编号/时间戳/受试者标识），不是整行比对；近似重复（大小写/空格/单位写法差异）先归一再比对。
- outliers：优先物理上下限（字典/QC 规则），无物理限才用 IQR(k=3)；**action 默认 flag**，drop/cap 必须有工单明示依据。

验收：rule_basis.tsv 每行有 dictionary_quote（没有字典依据的规则标 inferred+uncertainty）。

### Step 2 执行清洗（脚本留痕）

```bash
python3 $SKILL_DIR/scripts/clean.py /app/work/data.raw.csv /app/work/rules.json /app/output/cleaned
```

产出 clean.csv + cleaning_log.json（逐字段：动作/计数/受影响行号/策略）。内置原则：缺失只标记不填补；异常默认 flag；单位换算留原值列；去重只删主键重复且记录保留哪条。

### Step 3 质量对账（报告数字=结果表，硬门槛）

```bash
python3 $SKILL_DIR/scripts/qa_report.py /app/output/cleaned/cleaning_log.json /app/output/cleaned/clean.csv
```

断言：① log.n_rows_in/n_rows_out 与 clean.csv 实际行数一致 ② 每字段 missing 计数与 clean.csv 该列空值数一致 ③ 每个动作的行号存在 ④ 不存在"填补"类动作（impute 检查=0）。任一 FAIL → 修规则重跑。

### Step 4 result.json

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "cleaned_table": {"csv": "/app/output/cleaned/clean.csv", "rows_in": 0, "rows_out": 0,
                     "snapshot_sha256": "..."},
  "rules": {"rules_json": "/app/work/rules.json", "rule_basis": "/app/work/rule_basis.tsv",
             "n_rules": 0},
  "field_problem_list": [{"field": "...", "missing_n": 0, "outlier_n": 0, "dup_n": 0, "converted": true}],
  "quality_report": {"log": "/app/output/cleaned/cleaning_log.json", "qa_report": "pass"},
  "not_done": {"imputation": "禁止（组织方修订：不填补/不推断群体统计）", "imputed_cells": 0},
  "anomalies": [{"type": "unverifiable_unit", "detail": "..."}],
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

题面三大交付：分析结果（清洗表）/质量与复现证据（快照+规则+日志+代码+版本）/异常说明（不静默修改掩盖）。output_contract 逐字段落实。

## 5. 数字门槛

- 五类处理（缺失/异常/重复/格式/单位）按工单覆盖；未覆盖的在 not_done 说明。
- qa_report 全 PASS；imputed_cells=0；每个规则有字典依据或显式 inferred。
- 复跑：同输入+同 rules.json → 行数与逐字段计数完全一致（clean.py 无随机性）。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 无数据字典 | 按表头原样处理；units/类型标 unverified；partial 可接受 |
| 全列缺失/空表 | 该列进 anomalies，不删列；空表→failed |
| 编码乱码 | 检测编码（utf-8/gbk 尝试），转换记录进 log |
| 单位不明 | 不换算，_raw 保留，anomalies 记录 |
| 主键冲突 | 保留组内信息最完整行，冲突细节进 anomalies |
| 文件损坏/权限不足 | failed + 明确报错位置 |

## 7. 自查清单

- [ ] 快照 sha256；原文件未动
- [ ] rules.json + rule_basis.tsv（字典引用）齐
- [ ] 四类缺失区分；impute=0；异常默认 flag
- [ ] qa_report 对账全过
- [ ] result.json 契约字段全覆盖、status 如实

## 8. 效率约束

先最小 result；规则一次成型；对账失败最多修 2 轮；≤50 文件。

## 9. 最小示例

7 行脏表（缺失 token、重复行、单位换算、日期标准化）→ clean.py → cleaning_log 6 个动作留痕 → qa_report 对账 pass（见 README 自测记录，示例非正式案例结果）。


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

- workorder 类型: `cleaning_workorder`；spec 文件命名: `rules.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。


## 附录 D 四类缺失的区分细则（Step 1 执行核心）

| 原值 | 类别 | 处置 | 结果列表现 |
|---|---|---|---|
| "" / NA / N/A / -999 | 录入缺失 | 置空+计数 | 空单元格 |
| "未检出" / "<LOD" / "<0.01" | 低于检出限 | 原文本保留进 _raw_<col>，主列置空 | 空 + _raw 保留 |
| "0"（字典说明量程不含 0 时） | 可疑零值 | flag 进 anomalies，不改动 | 原值保留 |
| 空格/全角空格 | 格式故障 | strip 后按上述分类 | 归一后入库 |

## 附录 E 与聚合表场景的特别约定（组织方修订）

- 输入是发表聚合表的转录，不是原始实验数据：**不得推算个体数、不得补造分层数据、不得推断群体统计量**。
- 注入故障的典型形态（据题面）：编码错误、存储格式错位、单位错标——清洗时逐字段与字典对表，发现与字典冲突的写 anomalies 而非静默修。
- 报告口径："清洗后表"只含字典允许的变换（换算/归一/去重），其余原样保留。


## 附录 F 维护与版本

- 本版本 v1（2026-11-24）：脚本已在构建机实跑（README 自测记录）；迭代时新开 v2 目录并更新 README 差异说明。
- 依赖：仅 Python 3.8+ 标准库 + Pillow（PNG 渲染）；评测环境 scientific-python 兼容。
- 已知限制：p 值/F 分布为近似（stats 题）；PNG 在无 CJK 字体环境需 FIG_CJK_FONT。
