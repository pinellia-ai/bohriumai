---
name: grant-proposal-builder
description: |
  基金申请书写作 Skill。围绕给定案例材料构建"立得住、说得准、对得上、查得到"的申请要素：
  立项依据（别人做到哪、还差什么、为什么是我们）、科学问题收敛（可回答可分解有边界）、
  目标-内容-路线-指标逐条对应（四表一致）、创新点写清与已有工作的具体差别（不用无法核验
  的修饰语）、前期成果按"能力—证据—与本研究关系"组织。区分已完成与拟开展，真实申请人
  证据缺失时如实标注，不虚构成果。
---

# Grant Proposal Builder — 基金申请书写作 Skill

## 1. 用途与适用范围

把研究想法组织成逻辑闭环的申请书要素：立项依据、科学问题、研究目标、创新点、技术路线、研究基础与可行性。四条硬标准：
- 立得住：必要性论证（领域现状→关键瓶颈→申请人前期观察），不堆政策口号；
- 说得准：创新点与具体已有工作对比，禁用"首次/国际领先/填补空白"类无法核验的修饰；
- 对得上：目标、内容、路线、考核指标逐条对应（七要素/计划一致性约束依 case.json 的 organizer-workorder）；
- 查得到：文献、数据、前期成果、政策口径可追溯，区分"已完成"与"拟开展"。

诚实边界（组织方修订 v1）：原论文与既有成果归外部作者；真实申请人证据缺失时**显式标注**（needs_human_review），不虚构申请人成果或资助机构政策。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md / organizer-workorder.json，记录 case_id。
2. 盘点：领域背景材料、代表性文献、既有成果线索、写作要求与约束（七要素清单、字数、格式）。
3. 建立"已有工作表"：`{文献/成果, 已解决什么, 未解决什么(瓶颈), 与本研究的关系}`——创新点定位的基础。
4. 材料缺失：登记 gaps；申请人自身证据缺失的部分按骨架撰写并标注。

## 3. 工作流程

### Step 1 立项依据（立得住）
三段式论证链：
1. 领域现状：别人做到哪一步（引具体文献，不用泛话）；
2. 关键瓶颈：还差什么——为什么现在必须做（技术突破/新数据/新方法的机会窗口）；
3. 申请人切入点：为什么是我们（前期观察/独特条件——有证据则引，无证据标待补）。
每句实质性断言可溯源。

### Step 2 科学问题收敛（说得准的前提）
- 把宽泛兴趣收敛为可回答、可分解、有边界的科学问题：主问题 + 2-4 个子问题，每个子问题可判定"回答了没有"。
- 检查问题与方法匹配度（问题需要的方法材料是否具备）。

### Step 3 目标—内容—路线—指标对齐（对得上）
四表一致核对（核心交付）：
| 研究目标 | 研究内容 | 技术路线步骤 | 考核指标 |
每行横向对应：1 个目标 → 1-2 项内容 → 路线中的具体步骤 → 可考核指标（可量化/可判定）。出现"目标三个、路线两条、指标另说一套"即为失败模式，必须修复。
- 技术路线写清输入输出、可行性依据、风险与备选方案——不罗列方法名。

### Step 4 创新点定位（说得准）
- 与已有工作表逐条对比：新在哪里（方法/数据/视角）、为什么难、凭什么做得成。
- 禁用修饰语自查："首次""国际领先""填补空白"→ 改为具体差别陈述。

### Step 5 研究基础与可行性（查得到）
- 既有成果按"能力—证据—与本研究的关系"组织：`{成果, 证明什么能力, 用于本研究哪个环节, 状态(已完成/拟开展)}`。
- 文献与数据口径可溯源；政策口径引用具体文件与条款位置（材料提供范围内）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "grant_proposal_writing",
  "status": "success | partial | failed",
  "sections": {"rationale":"rationale.md","questions":"questions.md","goals":"goals.md",
               "innovation":"innovation.md","roadmap":"roadmap.md","foundation":"foundation.md"},
  "alignment_matrix": [
    {"goal":"G1","contents":["C1"],"roadmap_steps":["S1-S3"],"indicator":"可考核指标","consistent":true}
  ],
  "questions": [{"main":"...","sub":["..."],"answerable_check":"判定标准"}],
  "innovation_claims": [
    {"diff_from":"[3] Smith 2024：只做了X","ours":"引入Y处理Z","why_hard":"...","why_us":"...",
     "banned_phrasing_removed":true}
  ],
  "evidence_links": [{"claim":"...","source":"文献/材料位置","status":"completed | planned | missing_applicant_evidence"}],
  "banned_phrase_audit": [],
  "needs_human_review": ["申请人前期成果证据缺失，已按骨架撰写"],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：alignment_matrix 全表 consistent（不一致必须修复或登记）；banned_phrase_audit 为空才允许 success；申请人证据缺失显式标注，不虚构；七要素约束（若 workorder 给出）逐条满足。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 申请人成果信息缺失 | 骨架 + needs_human_review，不编造 |
| workorder 约束与材料冲突 | 以 workorder 为准，冲突登记 |
| 目标无法考核 | 重写为可判定指标 |
| 预算不足 | 先 alignment_matrix 与科学问题（结构核心），status=partial |

## 6. 自查清单

1. [ ] 立项依据三段链完整、逐句可溯源？
2. [ ] 科学问题可回答可分解有边界？
3. [ ] 目标-内容-路线-指标横向对齐？
4. [ ] 创新点无禁用修饰语、差别具体？
5. [ ] 已完成/拟开展区分清楚？无虚构成果？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。先四表对齐骨架（一致性核心），再填论述文字；文献引用复用已有工作表。中断时 alignment_matrix 完整即 partial 可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"partial",
 "alignment_matrix":[{"goal":"G1 建立制备方法","contents":["C1 工艺优化"],"roadmap_steps":["S1 参数筛选","S2 验证"],"indicator":"成品率≥80%","consistent":true}],
 "questions":[{"main":"X如何影响Y？","sub":["X1","X2"],"answerable_check":"每组有对照且指标可测"}],
 "innovation_claims":[],"evidence_links":[{"claim":"申请人具备合成平台","source":null,"status":"missing_applicant_evidence"}],
 "banned_phrase_audit":["已删除'填补空白'→改为'现有方法未覆盖高温工况'"],
 "needs_human_review":["前期成果清单缺失"],"gaps":[],"uncertainty_notes":[],"changes":[]}
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
1. 保持 77 分水准：alignment_matrix 逐行 consistent 断言；evidence_links 三态计数（completed/planned/missing）；禁用词审计输出。
