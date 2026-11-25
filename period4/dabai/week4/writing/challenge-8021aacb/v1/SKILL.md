---
name: structure-doctor
description: |
  论文结构与逻辑优化 Skill：对完整稿件做结构诊断并交付作者可直接执行的
  修改方案。核心方法：①章节功能拆解（每节回答什么论证问题）；②论点-
  论据映射表（逐条抽论断+支撑论据，找断裂/跳跃/循环论证/论据不足）；
  ③重复内容定位（n-gram 粗筛+语义同义重复）；④结论边界检查（结论是否
  超出数据与实验条件范围、相关是否写成因果）。每条诊断必须定位到章节/
  段落/原句锚文本并给出编辑动作（移/并/拆/收窄），不另起炉灶改写。
  离线运行，判断可回链原文，缺项显式标注。
---

# 论文结构与逻辑优化 Skill

## 1. 用途与适用范围

- 用途：输入一篇完整稿件 → 输出结构诊断报告 + 可执行编辑动作清单（JSON/Markdown），覆盖六类：研究问题与贡献主张对齐、章节结构与叙事顺序、论证链与论据对应、段落关系与重复内容、结论边界与表述尺度。
- 适用：期刊论文、学位论文章节、技术报告。
- 边界：不做语言润色类泛泛建议；每条诊断必须能指回原文位置；不虚构稿件中不存在的缺陷。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、`output_contract` 全字段、稿件路径。
2. 读 `/input/task.md`：诊断范围（六类可全查或指定子集）、输出格式要求。
3. 打开稿件读全文；先做完整性盘点 → `/app/work/integrity.md`：是否有缺章节、无参考文献、图表/公式缺失、格式混乱、稿件截断。存在上述情况先记 anomalies，诊断在现有文本上继续。
4. 稿件为空或不可读 → status=failed + missing_inputs。

## 3. 工作流程（6 步流水线）

### Step 1 章节功能拆解 → /app/work/section-map.json
- 每节登记：`{section_id, title, function(铺垫/方法/证据/反驳/结论), key_question(该节回答什么), word_share}`。
- 研究问题与贡献主张单独抽取：Q-n（研究问题原文位置）、CLAIM-n（贡献主张原文位置）。
- 验收：每节有 function；Q/CLAIM 可回链原句。

### Step 2 论点-论据映射 → /app/work/claim-evidence-map.json
- 逐段抽取论断：`{claim_id, anchor(原句锚文本≤30字), location, claim_type(事实/推断/主张), evidence[], verdict}`。
- verdict 四类：`supported`(有对应论据) / `gap`(断裂：无论据) / `jump`(跳跃：论据与论断间缺推导步) / `circular`(循环论证) / `weak`(论据强度不足：个案撑普遍结论)。
- 跨章呼应检查：引言承诺的问题/贡献 → 讨论/结论逐一兑现，缺兑现记 `unfulfilled`。
- 验收：结论章每条论断均有映射；verdict 不凭风格偏好判错。

### Step 3 重复与衔接检查 → scripts/check_structure.py
- 运行 `python3 scripts/check_structure.py <manuscript.md>`
- 机械检出：① 跨章节重复句子（8-gram 完全重复 + 长句 Jaccard≥0.7 粗筛）；② 无过渡的相邻节（前节末句与新节首句零词汇交集提示逻辑跳跃，仅作线索）；③ 段落超长（>400字未分段）。
- 输出候选清单，语义级同义重复由 Agent 复核后定级（high/low）。

### Step 4 结论边界检查 → /app/work/conclusion-boundary.md
- 逐条结论对照：是否超出数据范围（样本/条件/时长）、相关→因果误写、缺限制说明（对照方法节实际条件）。
- 每条给 verdict：`within-boundary` / `overreach`(超范围) / `causal-misuse` / `missing-limits`，附原文位置与依据。
- 验收：结论条目覆盖率 100%（对照 Step1 的 CLAIM-n）。

### Step 5 修改方案 → /app/work/edit-plan.json + revision-notes.md
- 每条诊断转成可执行编辑动作，五型：
  - `move`: {移动块锚文本, 目标位置}
  - `merge`: {合并段落A锚, 合并段落B锚}
  - `split`: {拆分段落锚, 拆分点, 两部分各自去向}
  - `narrow`: {收窄句子锚, 原表述, 收窄后表述, 依据}
  - `add-transition`: {前节末, 后节首, 衔接建议}
