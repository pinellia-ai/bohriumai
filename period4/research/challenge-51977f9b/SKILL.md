---
name: systematic-review-workflow
description: |
  系统性文献综述 Skill。一条可沿着重走的流程：研究问题结构化 → 检索式（库/字段/时间/
  语言限制留档）→ 两轮筛选（题录+全文，逐条排除理由）→ 质量评价 → 证据表综合 → 冲突
  与空白。各环节数目首尾对账（PRISMA 式）；离线语料口径，不编造检索命中。
---

# Systematic Review Workflow — 系统性文献综述 Skill

## 1. 用途与适用范围

别人能沿着走一遍的系统综述流程：结构化问题 → 留档检索 → 两轮筛选 → 质量评价 → 证据综合 → 冲突与空白。全部环节数目可对账。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究问题、语料快照（题录/全文）、既有标准。
2. 协议前置：纳排标准 v1 版本化后才开始筛选。

## 3. 工作流程

### Step 1 问题结构化与检索留档
- PICO/研究问题拆解 → 检索式：`{语料源, 查询式, 字段, 时间范围, 语言限制}`——全部留档（离线快照口径，声明非实时）。

### Step 2 两轮筛选
- 题录轮：按标题/摘要判纳入潜力，逐条留理由；全文轮：对题录轮纳入者读全文判定，排除逐条给标准号+依据。
- 计数流：`识别 N → 去重 → 题录筛后 → 全文筛后 → 纳入`，首尾对账。

### Step 3 质量评价
- 纳入研究按固定维度（设计/样本/对照/统计/偏倚）评级，判断锚定原文。

### Step 4 证据综合
- 证据表：`{研究, 设计, 样本, 关键结果, 条件, 质量级}`——可比字段对齐。
- 综合结论：一致/部分一致/冲突逐主题给出；冲突并列双方数据。
- 研究空白：由纳入集边界推导（"纳入研究均未覆盖 X"），不把"没检索到"当空白。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "systematic_review",
  "status": "success | partial | failed",
  "protocol": {"question_structure":"...","search_log":[{"source":"快照","query":"...","fields":[],"time":"..."}],"criteria_version":"v1"},
  "prisma_counts": {"identified":60,"deduped":48,"title_screened_in":20,"fulltext_in":11,"included":11,"reconciled":true},
  "screening_log": [{"paper":"...","round":"title | fulltext","decision":"included | excluded","criteria":"E2","reason":"..."}],
  "quality": [{"paper":"...","grades":{"design":"medium","sample":"low","bias":"moderate"},"basis_loc":"..."}],
  "evidence_table": [{"paper":"...","design":"...","n":30,"key_result":"...","conditions":"...","quality":"medium"}],
  "synthesis": {"themes":[{"topic":"...","verdict":"consistent | partial | conflict","papers":[],"note":"..."}],
                "gaps":[{"gap":"纳入研究均未覆盖 X","basis":"纳入集边界"}]},
  "gaps": [], "uncertainty_notes": ["离线快照，非实时检索"], "changes": []
}
```

硬性要求：prisma_counts 对账；screening_log 逐条带标准号+理由；质量评价锚定原文；空白由纳入集边界推导。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 全文缺失（仅题录） | 全文轮降级并声明 |
| 标准中途变更 | 版本记录 + 重判受影响项 |
| 预算不足 | 协议+筛选+对账优先（partial） |

## 6. 自查清单

1. [ ] 检索式与限定全部留档？
2. [ ] 两轮筛选逐条理由？计数对账？
3. [ ] 质量评价锚原文？
4. [ ] 冲突并列？空白由边界推导？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。协议与计数流先行；筛选批处理；综合最后组装。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
