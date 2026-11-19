---
name: annotation-harvester
description: |
  阅读批注与知识沉淀 Skill。把散落的批注（PDF 高亮/页边批注/扫描手写/网页剪藏/零散
  语句）变成可回溯、可检索、可关联的知识资产：批注提取（保留页码/上下文/标注类型/
  颜色含义）、笔记结构化、知识关联（与主题/材料/结论挂接）、后续检索。
---

# Annotation Harvester — 阅读批注与知识沉淀 Skill

## 1. 用途与适用范围

批注承载"这一句为什么重要"的判断——离开原文件就只剩无法回溯的句子。四步：提取（含上下文与类型）、结构化、关联、检索。**每条批注回到原文件可定位**。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、批注载体（PDF 注释层/剪藏/手写扫描/零散文本）。
2. 盘点：载体类型与数量、可提取性（PDF 注释层可直接读；扫描件需 OCR）。

## 3. 工作流程

### Step 1 批注提取
- PDF 注释层：逐条读 `{页码, 标注类型(高亮/下划线/旁注), 被标原文, 批注内容, 颜色}`——颜色含义如有约定（如红色=质疑）登记到图例。
- 扫描手写：OCR + 人工可核定位；网页剪藏：保留来源 URL+抓取时间。
- 提取失败逐条登记（不静默丢弃）。

### Step 2 笔记结构化
- 每条批注：`{annotation_id, 原文被标片段, 批注内容, 类型(质疑/重点/疑问/延伸), 上下文(所在段落大意), source_locator}`。
- 零散语句：归位到主题/材料，注明"来源为笔记文件，原文出处未提供"（不硬挂）。

### Step 3 知识关联
- 批注 ↔ 主题/材料/结论挂接：`{annotation_id → related_topic, related_conclusion}`；同主题批注聚类。

### Step 4 检索与沉淀
- 索引：关键词/类型/材料 → annotation_id；沉淀为可复用知识卡（原文+判断+上下文一体）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "annotation_harvest",
  "status": "success | partial | failed",
  "annotations": [
    {"annotation_id":"a1","source":{"file":"paper_v2.pdf","page":4,"locator":"高亮框"},"type":"highlight+note",
     "highlighted_text":"被标原文","note":"批注内容","color_meaning":"红色=质疑（图例）",
     "context":"所在段落大意","topic_link":"机制X"},
    {"annotation_id":"a7","source":{"file":"scan_p12.jpg","ocr_confidence":0.82},"type":"handwriting",
     "extracted":"手写内容","locator":{"page":12},"needs_human_review":false}
  ],
  "clusters": [{"topic":"机制X","annotation_ids":["a1","a3","a9"]}],
  "index": {"by_type":{"质疑":4,"重点":11},"by_material":{"paper_v2":9}},
  "extraction_failures": [{"file":"...","reason":"注释层损坏"}],
  "color_legend": {"red":"质疑","yellow":"重点"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：annotations 每条有 source_locator；颜色含义有图例；OCR 置信度如实；失败不静默；散落语句不硬挂出处。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 注释层损坏 | 尝试渲染页面图像提取；失败登记 |
| 手写难辨 | OCR+needs_human_review |
| 预算不足 | PDF 注释层优先（结构化程度最高） |

## 6. 自查清单

1. [ ] 每条批注可回原文件定位？
2. [ ] 类型/颜色含义保留？
3. [ ] 关联与聚类有依据？
4. [ ] 失败/难辨如实标注？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。注释层批量脚本读取；OCR 仅用于必要页；索引自动生成。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
