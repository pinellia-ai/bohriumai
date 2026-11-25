---
name: literature-data-clean-standardize
description: |
  文献数据清洗与标准化：把带来源的抽取记录清洗成可统计数据表，规则库有编号
  可增删，单位换算保留原值并写出公式与精度，去重按可解释判定键，每条改动沿
  规则编号回到输入行。缺值保持空缺、未知单位标 unknown，不编造、不越权裁决
  科学冲突；先落盘最小 result.json 再充实。
---

# 文献数据清洗与标准化 Skill — 规则编号 + 行级追溯（v1）

## 1. 用途与适用范围

- 适用：把一批文献抽取记录（表格/JSONL/CSV）端到端清洗成可统计数据表：字段规范化、单位换算、同义归一、重复检测、异常报告，附行级变更记录与待人工确认清单。
- 不适用（不做也不报）：科学冲突的实质性裁决（只标 conflict 转人工）、数据补全插值、原始记录改写。
- 四个验收问题（主线）：
  1. **规得齐**：同指标统一字段名/类型/允许值集合。
  2. **换得准**：单位转换保留原值、写出公式与精度，复合单位/前缀/区间不出错。
  3. **合得对**：合并按可解释判定键，区分"重复记录"与"重复实验"。
  4. **追得回**：每个改动沿规则编号回到输入行；不敢确认的值单独列出。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段——result.json 逐字段落实；case.json 优先于本文。
2. 读 `/input/task.md`：确认指标范围、目标单位与"算对"标准。
3. 盘点材料：登记每个输入文件的行数/列名/编码。组织方注入的格式差异、重复抽取、缺值和未知单位**有明确身份标注时照单执行**，不当原作者数据篡改。
4. 材料缺失/空表 → status=failed + failure_reason；编码错乱先记录再尝试恢复，不硬猜。

## 3. 工作流程（六步流水线）

### Step 1 规则库初始化（→ /app/work/rules.jsonl）

规则条目格式（有编号、有优先级、可增删）：

```json
{"rule_id": "R001", "category": "field_norm | unit_convert | syn_norm | dedup | missing | range",
 "priority": 1, "applies_when": "<适用条件>",
 "action": "<操作描述>", "formula": "<换算公式，如 v_kPa = v_bar * 100>",
 "precision_policy": "keep_original | round:<n>",
 "fails_when": "<失效情形>", "conflict_resolution": "lower_rule_wins | escalate_manual"}
```

- 预置最小规则集 ≥10 条（字段规范化 3、单位换算 3、同义归一 2、去重 2）；案例中遇到未覆盖情况**新增规则并登记 rule_id**，不改写已有规则语义。
- 验收断言：rules.jsonl 每条字段齐全、rule_id 唯一、priority 可排序。

### Step 2 字段规范化（→ /app/work/normalized.jsonl）

- 按 rules.jsonl 的 field_norm 规则执行：列名映射（同义字段表）、类型转换（数值/文本/区间）、允许值集合校验。
- 未映射字段**不删除**：进 `unmapped_fields` 清单。
- 每行保留：`{row_id, input_ref: {file, line_no}, raw_record, normalized_record, applied_rules: [rule_id]}`。
- 验收断言：行数与输入一致（不丢行）；每行 applied_rules 可反查。

### Step 3 单位与格式换算（→ 合并进 normalized.jsonl）

- 换算纪律：**原值永不改动**——输出 `{"value_raw": <原始串>, "unit_raw": "", "value_std": <数值>, "unit_std": "<目标单位>", "formula": "R003: v=v_raw*100", "precision_note": "<精度说明>"}`。
- 复合单位（如 mL/min·g）按分子分母逐因子换算；数量级前缀（μ/m/k/M）查表；区间值（10-20）转成 `{low, high, unit}` 两字段。
- **单位未知/无法识别**：`unit_std=null` + flag=`unknown_unit`，不猜测换算。
- 验收断言：脚本 spot-check 换算公式（往返换算误差 < 1e-9）；unknown_unit 条目逐条登记。

### Step 4 重复检测与同义归一（→ /app/work/dup_report.json）

- 判定键（可解释）：`{物质归一键, 指标归一键, 条件键}` 三元组相同 → 候选重复；**仅名字相同、条件不同 → 不同实验，不合并**。
- 每组候选输出：`{group_id, member_row_ids, merge_basis, action: merged|kept_separate|needs_review}`；数值不一致的候选重复 → needs_review，不自动取值。
- 同义词归一按 syn_norm 规则 + 归一依据；无依据的写法保持原样。
- 验收断言：每组合并有 merge_basis；needs_review 清单非空时逐条写原因。

