---
name: academic-language-polisher
description: |
  学术语言润色 Skill。改得对（语法/句法/搭配/标点/用词真正改掉，不换说法掩盖）、说得像
  （目标文体语域、术语全篇统一、像同行写的）、留得住（语义保持：限定词/指代/因果强度/
  数字单位不丢不改）、改得明（每处修改可 diff、可回退、有理由）。输出润色稿 + 修改清单。
---

# Academic Language Polisher — 学术语言润色 Skill

## 1. 用途与适用范围

润色不是重写：改得对、说得像、留得住（语义保持）、改得明。典型失败场景的针对性修复：整段重写后限定词消失、术语前后漂移、中译英直译腔。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、原稿、润色要求（目标文体/语言/重点）。
2. 建立语义保持清单（改前基线）：限定词清单、术语表、数字与单位清单、指代与因果关系清单——润色后逐项对账的基准。
3. 稿件缺失：status=failed。

## 3. 工作流程

### Step 1 基线提取（留得住的锚）
- 扫描原稿：`{限定词（may/only/under X conditions）, 术语出现处, 数字/单位, 因果与让步连接词}` 逐条登记——这些是"不许丢"的清单。

### Step 2 逐句润色（改得对）
- 真修错误：语法/搭配/标点/用词——每处修改对应一个**具体错误类型**，不做无理由改写。
- 术语统一：全篇查术语表，漂移处（引言 vs 方法用词不同）统一为首选译名/写法。
- 语域调整：去口语化、去直译腔（中译英按英文惯用句式重组），但保持作者立场与语气强度。

### Step 3 语义对账（留得住）
- 润色稿 vs 基线逐项核对：限定词在否？数字单位改了吗？因果强度升了吗？指代对象变了吗？
- 任何丢失/升级 → 回改，不让"换一种说法"掩盖语义漂移。

### Step 4 修改清单（改得明）
- 每处修改：`{loc, before, after, reason(错误类型), semantic_safe:true}`——作者可逐条采纳/驳回，可 diff 回退。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "language_polishing",
  "status": "success | partial | failed",
  "baseline": {"hedges":12,"terms":9,"numbers":7,"causal_links":4},
  "edits": [{"loc":"abstract para1","before":"...","after":"...","error_type":"grammar | collocation | register | term-drift | punctuation","reason":"主谓不一致","semantic_safe":true}],
  "semantic_audit": {"hedges_kept":12,"numbers_kept":7,"causal_strength_changes":0,"term_violations":[]},
  "files": {"polished":"polished.md","diff":"edits 清单内嵌"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：semantic_audit 全保留（丢失项必须回改后才 success）；edits 每条有错误类型与理由；无重写式大改（除非任务要求 rewrite 并登记）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 原句语义不明 | 保守改最小集 + needs_human_review |
| 任务要求整段重写 | 按 rewrite 模式执行并全程对账基线 |
| 预算不足 | 语法错误修复优先，语域调整 partial |

## 6. 自查清单

1. [ ] 每处修改有错误类型理由？非无理由改写？
2. [ ] 术语全篇统一？
3. [ ] 限定词/数字/因果强度全保留？
4. [ ] 修改清单可 diff 回退？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。基线扫描脚本化；逐句润色批量；对账脚本自动比对。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：事实底稿/配置/日志/文献是事实依据；不为行文顺畅补造数值或文献；不编造软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（稿件文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：事实、数字、引用保留来源或修改记录。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
