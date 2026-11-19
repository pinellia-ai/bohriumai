---
name: bilingual-academic-translator
description: |
  学术翻译与双语写作 Skill。术语稳（可维护术语表、译法全篇锁定含图表题注）、数字实
  （数值/单位/量级/范围/年份原样落地，中英数字表达差异处理）、对得齐（句段级双语对照、
  段序/图表编号/题注/脚注/参考文献原位保留）、边界清（增译省译标注、否定范围/因果强度/
  模糊限制语保持原意、引用与归属完整）。输出双语对照稿 + 术语表 + 边界审计。
---

# Bilingual Academic Translator — 学术翻译与双语写作 Skill

## 1. 用途与适用范围

学术文本的中英互译（以英→中为主）：句段级双语对齐可逐段修改；术语全篇一致；数字与限定语原样落地；不出现作者没说过的结论。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点：原文（摘要/正文/图表题注/脚注/参考文献）、目标语言与文体要求、已有术语表（若有）。
3. 记录学科领域——同一英文词在不同学科译法不同（如 cell、field、solution），以材料学科为准。

## 3. 工作流程

### Step 1 术语抽取与锁定（术语稳）
- 扫全文抽取领域术语、缩写、上下位词，建术语表：`{英文, 中文译法, 首现位置, 学科依据}`。
- 缩写处理：首现"中文全称（英文缩写）"，后文用缩写。
- 译法锁定到**全篇包括图表题注与附录**——同一术语每次出现同一译法；学科歧义词按材料语境选定并在表中注明。

### Step 2 句段对齐翻译（对得齐）
- 句段级一一对应：段落顺序、图表编号、题注、脚注、参考文献条目**原位完整保留**。
- 公式、符号、变量名不翻译；参考文献条目原文保留（仅题注类需译时另行标注）。
- 避免逐字直译的冗长生硬，也**不**改成宣传口吻或口语化——保持学术语域。

### Step 3 数字与事实校验（数字实）
- 数字、单位、量级、范围、年份、样本量、统计口径逐项核对原样落地：不四舍五入、不错配单位、不"顺手改整数"。
- 中英数字表达差异显式处理：4.5万 ≠ 4.5 million（应为 45,000）；billion=十亿；百分数与有效数字保留。

### Step 4 语义边界审计（边界清）
- 增译/省译逐处标注（must/should/may 的义务强度；not only...but also 的范围）。
- 否定范围：`does not significantly reduce A and B` 的否定覆盖面翻译时保持。
- 因果强度与模糊限制语（suggest/indicate/demonstrate → 提示/表明/证明）强度对应不升级。
- 引用标记（et al.、上标、方括号）与作者归属完整保留；不出现原文没有的结论。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "bilingual_translation",
  "status": "success | partial | failed",
  "term_table": [{"en":"tensile strength","zh":"拉伸强度","first_seen":"Abstract S2","discipline_note":"材料学标准译法"}],
  "bilingual_segments": [
    {"seg_id":1,"source":"英文原句","translation":"中文译文","alignment":"1:1 | 1:n | n:1",
     "notes":null}
  ],
  "number_audit": [{"seg_id":2,"original":"4.5 million","translated":"450万","ok":true}],
  "boundary_audit": [
    {"seg_id":3,"type":"hedging | negation | causality | addition | omission","original":"may contribute",
     "translated":"可能促进","strength_preserved":true,"note":""}
  ],
  "structural_integrity": {"paragraph_order":true,"figures_numbering":true,"captions_translated":true,
                           "footnotes_kept":true,"references_kept_verbatim":true},
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：术语表全篇一致（脚本可抽查）；number_audit 覆盖全部数值句；boundary_audit 覆盖全部限定语；双语段可逐段对照修改。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 学科歧义术语 | 按材料语境定译，表中注明，needs_human_review 提示 |
| 原文语病 | 按最合理解读翻译，note 记录原文问题，不擅自"修复"事实 |
| 长句无法 1:1 | 标 1:n 拆分，段序不乱 |
| 文化专有表述 | 直译+括号注释，不意译丢失 |
| 预算不足 | 先术语表+核心章节（摘要/结果），status=partial |

## 6. 自查清单

1. [ ] 术语全篇（含题注）同一译法？
2. [ ] 数字/单位/年份逐项原样？中英数字差异处理正确？
3. [ ] 句段对齐、结构完整、参考文献原样？
4. [ ] 否定/因果/限制语强度无升降？无新增结论？
5. [ ] 增译省译全部标注？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。术语表先行；翻译按段落批量推进；数字与边界审计合并为一次全文扫。中断时已译段落对齐完整可交（partial）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "term_table":[{"en":"graphene","zh":"石墨烯","first_seen":"Abstract S1","discipline_note":"标准译法"}],
 "bilingual_segments":[{"seg_id":1,"source":"The composite showed 30% improvement.","translation":"该复合材料提升了30%。","alignment":"1:1","notes":null}],
 "number_audit":[{"seg_id":1,"original":"30%","translated":"30%","ok":true}],
 "boundary_audit":[{"seg_id":2,"type":"hedging","original":"suggests","translated":"提示","strength_preserved":true,"note":""}],
 "structural_integrity":{"paragraph_order":true,"figures_numbering":true,"captions_translated":true,"footnotes_kept":true,"references_kept_verbatim":true},
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