### Step 5 异常报告与导出（→ /app/output/clean_data.csv + anomaly_report.json + change_log.jsonl）

- 可统计数据表 `clean_data.csv`（UTF-8，标准列名，缺值空缺不填 0）。
- 异常报告按类计数与明细：`missing / out_of_range / conflict / unit_unknown / encoding_error / source_coverage`。
- **行级变更记录** `change_log.jsonl`：`{row_id, field, before, after, rule_id, input_ref}`——任何被改动的值 100% 有条目。
- 待人工确认清单 `needs_review.jsonl`：科学冲突、needs_review 重复、unknown_unit。
- 验收断言：change_log 条数 = 被改动单元格数（脚本对账）。

### Step 6 result.json 组装（先最小后充实）

- 进入 Step 2 前写最小 result.json（status=partial）；走完覆盖完整版。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "cleaning": {
    "input_rows": 0, "output_rows": 0, "fields_mapped": 0, "unmapped_fields": [],
    "rules_applied": ["rule_id 计数表"], "rules_library": "rules.jsonl"
  },
  "conversions": {"count": 0, "spot_check_pass": true, "unknown_unit_count": 0},
  "dedup": {"groups": 0, "merged": 0, "kept_separate": 0, "needs_review": 0},
  "anomaly_report": {"missing": 0, "out_of_range": 0, "conflict": 0, "details_file": "anomaly_report.json"},
  "traceability": {"change_log": "change_log.jsonl", "changed_cells": 0, "log_matches_changes": true},
  "evidence_and_boundary": {
    "not_reported": ["<材料未提供项>"],
    "no_fabrication_check": "缺值保持空缺，无插值/无编造",
    "manual_review_file": "needs_review.jsonl"
  },
  "run_status": {"state": "", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["<实际输入文件>"],
  "uncertainty_notes": ["<科学冲突、存疑归并>"],
  "change_log": []
}
```

## 5. 数字门槛（达不到诚实标 partial）

1. 行数守恒：input_rows = output_rows + 显式登记的剔除行（剔除也要留记录）。
2. 100% 被改动值有 change_log 条目且 rule_id 可反查；输入行可回溯（file+line_no）。
3. 换算 spot-check 往返误差 < 1e-9；unknown_unit 不猜换算。
4. 缺值空缺率 = 报告值（不填 0 不插值）；needs_review 逐条有原因。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 单位无法识别 | flag=unknown_unit，不换算，进 needs_review |
| 同义字段冲突（两个映射候选） | 按规则 priority 取优先者并登记，未决进 needs_review |
| 数值越界 | 不删行，标 out_of_range，保留原值 |
| 科学冲突（同指标两值矛盾） | 标 conflict 双列保留，**不裁决**，转 needs_review |
| 编码错乱 | 记录原始字节，按检测编码恢复；恢复失败的行标 encoding_error 保留 |
| 空表/全缺列 | status=partial + failure_reason，不虚构行 |
| 重复但条件不同 | kept_separate，注明"重复实验非重复记录" |
| output_contract 与本文冲突 | 以 case.json 为准 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] 规则库有编号可增删；每条改动带 rule_id
- [ ] 原值保留、换算公式与精度可见；unknown_unit 不猜
- [ ] 去重按判定键；needs_review 不自动合并
- [ ] 行数守恒；change_log 与改动对账通过
- [ ] 缺值空缺、无编造；冲突不裁决

## 8. 效率约束

预算 64 请求 / 900 秒。策略：全部用 Python 脚本执行（scripts/clean_pipeline.py：规范化→换算→去重→报告一次跑通）；模型请求只用于同义关系判断与冲突描述；先落盘最小 result.json。限额 ≤50 文件 / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"row_id":"r007","input_ref":{"file":"extract_records.jsonl","line_no":7},
 "value_raw":"1.2","unit_raw":"bar","value_std":120.0,"unit_std":"kPa",
 "formula":"R002: kPa = bar * 100","precision_note":"1.2 bar 3位有效数字，std 保留3位有效","applied_rules":["R002"]}
{"group_id":"G01","member_row_ids":["r003","r011"],"merge_basis":"物质+指标+条件键相同且数值一致","action":"merged"}
{"group_id":"G02","member_row_ids":["r004","r012"],"merge_basis":"物质相同但温度条件不同（300K vs 350K）","action":"kept_separate","note":"重复实验非重复记录"}
```

（以上为格式示意，正式结果以实际材料运行为准。）
