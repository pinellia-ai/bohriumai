---
name: longdoc-consistency-manager
description: |
  学位论文与长文档写作 Skill。立得住（章节规划对应提纲/论证链/字数分配）、连得上（跨
  章节术语/符号/编号/图表引用/结论一致性，改动影响段可找出）、改得动（局部修改保留原意，
  作者看懂改了什么）、查得清（论断/引用/改动可追溯复核）。核心资产：术语表/符号表/定义
  清单/结论清单 + 版本级改动记录。
---

# Long-doc Consistency Manager — 学位论文与长文档写作 Skill

## 1. 用途与适用范围

数万字长文的四问管理：立得住（章节规划 vs 提纲/论证链/字数）、连得上（跨章一致性+影响分析）、改得动（局部改保留原意）、查得清（可追溯）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、提纲/章节要求、既有稿件、字数分配约束。
2. 建立**一致性清单底账**：术语表、符号表、定义清单、结论清单（扫描既有稿件生成）。
3. 材料缺失登记。

## 3. 工作流程

### Step 1 章节规划（立得住）
- 每节：`{回答什么问题, 需要哪些证据, 字数预算, 依赖哪些节}`——规划与提纲/论证链对应。
- 检测章节重复或断裂（前后节论述同一内容/缺过渡）。

### Step 2 一致性底账（连得上）
- 术语表：同一概念的不同写法检测（缩写/全称/同义词），统一或登记映射。
- 符号表、定义清单（重复定义检测）、结论清单（前后矛盾检测）。
- **影响分析**：改动一处（定义/数值/符号），自动列出受影响段落清单。

### Step 3 局部修改纪律（改得动）
- 只动需要动的段落：修改记录 `{位置, 原句, 新句, 理由, 类型(作者原句保留 | 机器改写)}`。
- 保留作者原意与既有表述——改写句与原句差异可见。

### Step 4 可追溯（查得清）
- 每个论断绑文献（存疑引用标记）；每次改动有版本记录；长上下文：前文定义/已用材料/已下结论在写作时可见（底账查询）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "longdoc_writing",
  "status": "success | partial | failed",
  "chapter_plan": [{"section":"3.2","answers":"...","evidence_needed":["..."],"word_budget":1500,"depends_on":["3.1"]}],
  "consistency_ledger": {"terms":[{"canonical":"拉伸强度","variants":["强度","tensile"]}],
    "symbols":[],"definitions":[{"term":"...","where":["2.1","3.4"],"duplicate":true}],
    "conclusions":[{"claim":"...","where":["4.2","5.1"],"contradiction":false}]},
  "impact_analysis": [{"changed":"3.2 定义","affected":["4.1","5.3"]}],
  "edit_log": [{"loc":"4.1 para2","before":"...","after":"...","reason":"...","type":"author_kept | machine_rewrite"}],
  "citation_audit": [{"claim_loc":"5.2","ref":"[12]","status":"ok | 存疑 | 缺失"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：底账四表齐；改动有 edit_log 且原句保留；影响分析覆盖改动传播；存疑引用不静默。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 提纲与材料矛盾 | 以材料为准规划，矛盾登记 |
| 稿件过大超预算 | 底账扫描+关键章处理优先，其余 partial |
| 前后矛盾结论 | 并列记录 + needs_human_review |

## 6. 自查清单

1. [ ] 章节规划对应提纲/论证链/字数？
2. [ ] 四表底账建立且用于写作过程？
3. [ ] 改动影响段可找出？
4. [ ] edit_log 保留原句？作者原意保留？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。底账扫描脚本化（正则+关键词）；一致性检测批处理；改动即记 edit_log。
