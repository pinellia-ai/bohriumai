---
name: coverage-gap-analyzer
description: |
  检索覆盖率与遗漏分析 Skill。拒绝四种失效：以结果定义分母、把没找到当不相关、归因
  泛泛、补检空转。用独立于检索结果的参照集做分母，遗漏显式列出并归因到具体查询式/字段/
  时间窗，补检必须报告新增命中。离线语料+组织方快照口径，覆盖率按有限快照表述。
---

# Coverage & Gap Analyzer — 检索覆盖率与遗漏分析 Skill

## 1. 用途与适用范围

对一次检索做诚实的覆盖率审计。四条铁律：
1. **分母独立**：应检文献集合来自参照标准（组织方提供的语料全集/已知相关集），不是检索结果自身反推；
2. **遗漏显式**：参照集中未命中的逐条列出，绝不从清单划掉了事；
3. **归因具体**：漏检原因落到"哪个查询式、哪个字段、哪个时间窗"，不写"数据库覆盖不足"；
4. **补检有效**：补充检索报告新增命中数，无新增=空转，如实报告遗漏未降。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、原检索过程记录（查询式+命中）、参照集（语料全集或已知相关文献清单）。
2. 盘点：参照集大小、原检索命中、字段可用性。参照集缺失→无法算覆盖率，如实报告并退化为定性分析。

## 3. 工作流程

### Step 1 分母确定（独立于结果）
- 参照集 = 组织方提供的文献全集/标注相关集。明确记录分母定义与大小。
- 禁止用检索命中反推应检集合。

### Step 2 命中对账
- 参照集 ∩ 检索命中 = 已检出；参照集 - 命中 = **遗漏清单**（逐条列出，含 ID）。
- 覆盖率 = |已检出 ∩ 参照相关集| / |参照相关集|，按快照口径表述（不宣称全局覆盖率）。

### Step 3 遗漏归因（落到可操作粒度）
- 每条遗漏检查：哪个查询式漏了它（逐查询式回放匹配）？哪个字段本可命中（标题/摘要/关键词）？哪个限定（时间窗/类型过滤）排除了它？
- 归因输出：`{record_id, missed_by_query:[...], fixable_field:"abstract 未检索", root_cause:"查询式q2未含术语X"}`。

### Step 4 补检设计与验证
- 针对每类归因设计补检查询式（补术语/补字段/放宽窗口）。
- 执行补检：**报告新增命中**；新增=0 的补检如实标注"空转，遗漏未下降"，删除该策略并说明。

### Step 5 汇总输出

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "coverage_gap_analysis",
  "status": "success | partial | failed",
  "denominator": {"definition":"组织方参照集","size":24,"independent_of_results":true},
  "coverage": {"retrieved_and_relevant":17,"missed":7,"rate_snapshot":0.71,"note":"有限快照口径"},
  "missed_list": [
    {"record_id":"r9","missed_by_queries":["q1","q3"],"fixable_field":"abstract",
     "root_cause":"q1 未含术语 'pyroptosis'，q3 时间窗截止2021（该文2022年）"}
  ],
  "supplementary_searches": [
    {"query":"...","new_hits":3,"effective":true},
    {"query":"...","new_hits":0,"effective":false,"note":"空转，已弃用"}
  ],
  "after_fix_coverage": {"rate_snapshot":0.83,"missed_remaining":4},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：denominator.independent_of_results=true 且属实；missed_list 完整（与 coverage 数字对账）；归因落到查询式/字段/窗口粒度；补检逐条报新增。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 参照集缺失 | 不算覆盖率，定性归因 + 明确声明 |
| 原检索记录缺失 | 无法归因到查询式 → 登记并要求补数据 |
| 预算不足 | 对账与遗漏清单优先，补检 partial |

## 6. 自查清单

1. [ ] 分母独立于检索结果？
2. [ ] 遗漏逐条列出并与覆盖率数字对账？
3. [ ] 归因具体到查询式/字段/时间窗？
4. [ ] 补检有效性（新增命中）如实报告？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。对账脚本化；逐查询式回放批处理；补检按归因优先级排序执行。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
