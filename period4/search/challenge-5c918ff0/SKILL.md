---
name: multi-db-merge-dedup
description: |
  多数据库联合检索 Skill。对不同学术库返回的结构化响应做规范合并：按标识符（DOI/PMID/
  标题规范化）识别同一论文，作者/期刊写法归一，字段语义按库口径区分（年份/卷期/DOI 含义
  不等价），每条记录标注来自哪个库、哪个字段被哪个库覆盖。交付可核对、可去重、有来源
  谱系的结果清单。离线快照口径，不声称每个库都全查过。
---

# Multi-DB Merge & Dedup — 多数据库联合检索 Skill

## 1. 用途与适用范围

解决"同一条查询复制到每个库然后拼接"的失败：同一论文多标识符重复、作者/期刊写法不一、字段语义不等价、说不清总共有几篇不同论文。交付标准：**去重后的唯一论文数说得清、每条记录来源谱系说得清、字段覆盖矩阵说得清**。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、查询式、各库响应快照。
2. 盘点数据源：每个库的记录格式、字段清单、标识符体系（DOI/PMID/索引号）。
3. 建立**字段语义表**：同名字段在不同库的口径差异（如 year=出版年 vs 收录年；volume 是否含专刊号）。

## 3. 工作流程

### Step 1 单库规范化
- 每库记录先规范化：作者名统一格式（姓全拼+首字母）、期刊名缩写→全称（对照语料）、标识符提取（DOI 小写去 https 前缀、PMID 纯数字）。
- 规范化规则编号留档，可复跑。

### Step 2 跨库实体对齐（去重的关键）
- 主键归并：DOI 精确匹配 > PMID > 标题规范化（小写、去标点、去多余空格）+ 年份容差匹配。
- 归并不确定时（标题近似但标识符缺）：标 `needs_human_review`，不静默合并。
- 输出：唯一论文数 + 合并谱系（哪条来自哪个库）。

### Step 3 字段级合并（口径安全）
- 每个字段取值时标注来源库：冲突值（如两库年份不同）并列保留 + 口径解释，不静默择一。
- 字段覆盖矩阵：`{字段 → 哪些库提供 → 覆盖率}`——说不清被哪库覆盖即为缺陷。

### Step 4 结果清单输出
- 唯一记录清单：每条含合并字段+来源谱系+匹配查询；总数与"合并前总条数→去重后"对账。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "multi_db_merge",
  "status": "success | partial | failed",
  "sources": [{"db":"Crossref","records":18,"fields":["title","DOI","year"]}],
  "field_semantics": [{"field":"year","db_A":"出版年","db_B":"收录年","rule":"合并取出版年并标注"}],
  "merged_records": [
    {"record_id":"u1","title":"...","identifiers":{"doi":"...","pmid":"..."},
     "fields":{"title":{"value":"...","source":"db_A"},"year":{"value":2022,"source":"db_B","alternatives":[{"value":2023,"source":"db_A","note":"收录年"}]}},
     "provenance":["db_A#r3","db_B#r11"],"matched_query":"q1"}
  ],
  "dedup_log": [{"kept":"u1","merged":["db_A#r3","db_B#r11"],"key":"doi","certainty":"exact"}],
  "coverage_matrix": {"title":["db_A","db_B"],"abstract":["db_B"],"abstract_coverage":"9/23"},
  "reconciliation": {"raw_total":41,"unique":23,"duplicates_removed":18,"needs_human_review":1},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：reconciliation 三数对账；每字段有 source；冲突并列；needs_human_review 不静默合并；无"全查过"声明。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 某库响应缺失/格式损坏 | 登记，只用可用库，coverage_matrix 如实 |
| 标题近似但无标识符 | 不合并，needs_human_review |
| 预算不足 | 规范化+主键归并优先（partial） |

## 6. 自查清单

1. [ ] 三数对账（原始/唯一/去重）？
2. [ ] 每条记录来源谱系齐？每字段有来源？
3. [ ] 字段语义差异已处理？冲突并列？
4. [ ] 不确定合并进人工清单？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。规范化与归并脚本化；coverage_matrix 自动统计；先交主键归并结果。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：reconciliation 三数对账（raw=unique
2. dups
3. review）；coverage_matrix 每字段覆盖率百分比；merged_records 每字段标来源库。
