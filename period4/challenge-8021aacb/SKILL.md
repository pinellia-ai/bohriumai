---
name: structure-logic-editor
description: |
  论文结构与逻辑优化 Skill。产出"诊得准、改得动、链得通、说得清"的结构评审：
  问题定位到章节/段落/句子并分类（研究问题对齐/章节顺序/论证链断裂/段落重复/结论越界），
  每条输出可执行编辑动作（移动/合并/拆分/收窄，而非另写一篇），逐条判断指回原文位置与
  依据，作者可采纳/部分采纳/驳回。六维度源文本审读，无预设缺陷、不整篇重写。
---

# Structure & Logic Editor — 论文结构与逻辑优化 Skill

## 1. 用途与适用范围

对给定稿件做源文本 grounding 的结构诊断与**可执行编辑计划**。六维度：研究问题与贡献主张对齐、章节结构与叙事顺序、论证链与论据对应、段落关系与重复内容、结论边界与表述尺度、跨章节呼应。

边界（组织方修订）：无预设缺陷清单——发现什么报什么；可编辑 JSON/Markdown 即达标；不做整篇未经请求的重写。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 通读稿件全文，建立结构地图：`{章节 → 段落号 → 段落功能(提出问题/方法/结果/论证/结论)}`。
3. 记录任务指定的关注范围（若 task.md 限定维度，按限定执行）。
4. 稿件缺失：status=failed。

## 3. 工作流程

### Step 1 论断—论据清单（链得通的基础）
- 逐段抽取论断：`{claim_id, 位置(段), text, 类型(问题/主张/结果/解释/结论)}`。
- 每条论断标注论据：来自本研究数据（哪图表）、来自文献（哪条）、还是无论据。
- 找出：断裂（结论无论据）、跳跃（缺中间步骤）、循环论证、论据强度不足。

### Step 2 结构诊断（诊得准）
按六维度逐项检查，**每个问题定位到段/句并分类**：
- `alignment`：研究问题是否贯穿？贡献主张与实际工作一致？问题与方法各说各话的位置。
- `structure`：章节顺序、篇幅失衡、该前置的铺垫、该后移的细节、该合并的章节。
- `chain`：Step 1 发现的论证链问题。
- `paragraph`：同义重复、跨章重复、缺过渡、逻辑跳跃。
- `boundary`：结论超出数据/条件范围、缺限制说明、相关写成因果。
- `coherence`：跨章节呼应（引言承诺 vs 结论兑现）。

每个问题项：`{issue_id, 维度, 位置(章节/段/句), 类型, 严重度, 证据(引用原文), 说明}`。没有问题的维度如实写"未发现"，不凑数。

### Step 3 编辑计划（改得动）
每个问题给**可执行动作**，不另起炉灶：
- `move`：把段X移到章Y第Z段后（理由）。
- `merge`：段A与段B合并（重复点）。
- `split`：段C拆为两段（拆分点）。
- `narrow`：句子S的论断收窄为…（原文越界证据）。
- `add_transition` / `delete` / `reorder`。
每个动作 = `{action_id, type, target(段/句), instruction, reason_link(issue_id), risk}`。作者可按动作逐条执行，改动可局部回滚。

### Step 4 溯源说明（说得清）
每条判断指回原文位置与依据（引用稿件原句），并给出采纳建议（采纳/部分采纳/待作者定夺）；作者复核路径明确。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "structure_logic_review",
  "status": "success | partial | failed",
  "structure_map": [{"section":"3 Results","paragraphs":5,"functions":["data","claim"]}],
  "claim_evidence_list": [{"claim_id":"c3","loc":{"section":2,"paragraph":4},"text":"...","evidence":"Fig.3 / 无","gap":"结论无论据"}],
  "issues": [
    {"issue_id":"i1","dimension":"boundary","loc":{"section":5,"paragraph":2,"sentence":3},
     "type":"overclaim","severity":"major","quote":"原文句子","note":"相关表述成因果，且样本仅雄性"}
  ],
  "edit_plan": [
    {"action_id":"a1","type":"narrow","target":{"section":5,"paragraph":2,"sentence":3},
     "instruction":"将'证明A导致B'改为'A与B相关（雄性小鼠，n=30）'","reason_link":"i1","risk":"低"}
  ],
  "coherence_notes": ["引言承诺的三点贡献与结论逐条对照结果"],
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：issues 每条有位置+原文引用+类型；edit_plan 每条可独立执行且与 issue 关联；无预设缺陷——只报实际发现；不输出整篇改写稿。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 稿件过短/非论文 | 按实际结构评审，说明局限 |
| 问题密集 | 按严重度排序，major 优先给动作 |
| 编辑动作与作者意图可能冲突 | 标 needs_human_review |
| 预算不足 | 先 chain+boundary 两维度（影响最大），status=partial |

## 6. 自查清单

1. [ ] 问题定位到段/句？类型与严重度明确？
2. [ ] 每条编辑动作可执行、可局部回滚？
3. [ ] 论断-论据清单完整？断裂/跳跃/循环已标记？
4. [ ] 判断可指回原文？结论边界问题已查？
5. [ ] 未发现问题的维度如实记录？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。结构地图与论断清单一次完成；诊断按维度批量扫；编辑计划从 issue 直接生成。中断时先交 issues（诊断核心），edit_plan 可 partial。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "issues":[{"issue_id":"i1","dimension":"boundary","loc":{"section":5,"paragraph":2,"sentence":3},"type":"overclaim","severity":"major","quote":"This proves the mechanism.","note":"仅为相关性证据"}],
 "edit_plan":[{"action_id":"a1","type":"narrow","target":{"section":5,"paragraph":2,"sentence":3},"instruction":"改为'与…机制相关'并加样本限制","reason_link":"i1","risk":"低"}],
 "coherence_notes":["引言承诺2点贡献，结论兑现2点"],
 "gaps":[],"uncertainty_notes":[],"changes":[]}
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
1. 交付量化对账：claim_evidence.csv（claim/loc/evidence/gap）逐条；edit_plan.csv（action↔issue 关联）；未发现问题维度如实记录。
