---
name: deep-research-agent
description: |
  深度研究 Agent Skill：把一段多步研究任务走完"问题拆解→检索规划→多步工具调用→证据综合"全链路，交付可复跑、可回链的研究结论。
  方法主线：拆解树（子问题可独立检索+依赖标注）→检索计划（顺序/来源/停止条件，避免重复查同批文献）→
  每次工具调用留参数与返回记录（tool_calls.jsonl）→证据表（结论句↔文献段落一一对应）→冲突证据并列不取一方→
  研究空白必须基于检索缺口。材料内结论标 material_fact，推断标 inference，查不到标 unverifiable，绝不越界。
---

# 深度研究 Agent（Decompose · Plan · Orchestrate · Synthesize）

## 1. 用途与适用范围

- **做**：给定一个研究问题与材料/工具集，产出：拆解树、检索计划、带记录的多步工具调用、证据表、综合结论、研究空白。验收三件事：拆解出的子问题可独立检索；每条结论回链到文献段落；整条路径他人可按记录复跑。
- **不做**：单篇逐句精读、元数据方法学审查、翻译润色。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、研究问题、材料清单（本地文件/题录）、可用工具、输出要求。
2. 读 task.md 确认：证据范围、时间窗、比较对象。
3. 材料与工具全缺失 → status=failed。

## 3. 工作流程（五步）

### Step 1 问题拆解（产物 decomposition.json）
识别：研究对象、机制/干预、比较基线、时间范围、证据要求 → 拆成子问题清单，每条：
`{sq_id, question, search_action(检索词/检索式), depends_on[], evidence_type(定量/定性/事实)}`
- 拆解不停留在关键词改写：每个子问题必须能独立发起一次检索并独立判定是否已答。
- 依赖标注：如 SQ3"剂量-效应关系"依赖 SQ2"剂量范围"的前置结果。

### Step 2 检索计划（产物 search_plan.json）
- 为每个 sq 安排：顺序（先依赖前置）、来源范围（本地材料/在线库）、停止条件（如"连续 2 次检索无新增相关文献即停"，**写死在计划里**）。
- 去重约束：同一来源+同一检索式不得重复执行；新检索必须提供与既有 sq 不同的增量词。

### Step 3 多步工具调用（产物 tool_calls.jsonl）
- 每次调用记录：`{call_id, sq_id, tool, params, returned_summary, result_count, failed?, retry_of?}`。
- 中间产物可复用：解析出的证据块存 evidence_pool.json（`{ev_id, sq_id, source, locator, snippet}`），后续步骤引用 ev_id，不重复解析。
- 检索为空/工具报错：记录并触发降级（换检索词→换来源→标记该 sq unresolved），不无限重试（每 sq ≤3 次）。

### Step 4 证据综合（产物 evidence_table.csv/json）
- 每行：`{ev_id, sq_id, source(文献标识), locator(文件+页/段), snippet(原文片段), finding, evidence_strength(strong/moderate/weak), conflicts_with[]}`。
- 结论句与证据行一一对应：综合结论（synthesis.json）里每个结论句带 `supported_by: [ev_id...]`。
- **冲突处理**：结论相反的文献并列呈现（conflicts 表），写明各自证据位置与强度，不得只取一方或写"尚存争议"了事。
- 表述强度三档：已被证明（≥2 独立来源且无冲突）/ 有提示性证据（单来源）/ 仍有争议（有冲突证据）。

### Step 5 研究空白与交付（→ /app/output/result.json）
- 空白必须引用检索缺口：`{gap, basis: "sq X 在 N 次检索（词表…）后无命中/仅弱证据", excluded: 排除条件}`——禁止凭空判断。
- 汇总写 result.json（§4），区分 material_fact（材料内事实）/ inference（推断，附推理链）/ unverifiable（查不到，附检索记录）。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "decomposition": {"sq": [{"sq_id": "SQ1", "question": "...", "search_action": "...", "depends_on": [], "evidence_type": "quantitative"}]},
  "search_plan": {"queries": [{"sq_id": "SQ1", "order": 1, "sources": ["local"], "query": "...", "stop_rule": "2连空停"}]},
  "tool_calls": "tool_calls.jsonl（每次调用的参数与返回记录）",
  "evidence_table": [{"ev_id": "E1", "sq_id": "SQ1", "source": "Smith 2023", "locator": "results.pdf#page=5,para=2",
                       "snippet": "...", "finding": "...", "evidence_strength": "strong"}],
  "synthesis": [{"claim": "结论句", "supported_by": ["E1", "E3"], "strength": "已被证明|有提示性证据|仍有争议",
                  "type": "material_fact|inference", "inference_chain": "仅 inference 时填"}],
  "conflicts": [{"topic": "...", "ev_a": "E1", "ev_b": "E4", "resolution": "并列呈现+强度对比"}],
  "gaps": [{"gap": "...", "basis": "检索缺口描述", "queries_tried": [...]}],
  "uncertainty": ["SQ3 unresolved：材料与检索均无定量数据"],
  "operation_evidence": {"files": ["decomposition.json", "search_plan.json", "tool_calls.jsonl", "evidence_table.json"],
                          "rerun_cmd": "按 search_plan 顺序重放 tool_calls 可复现 evidence_table"}
}
```

## 5. 数字门槛

- 回链率 100%：synthesis 每条 claim 的 supported_by 至少 1 条 ev，且 ev.locator 可在源文件定位。
- 冲突率对账：evidence_table 中标记 conflicts_with 的行全部出现在 conflicts 表。
- 空白有据率 100%：gaps 每条带 queries_tried。
- 工具调用记录完整率 100%：tool_calls.jsonl 行数 ≥ search_plan.queries 数。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 检索为空 | 换词一次→换源一次→sq 标 unresolved，记入 gaps |
| 工具报错/限流 | 记 failed+retry_of，≤3 次/查 |
| PDF 解析失败 | 该文献记 unreadable，不入证据表 |
| 证据冲突 | conflicts 并列，不取一方 |
| 依赖未完成 | 按 depends_on 等待，未完成的前置标 unresolved 后下游跳过 |
| 预算将尽 | 先落盘 result.json 最小版（已有证据+已答 sq） |

## 7. 自查清单

- [ ] case_id 原样；拆解非关键词改写（每 sq 有 search_action+判定标准）。
- [ ] 每条结论有 ev 回链；冲突并列；空白有检索缺口依据。
- [ ] tool_calls.jsonl 可重放；material_fact/inference/unverifiable 三分明确。

## 8. 效率约束

检索计划一次性生成（1 次模型调用），执行按 plan 顺序脚本化重放；模型请求预算分配：拆解 1、计划 1、综合 ≤4、复核 1，其余留给兜底。900s 内先出最小 result.json 再充实。

## 9. 最小示例（示意输出，非正式案例结果）

问题："X 蛋白在 Y 疾病中的剂量-效应关系？"
拆解：SQ1 X 与 Y 的相关性证据 → SQ2 X 的剂量范围 → SQ3(依赖 SQ1,SQ2) 剂量-效应定量关系。
结论示例：`{"claim": "X 在 0.5-2 mg/kg 区间与 Y 指标呈负相关", "supported_by": ["E2", "E5"], "strength": "有提示性证据", "type": "material_fact"}`
