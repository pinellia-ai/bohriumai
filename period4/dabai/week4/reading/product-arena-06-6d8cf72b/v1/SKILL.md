---
name: structured-paper-notes-anchor
description: |
  文献总结与结构化笔记：按论文自身章节对齐生成结构化笔记（研究问题/数据/方法
  条件/发现/局限字段化卡片），每条关键笔记带锚点（章节+段落+页码）可回原文，
  知识点条目可检索。不套通用摘要模板，锚点经脚本校验，原文没有的信息标
  not_found；先落盘最小 result.json 再充实。
---

# 文献总结与结构化笔记 Skill — 章节对齐 + 锚点回链（v1）

## 1. 用途与适用范围

- 适用：单篇论文 → 结构化笔记：章节对齐的章节摘要 + 字段化论文卡片 + 可检索知识点条目，全部带锚点回链原文。
- 不适用（不做也不报）：脱离原文的通读摘要模板、跨多篇论文的综述生成、笔记质量自动打分。
- 四个验收问题（主线）：
  1. **对得上**：笔记骨架与论文自身章节和论证顺序一致。
  2. **留得住**：研究问题/数据/方法条件/主要发现/局限全记录，尤其结论成立的前提条件。
  3. **找得回**：每条关键笔记指回具体章节/段落/页码/图表。
  4. **用得上**：笔记可检索、可比较、可继续加工（JSONL 字段化）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段——result.json 逐字段落实；case.json 优先于本文。
2. 读 `/input/task.md`：确认笔记字段要求与范围。
3. 盘点材料：有章节结构的文本照主流线；双栏错序先修复阅读顺序（按页序+栏序）；扫描件/加密文档 → 标 partial。
4. 材料缺失 → status=failed + failure_reason。

## 3. 工作流程（五步流水线）

### Step 1 章节切分（→ /app/work/sections.jsonl）

- 按编号模式+字号/加粗特征识别章节层级，每节登记：`{section_id, level, title, page_no, para_range}`。
- 摘要/参考文献/附录单独识别为特殊节。
- 验收断言：节标题逐字来自原文（脚本子串匹配）；层级不跳级。

### Step 2 论文卡片（→ /app/work/paper_card.json）

统一字段，一项一源：

| 字段 | 内容 | 锚点要求 |
|---|---|---|
| research_question | 研究问题 | 引言节锚点 |
| data | 数据/样本（规模、来源） | 锚点 |
| methods | 方法+关键条件（参数、设置、前提） | 方法节锚点 |
| findings | 主要发现（逐条，数值保留） | 结果节锚点 |
| limitations | 局限（含结论成立的前提条件） | 原文明确写的才记；未写标 not_found |
| conclusions | 结论 | 结论节锚点 |

- **纪律**：方法条件（温度/样本量/版本）不省略——"留得住"的核心；原文没有 limitations 字段时 `limitations=null + not_found 登记`，**不套模板编造**。
- 验收断言：每字段有 anchor；数值与原文子串匹配。

### Step 3 章节摘要（→ /app/work/section_notes.jsonl）

- 按论文原章节顺序逐节提炼：`{section_id, purpose, method_or_content, result, transition: "<与上下章的承接关系>"}`。
- 每节 2-4 句，**禁止合并多节成通篇摘要**；节内关键句用 `support_span` 保留原文片段。
- 验收断言：section_notes 数 = 实质章节数（摘要/参考文献除外，缺失要说明）。

### Step 4 知识点条目与锚点校验（→ /app/work/knowledge_points.jsonl）

- 从笔记拆出可检索条目：`{kp_id, type: concept|variable|method|finding, term, definition_or_value, anchor: {section_id, para_id, page_no}, support_span: "<原文片段>", related_kp: [kp_id]}`。
- 缩写/同义表述归并：给 basis，条目不重复不矛盾。
- **锚点校验脚本**（scripts/verify_notes.py）：每个 support_span 在原文中子串匹配；anchor 指向的 section 存在。失败条目回改或标 unresolved。
- 验收断言：verify_notes.py 退出码 0（或仅余 unresolved 且逐条登记）。

### Step 5 result.json 组装（先最小后充实）

- 进入 Step 2 前写最小 result.json（status=partial）；走完覆盖完整版。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "notes": {
    "sections_detected": 0,
    "section_notes": "section_notes.jsonl",
    "paper_card": "paper_card.json",
    "knowledge_points": {"file": "knowledge_points.jsonl", "count": 0}
  },
  "anchors": {
    "format": "section_id+para_id+page_no",
    "verified_count": 0,
    "failed_count": 0
  },
  "evidence_and_boundary": {
    "not_found": ["<原文未写的字段，如 limitations>"],
    "unverifiable": ["<无法确认的笔记条目>"],
    "not_reported": ["<材料未提供项>"]
  },
  "run_status": {"state": "", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["<实际输入文件>"],
  "uncertainty_notes": ["<双栏错序修复说明、存疑归并>"],
  "change_log": []
}
```

## 5. 数字门槛（达不到诚实标 partial）

1. 章节覆盖率 ≥ 实质章节的 90%（缺失节逐条登记原因）。
2. 论文卡片 6 字段有值或有 not_found 登记（无空字段无默认编造）。
3. 锚点校验：support_span 子串匹配率 100%；anchor 指向存在节。
4. 知识点条目无重复（term 归一后唯一）。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 扫描件/加密文档 | 标 partial，OCR 段落置信度登记 |
| 双栏错序 | 按页序+栏序修复并在 uncertainty_notes 说明 |
| 图表/公式缺失 | 相应知识点条目标 unresolved |
| 超长文 | 按章节顺序处理逐节落盘，中断标 partial 写明已处理范围 |
| 无编号章节 | 用标题字号/位置判定层级，判定依据登记 |
| 原文无 limitations | not_found 登记，不编造 |
| output_contract 与本文冲突 | 以 case.json 为准 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] 笔记骨架与论文章节一致，有承接关系
- [ ] 论文卡片字段齐、方法条件未省略
- [ ] 每条关键笔记有锚点且脚本校验通过
- [ ] 知识点可检索无重复；not_found 如实登记

## 8. 效率约束

预算 64 请求 / 900 秒。策略：章节切分、锚点校验、条目查重全脚本化（scripts/verify_notes.py）；模型请求只用于卡片字段抽取与摘要撰写；逐节落盘。限额 ≤50 文件 / 2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"section_id":"S4","title":"4. Experiments","purpose":"验证方法有效性","method_or_content":"在三个基准上与 2 个基线比较","result":"主基准提升 3.2%","transition":"承接 S3 的方法定义，为 S5 分析提供数据","support_span":"outperforms the strongest baseline by 3.2%","anchor":{"section_id":"S4","para_id":"P21","page_no":5}}
{"kp_id":"KP007","type":"finding","term":"conversion at 350C","definition_or_value":"92% CO2 conversion","support_span":"92% CO2 conversion was obtained at 350 C","anchor":{"section_id":"S3","para_id":"P8","page_no":4},"related_kp":["KP003"]}
{"field":"limitations","value":null,"not_found":true,"note":"原文未设 limitations 节，不编造"}
```

（以上为格式示意，正式结果以实际材料运行为准。）
