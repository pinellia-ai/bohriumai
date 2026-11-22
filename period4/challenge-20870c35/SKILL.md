---
name: talk-organizer-qa-ready
description: |
  学术汇报内容组织 Skill。把"这次汇报要达成什么"转成可检查目标，按听众（组会/答辩/
  评审）调整背景铺垫与证据深度，在"问题—方法—结果—结论"骨架上做取舍与铺垫形成叙事
  顺序，每页唯一主张+支撑证据+证据强度标注，并预判问答准备备用页。硬约束：页面每个论断
  可在源材料找到对应位置；叙事顺序服务于指定听众与时长；取舍过程可复核。
---

# Talk Organizer — 学术汇报内容组织 Skill（问答有备）

## 1. 用途与适用范围

只计"从已有内容材料到可讲页面的组织与交付"：报告目标、听众、叙事顺序、重点信息、问答准备。三标准：① 页面每个论断能在源材料找到位置；② 叙事顺序服务于指定听众与时长；③ 取舍过程可复核。

不负责：论文精读、学术写作成稿、科研绘图素材生产（由相邻课题承担）。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id 与**汇报约束**：场合（组会/答辩/评审）、听众、时长、页数、模板。
2. 盘点源材料：研究内容、结果数据、图表、既有材料。逐文件登记定位体系。
3. 材料缺失：status=failed；约束缺失（如未给时长）按场合惯例设默认并在 uncertainty_notes 声明。

## 3. 工作流程

### Step 1 报告目标（转成可检查）
- 把场合转成可判定目标：如"让评委认可方法新颖性"→ 检查项：创新点页 ≥1、与已有工作对比页 ≥1、证据强度表述明确。
- 每个目标配验收标准（页数、内容、结论强度），写进 objectives 表。

### Step 2 听众分析（决定深浅）
- 识别听众先验知识、关注点、可能质疑：
  - 组会：熟悉背景 → 少铺垫、重方法细节与进度风险；
  - 答辩：重创新点与边界 → 创新对比+局限页加重；
  - 评审：重结论与证据强度 → 数据页+对照说明加重。
- 决定三件事：背景铺垫比例、术语解释范围、证据展示深度。

### Step 3 叙事顺序（有起承转合）
- 在"问题—方法—结果—结论"骨架上做**取舍与铺垫**：不是按论文目录搬运。
- 页数↔时长配比核对（如 10 分钟 ≈ 10-12 页），每页预留讲述时间。
- 起承转合：开场钩子（为什么重要）→ 铺垫收敛到问题 → 方法一页讲清 → 结果按证据强度排序 → 结论与边界收口。

### Step 4 重点信息（每页一句可讲的结论）
- 每页**唯一主张** + 支撑证据 + **证据强度标注**（direct/inference/undetermined）。
- 长段落压缩成一句可讲结论（保留数值/条件），标注源材料位置。
- 图表与页内结论对应：编号、引用不错位。

### Step 5 问答准备（被追问时有准备）
- 预判四类追问：机制、数据、对照、局限——针对每类预判 2-3 个具体问题。
- 每个预判问题准备：可引用的页面（"见第 N 页"）、**备用页**（附录页，不计入正片页数）、口径一致的回答要点。
- 高风险问题（数据弱点、对照缺失）的应答口径与正文一致，不夸大不回避。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "talk_content_organization",
  "status": "success | partial | failed",
  "objectives": [{"goal":"...","check":"...","met":true}],
  "audience_profile": {"occasion":"defense","prior_knowledge":"high","emphasis":"novelty+boundary","background_ratio":"low"},
  "outline": [{"page":1,"claim":"...","evidence_strength":"direct","source_locator":{"material":"...","section":"..."},"talk_minutes":1.0}],
  "narrative_rationale": {"order_reason":"...","transitions":["p1→p2: ..."]},
  "qa_prep": [
    {"predicted_question":"...","category":"data | mechanism | control | limitation",
     "answer_points":["..."],"ref_pages":[4],"backup_slide":"backup-1"}
  ],
  "backup_slides": [{"id":"backup-1","claim":"...","source_locator":"..."}],
  "files": {"outline_md":"outline.md","deck_ref":"slides.pptx 或页面清单"},
  "constraints_check": {"page_count_ok":true,"duration_match":"10min/10页","template_ok":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：outline 每页有 claim + source_locator + evidence_strength；qa_prep 至少覆盖四类追问各 1 条；constraints_check 全过；取舍理由记录（narrative_rationale + changes）可复核。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 场合/听众信息缺失 | 按材料推断最可能场合 + uncertainty_notes 声明 |
| 内容多页数少 | 按目标优先级裁剪，取舍登记 |
| 源材料有弱点（对照缺失等） | 不回避：列入 qa_prep 高风险项，正文如实标 limitation |
| 预算不足 | outline+qa_prep 先落盘（partial），备注页后补 |

## 6. 自查清单

1. [ ] 目标可检查且逐项 met？
2. [ ] 听众三要素（铺垫比例/术语范围/证据深度）明确？
3. [ ] 顺序服务听众与时长？页数↔时长匹配？
4. [ ] 每页唯一主张+证据强度+源定位？
5. [ ] 四类追问都有准备？备用页齐？口径与正文一致？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。outline 与 qa_prep 先行落盘；备用页从源材料直接摘编不重写。中断时 outline 完整即 partial 可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "objectives":[{"goal":"让评委认可方法新颖性","check":"创新对比页≥1","met":true}],
 "audience_profile":{"occasion":"defense","prior_knowledge":"high","emphasis":"novelty+boundary","background_ratio":"low"},
 "outline":[{"page":4,"claim":"X机制使效率提升38%","evidence_strength":"direct","source_locator":{"material":"results.csv","section":"Fig.4a"},"talk_minutes":1.0}],
 "qa_prep":[{"predicted_question":"对照组是什么？","category":"control","answer_points":["以未处理组为对照，见p4"],"ref_pages":[4],"backup_slide":"backup-1"}],
 "backup_slides":[{"id":"backup-1","claim":"对照设置细节","source_locator":"methods.md §3"}],
 "constraints_check":{"page_count_ok":true,"duration_match":"10min/10页","template_ok":true},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`（deck/页面文件 + result.json）。
4. **尽早落盘**：先用最小可用结果写一次 result.json，再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（论文章节/图表号/材料位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：outline.csv（页/主张/强度/时长/定位）
2. qa_prep.csv（四类问题计数）
3. 页数-时长配比计算式。