- 每条动作带：`{id, type, target_anchor, action, reason, based_on(诊断id), severity(high/med/low)}`。
- 不输出另起炉灶的整篇改写稿；每条动作作者复核后可判采纳/部分采纳/驳回。
- 验收：每条编辑动作可回链诊断 id；诊断可回链原文位置。

### Step 6 交付 → /app/output/
- `result.json`、`edit-plan.json`、`revision-notes.md`（人读版诊断+方案）、`claim-evidence-map.json`、`section-map.json`、`integrity.md`。

## 4. 输出契约（result.json 逐字段）

以 `output_contract` 为准，通用骨架：

```json
{
  "case_id": "<原样>",
  "status": "completed | partial | failed",
  "deliverables": {
    "edit_plan": "/app/output/edit-plan.json",
    "revision_notes": "/app/output/revision-notes.md",
    "claim_evidence_map": "/app/output/claim-evidence-map.json",
    "section_map": "/app/output/section-map.json"
  },
  "fact_source_map": [
    {"diagnosis_id": "D-3", "anchor": "实验证明方法A更优", "location": "§4.2 para1", "basis": "稿件原文+claim-evidence gap"}
  ],
  "version_and_boundaries": {
    "change_records": ["诊断基于稿件v?,未改动原文"],
    "manual_review_items": ["D-7 重复段落语义级判定需作者确认"],
    "material_gaps": ["稿件无参考文献节，D-9 论据强度无法核对"],
    "anomalies": ["稿件在第5章处疑似截断"]
  },
  "uncertainty": [
    {"item": "§3.1 与 §5.2 疑似同义重复", "level": "medium", "handling": "机械粗筛候选，待人工复核"}
  ],
  "summary": {"n_sections": 6, "n_claims": 23, "n_findings": 11,
               "by_type": {"gap": 2, "jump": 1, "weak": 3, "overreach": 2, "duplication": 3},
               "n_edit_actions": 11}
}
```

## 5. 数字门槛

| 门槛 | 值 | 不达标 |
|---|---|---|
| 六类诊断覆盖 | 任务要求类别 100%（缺项类显式标"稿件无此问题"） | 漏类 → partial |
| 诊断定位粒度 | 每条到章节+段落+锚文本 | 无定位条目=0 |
| 编辑动作可执行性 | 每条有 type+target+action | 缺任一 → 重写该条 |
| 虚构缺陷 | 0（锚文本在原文可检索，脚本核对） | 检出即删 |
| 结论覆盖率（CLAIM 对照） | 100% | 缺对照 → partial |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 缺章节/无参考文献 | integrity.md 记录；相关诊断标 material_gaps 不硬判 |
| 图表公式缺失引用 | anomalies 记录，交叉引用类诊断降级为线索 |
| 稿件截断 | 记截断点，截断后内容不诊断 |
| 格式混乱无法分节 | 按语义重新切分并在 section-map 说明 |
| 六类中某类确无问题 | 显式输出"该类检查完成，未发现问题"，不算缺项 |
| 机械重复误报 | 复核定级，误报剔除并保留记录 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 每条诊断有 location+锚文本，且锚在原文可检索（脚本核对）
- [ ] 每条编辑动作五型之一、字段齐全、可回链诊断
- [ ] verdict 有依据，无风格偏好类判断
- [ ] 结论条目 100% 对照；相关/因果表述逐条核对
- [ ] anomalies/integrity 如实；status 与实际一致

## 8. 效率约束

- 64 请求/900 秒：Step3 脚本先跑（零模型成本）；映射与诊断按章节分批；先落最小 result.json。
- ≤50 文件、单文件 ≤500KB、总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入：6 节实验论文 md。
section-map：6节功能拆解+Q-1/Q-2+CLAIM-1..3 → claim-evidence-map 23 条（gap 2、jump 1、weak 3）→ check_structure.py 检出 3 处 8-gram 重复候选 → conclusion-boundary：CLAIM-3 超样本范围 overreach → edit-plan 11 条（move 2 / merge 1 / split 1 / narrow 3 / add-transition 4），每条带锚文本 → result.json status=completed。
