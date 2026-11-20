---
name: proposal-stage-planner
description: |
  开题报告与研究计划书 Skill。四问对齐：研究问题具体可证伪（背景真指向缺口而非综述
  空转）、目标-路线-验证-成果一一对应、阶段计划落在周期/经费/数据/人员条件内（里程碑
  与任务量匹配）、风险带触发信号+备选方案+决策时点。关键论断引用可追溯，交付可编辑
  源文件。七要素/计划一致性约束依 case.json。
---

# Proposal Stage Planner — 开题报告与研究计划书 Skill

## 1. 用途与适用范围

立得住（缺口陈述而非文献罗列）、对得上（目标↔路线↔验证↔成果逐条对应）、排得开（计划匹配资源条件）、说得清（风险有信号与备选、论断可追溯）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、课题指南/材料、周期/经费/人员约束、写作要求（七要素约束如有）。
2. 从指南+前期数据+文献抽"已知—未知—待验证"三级缺口陈述素材。
3. 材料缺失登记；申请人证据缺失按骨架+标注（不虚构）。

## 3. 工作流程

### Step 1 缺口陈述（立得住）
- "已知（引具体文献与结论）→ 未知（具体未解决问题）→ 待验证（本研究要做的）"三段式，每句可溯源。
- 问题定义：收敛为 1-3 个**可证伪**研究问题，每个配判断标准（指标/样本/对照/时间点）。

### Step 2 四表对齐（对得上）
- `目标 → 技术路线步骤 → 验证方式 → 预期成果`横向一表逐行对应；出现目标三路线二指标另说=失败模式，必须修复。
- 每个目标可考核：指标可量化、有对照、有时间点。

### Step 3 阶段计划（排得开）
- 技术路线拆成有输入输出与前后依赖的步骤 → 映射到季度/月度里程碑。
- 落在给定周期/经费/数据/人员条件内：任务量与里程碑匹配；标注关键路径与可并行项。

### Step 4 风险与备选（说得清）
- 风险四类：数据获取/方法可行性/进度/伦理合规。
- 每条风险：`{触发信号, 影响范围, 备选方案, 决策时点}`——不是泛泛"存在风险"。

### Step 5 可编辑交付
- 论断与引用一一对应；交付可编辑源文件（保留章节编号/样式），论断可追溯。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "proposal_writing",
  "status": "success | partial | failed",
  "gap_statement": {"known":["..."],"unknown":["..."],"to_verify":["..."]},
  "questions": [{"q":"可证伪研究问题","falsifiable_check":"判定标准"}],
  "alignment_matrix": [{"goal":"G1","route_steps":["S1-S2"],"validation":"...","deliverable":"...","consistent":true}],
  "milestones": [{"stage":"S1","months":"1-3","tasks":["..."],"depends_on":[],"critical_path":true,"resources":"..."}],
  "risks": [{"category":"data","trigger":"...","impact":"...","fallback":"...","decision_point":"第6月"}],
  "evidence_links": [{"claim":"...","source":"文献/材料位置","status":"completed | planned | missing_applicant_evidence"}],
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：alignment_matrix 全 consistent；risks 四要素齐（无泛泛风险）；evidence_links 区分已完成/拟开展/缺失；申请人证据缺失不虚构。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 指南约束与材料冲突 | 以指南为准，冲突登记 |
| 周期/经费约束无法容纳计划 | 压缩方案 + needs_human_review |
| 预算不足 | 缺口陈述+四表先行（partial） |

## 6. 自查清单

1. [ ] 问题可证伪？缺口三级陈述可溯源？
2. [ ] 四表逐行对应无断裂？
3. [ ] 里程碑匹配约束条件？关键路径标注？
4. [ ] 风险四要素齐？论断引用一一对应？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。缺口陈述与四表先行；里程碑脚本排布；交付文件最后组装。
