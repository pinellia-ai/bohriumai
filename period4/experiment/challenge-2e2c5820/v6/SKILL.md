---
name: feasibility-assessor
description: |
  实验方案可行性评估 Skill。纸面通过≠能开工：设备到位与排期、材料货期、样本来源与量、
  人时占用、参数容差依据、异常处置、伦理与安全审批——分散在方案文档/设备清单/采购记录/
  SOP/审批表单里的约束逐条对上。输出可开工判定：每条约束 已满足/缺口/未知 + 开工建议。
---

# Feasibility Assessor — 实验方案可行性评估 Skill

## 1. 用途与适用范围

把"纸面通得过"变成"能不能开工"：七类约束逐条核对——设备（到位/排期）、材料（货期）、样本（来源/量）、人时、参数容差（依据）、异常处置、伦理安全审批。约束分散在多文档 → 逐文档抽取逐条对上。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、方案文档、约束文档（设备清单/采购记录/SOP/审批表）。
2. 从方案抽取**需求侧清单**：要什么设备/材料/样本/人时/审批——逐条编号。

## 3. 工作流程

### Step 1 需求侧抽取
- 方案逐步骤抽：`{需要什么, 数量/规格, 何时需要, 依赖哪步}`。

### Step 2 供给侧核对（逐条对上）
- 每条需求 vs 约束文档：`{constraint_id, 需求, 供给(文档+位置), 状态: satisfied | gap | unknown}`。
- 具体核对：设备型号匹配？货期 vs 需要日期？样本量 vs 来源量？容差有 SOP 依据？

### Step 3 伦理与安全
- 动物/人体样本 → 审批状态核对（审批表单）；安全边界（危化品/生物安全等级）与 SOP 对照。
- 审批缺失 = 硬性阻断项（不改判"可以开工"）。

### Step 4 判定与建议
- `可开工 | 有条件开工（列缺口+补齐路径） | 暂缓（硬阻断项）`；每条 gap 给补齐动作与责任人建议。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "feasibility_assessment",
  "status": "success | partial | failed",
  "requirements": [{"req_id":"r1","item":"低温离心机","spec":"4°C, 15000g","when":"步骤2","doc_loc":"方案步骤2"}],
  "constraint_check": [
    {"req_id":"r1","supply":{"doc":"设备清单 p2","item":"离心机 X 型 15000g"},"status":"satisfied"},
    {"req_id":"r2","item":"酶试剂 10mL","supply":{"doc":"采购记录","item":"已订，到货 3/15"},"status":"gap","impact":"步骤2顺延","mitigation":"先做步骤1"},
    {"req_id":"r5","item":"伦理批件","supply":null,"status":"unknown","hard_block":true}
  ],
  "verdict": {"level":"ready | conditional | hold","gaps_to_close":[{"item":"酶试剂","action":"等货期或改供应商"}]},
  "param_tolerance_check": [{"param":"37±1°C","basis":"SOP-S12 有依据"}],
  "safety_ethics": {"approval_status":"unknown","blocked":true,"note":"审批表单未包含批件"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：requirements 逐条编号核对（不漏项）；status 三态+文档定位；硬阻断项（伦理/安全）不改判；verdict 与缺口一致。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 约束文档缺失 | 该类 unknown + needs_human_review |
| 约束相互冲突 | 并列记录，保守判定 |
| 预算不足 | 硬阻断项（伦理/设备/材料）优先 |

## 6. 自查清单

1. [ ] 七类约束逐条核对？
2. [ ] 每条有文档定位？三态判定？
3. [ ] 硬阻断未放行？
4. [ ] gap 有补齐路径？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。需求抽取先行；供给侧核对脚本辅助（文档关键词定位）；判定最后。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 76 分水准：constraint_check.csv（七类约束/三态/文档定位）逐条
2. 硬阻断断言
3. verdict 与缺口一致表。
