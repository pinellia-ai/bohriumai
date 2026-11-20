---
name: methods-stats-reviewer
description: |
  研究方法与统计审查 Skill。审查单式产出：研究设计、变量定义、统计方法、样本量、结果
  报告五维逐条审查——问题出在哪一段、哪类缺陷、严重程度、依据、怎么改。统计判断谨慎：
  只报可从稿件确认的问题，推断性结论标 needs_review。
---

# Methods & Stats Reviewer — 研究方法与统计审查 Skill

## 1. 用途与适用范围

五维审查单：研究设计（设计能否回答研究问题）、变量定义（操作性定义明确）、统计方法（检验选择与假设匹配）、样本量（依据/功效）、结果报告（量齐备：效应量/CI/精确 p）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、稿件（方法/结果段）、统计审查重点。
2. 判定边界：只对**稿件内可确认**的问题下结论；需要原始数据才能确认的 → needs_review。

## 3. 工作流程（五维逐条）

### D1 研究设计
- 设计类型 vs 研究问题匹配（相关设计回答不了因果问题）；对照设置；混杂控制声明。

### D2 变量定义
- 关键变量操作性定义（怎么测的）；自变量/因变量明确；缺失变量定义逐条列出。

### D3 统计方法
- 检验与数据类型/分布假设匹配（如连续非正态用非参）；多重比较校正；方法描述可复算（检验名+自由度/参数）。

### D4 样本量
- 报告了 n 吗？有依据（功效分析）吗？亚组样本量够吗？——只报稿件层面可确认项。

### D5 结果报告
- 效应量+CI+精确 p（不止"显著"）；检验与描述一致；表格数值与正文一致。

### 输出分级
每条：`{loc, 维度, 缺陷类型(设计缺陷 | 报告缺失 | 方法不当 | 表述含糊), severity: critical | major | minor, 依据(引用稿件原句), 修改建议}`。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "methods_stats_review",
  "status": "success | partial | failed",
  "findings": [
    {"issue_id":"m1","dimension":"stats_method","loc":{"section":"Methods para3"},
     "defect":"method_misuse | reporting_missing | design_flaw | vague",
     "severity":"major","quote":"稿件原句","basis":"连续变量未检验正态性即用t检验（稿件未声明检验）",
     "suggestion":"补充正态性检验或改用非参检验"}
  ],
  "per_dimension": {"design":{"checked":true,"issues":["m3"]},"variables":{},"stats":{},"sample_size":{},"reporting":{}},
  "needs_review": [{"item":"功效分析是否充分","reason":"需原始数据与效应量假设"}],
  "stats": {"critical":0,"major":3,"minor":5},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：findings 每条有维度+缺陷类型+severity+稿件原句依据+具体建议；统计推断谨慎（needs_review 不硬下结论）；五维全覆盖。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 统计细节稿件未报告 | 报告缺失类缺陷（不是推断错误） |
| 需原始数据判断 | needs_review |
| 预算不足 | D1/D3（设计+统计方法）优先 |

## 6. 自查清单

1. [ ] 五维全覆盖？
2. [ ] 每条有原句依据+具体建议？
3. [ ] 统计判断谨慎（needs_review 分离）？
4. [ ] 可交办（位置/严重度齐）？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。五维批量扫描；统计术语核对清单辅助；输出按 severity 排序。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
