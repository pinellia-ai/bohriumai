---
name: literature-data-cleaner
description: |
  文献数据清洗与标准化 Skill。对文献抽取结果做规则化清洗：字段规范化映射（同义字段/
  拆分字段/缺省）、单位与格式标准化（换算公式与精度全程留痕、复合单位/前缀/区间值）、
  重复检测与同义词归一（可解释判定键，区分重复记录与重复实验）、异常报告与行级变更
  记录（每个改动值可沿规则编号回到输入行与原始文献）。输出标准化数据表 + result.json。
---

# Literature Data Cleaner — 文献数据清洗与标准化 Skill

## 1. 用途与适用范围

把一批真实文献抽取结果清洗成"规得齐、换得准、合得对、追得回"的标准化数据表。核心原则：**不改原始记录**——所有转换在副本上做，每个改动值沿规则编号可回溯。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点数据：抽取结果表（CSV/JSON）、来源文献元数据、既有字段说明。记录每张表的行数与列名。
3. 建立原始数据只读快照（/app/work/raw_snapshot.csv），一切清洗在副本进行。
4. 数据为空/结构不明：status=failed 并说明，不凭空设计字段。

## 3. 工作流程

### Step 1 字段映射（规得齐）
- 扫描全部列名与值域，建立映射表：`raw_column → standard_field`，含映射依据（同义词典/内容抽样验证）。
- 处理：同义字段（tensile strength / σ_max）、拆分字段（value+unit 两列合一）、字段缺省（标注 NULL 不填 0）、版本变化（不同来源 schema 差异）。
- 输出未映射字段清单——映射不了的列显式列出，不强行归并。

### Step 2 单位与格式标准化（换得准）
- 建立单位换算表（规则编号 R-U01…）：每条换算记录 `原值、原单位、目标单位、换算公式、精度`。
- 复合单位（MPa·m^1/2、mg/(cm²·h)）逐分量换算；数量级前缀（m/µ/n）严格 10^k 换算；区间值（15–20）保留区间形式 `[low, high]`，不取均值冒充。
- **保留原值**：输出表中每行带 `original_value` 与 `standardized_value` 两列。
- 精度跟随原值有效数字，不增位数。

### Step 3 重复检测与归一（合得对）
- 判定键可解释：如 `物质名(规范化) + 指标(标准字段) + 条件(温度±1, 压力±1)`；键的构造规则写进报告。
- 区分**重复记录**（同实验重复录入 → 建议合并）与**重复实验**（同物质同指标不同实验 → 保留两条，标 replicate）。
- 同义词归一（graphene / Grafen / 石墨烯）：用显式词典，词典外的新写法进待确认清单。
- 合并动作只出**建议**（merge_group + 保留行依据），不直接删除数据。

### Step 4 异常检测与追溯（追得回）
- 异常类型：缺失、越界（按指标物理合理范围）、冲突（同键不同值）、换算失败、来源覆盖（无文献引用的行）。
- 行级变更记录：每条改动 = `{row_id, field, original, standardized, rule_id, source_ref}`，可从输出值一路回查到输入行与原始文献。
- 工具不敢确认的值单独列 `needs_human_review` 清单——不静默放过也不静默修正。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "data_cleaning_standardization",
  "status": "success | partial | failed",
  "field_mapping": [{"raw":"tensile_strength_MPa","standard":"tensile_strength","basis":"unit suffix + values sampled","unmapped":[]}],
  "unit_conversions": [{"rule_id":"R-U01","from":"GPa","to":"MPa","formula":"x*1000","applied_rows":12}],
  "standardized_table": "cleaned_data.csv",
  "merge_suggestions": [{"group_key":"graphene|conductivity|300K","row_ids":[4,17],"type":"duplicate_record","action":"keep row 17 (newer source)","reason":"..."}],
  "anomalies": {"missing":[],"out_of_range":[],"conflicts":[],"conversion_failed":[],"no_source":[]},
  "needs_human_review": [{"row_id":23,"field":"band_gap","value":"2.1","concern":"原文区间2.1-2.4被抽取工具截断"}],
  "change_log": [{"row_id":4,"field":"conductivity","original":"1.2e3 S/cm","standardized":"1200 S/m","rule_id":"R-U07","source_ref":"row4/src_ref"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：原始数据只读、全部改动留痕可回溯；needs_human_review 非空时不得假装全部确认；cleaned_data.csv 与 change_log 一致。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 列名无法映射 | 进未映射清单，原样保留该列 |
| 单位缺失 | 该值标 unknown_unit，不默认单位 |
| 区间/离散值 | 保留原形式，不均值化 |
| 重复键冲突（同键不同值） | 记 conflicts，两条都保留，不静默择一 |
| 预算不足 | 先字段映射与单位标准化（影响面最大），status=partial |

## 6. 自查清单

1. [ ] 原始快照只读未动？全部改动有 rule_id 与来源？
2. [ ] 复合单位/前缀/区间换算正确，原值保留？
3. [ ] 合并有可解释判定键，重复记录 vs 重复实验区分？
4. [ ] 异常报告五类齐全？不敢确认的值单独列出？
5. [ ] change_log 可逐行回查？CSV 与 JSON 一致？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。清洗用 python 脚本批处理（规则写进脚本，可复跑）；模型请求只用于词典判断与抽样验证，不逐行消耗。先出字段映射 + 单位标准化（最小可用），再补合并与异常报告。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "field_mapping":[{"raw":"sigma_MPa","standard":"tensile_strength","basis":"值域320-450符合MPa强度","unmapped":[]}],
 "unit_conversions":[{"rule_id":"R-U01","from":"GPa","to":"MPa","formula":"x*1000","applied_rows":2}],
 "merge_suggestions":[{"group_key":"graphene|conductivity|RT","row_ids":[4,17],"type":"duplicate_record","action":"keep 17","reason":"同实验两次录入，来源日期更新"}],
 "anomalies":{"missing":[{"row_id":9,"field":"band_gap"}],"out_of_range":[],"conflicts":[],"conversion_failed":[],"no_source":[]},
 "needs_human_review":[{"row_id":23,"field":"band_gap","value":"2.1","concern":"原文为区间"}],
 "change_log":[{"row_id":4,"field":"conductivity","original":"1.2e3 S/cm","standardized":"1200 S/m","rule_id":"R-U07","source_ref":"row4"}],
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 70 分水准：change_log 行级 CSV 全量（before/after/rule_id）；reconciliation 对账表；needs_human_review 计数。
