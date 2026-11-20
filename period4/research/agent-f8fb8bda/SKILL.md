---
name: deep-research-workflow
description: |
  深度研究 Agent Skill。多步研究任务的编排器：问题拆成可检索子问题 → 规划查什么/顺序
  → 调用检索/解析/计算工具取材 → 组织成有依据有边界的结论。全程可复核：每步留痕、失败
  可定位可恢复；结论区分材料事实/合理推断/无法确定。
---

# Deep Research Workflow — 深度研究 Agent Skill

## 1. 用途与适用范围

把"一段多步研究任务"跑成**可复核的流水线**：拆解→规划→取材→综合。四条纪律：任务边界清、输入输出固定、过程可复核、失败可定位可恢复。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究任务描述、可用工具清单（检索/解析/计算）与范围。
2. 明确任务边界：回答什么/不回答什么/可用哪些材料——边界写入计划。
3. 纳排规则（如适用）先于取材。

## 3. 工作流程

### Step 1 任务拆解与计划
- 研究任务 → 子问题 DAG：`{subq_id, 依赖, 检索策略, 预期产出}`——计划先行落盘，后续执行对照。

### Step 2 取材执行（步步留痕）
- 每步：`{step_id, action(检索/解析/计算), inputs, outputs(文件/记录), status}`。
- 工具调用失败：重试一次 → 仍失败则标注 failed_step + 依赖该步的子问题降级为"无法确定"，**不编造该步结果**。

### Step 3 证据组织
- 证据表：`{evidence_id, subq_id, 内容要点, 来源定位, 可比字段}`——跨材料对齐可比字段。

### Step 4 综合结论（有依据有边界）
- 结论分层：`material_fact`（材料直接陈述）/ `inference`（合理推断+推断链）/ `undetermined`（材料不足）。
- 每条结论带 evidence_ids；冲突证据并列不抹平。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "deep_research",
  "status": "success | partial | failed",
  "plan": [{"subq_id":"s1","depends":[],"strategy":"...","deliverable":"..."}],
  "steps_log": [{"step_id":"st3","action":"retrieval","inputs":["q:..."],"outputs":["e5","e6"],"status":"ok | failed | retried"}],
  "evidence_table": [{"evidence_id":"e5","subq_id":"s1","point":"...","source":{"file/doc":"...","locator":"..."},"comparable_fields":{}}],
  "conclusions": [{"text":"...","layer":"material_fact | inference | undetermined","evidence_ids":["e5"],"inference_chain":null}],
  "conflicts": [{"evidence":["e5","e8"],"note":"来源说法不一致"}],
  "failure_recovery": [{"step":"st4","failed_reason":"...","resume_from":"st3 产物"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：steps_log 全程留痕（成功/失败都记）；failed 步骤不编造；结论三层分层且带证据 ID；恢复路径明确。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 工具不可用 | 降级路径 + failed_step 登记该子问题 undetermined |
| 子问题超范围 | 边界外拒绝并说明 |
| 预算不足 | 按计划优先级完成核心子问题（partial） |

## 6. 自查清单

1. [ ] 计划先行且边界明确？
2. [ ] 每步留痕？失败可定位可恢复？
3. [ ] 结论三层分层、带证据 ID？
4. [ ] 冲突并列未抹平？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。计划与证据表结构先行；取材批处理；综合结论最后组装。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
