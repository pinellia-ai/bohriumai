---
name: annotate-knowledge-harvest
description: |
  阅读批注与知识沉淀 Skill：把散落在 PDF 高亮/页边批注/扫描标记/文本批注中的阅读判断，逐条提取为带原文回链的结构化笔记，
  并完成知识关联与可检索入库。方法主线：批注提取（区分类型/颜色/页码/坐标，PDF 真实 annotation 对象优先）→
  锚点校验（摘录文本在原文页内逐字对齐，对不齐标 anchor_shift）→笔记结构化（问题/方法/结论/疑点+来源定位）→
  关联（明确依据，控制过度连接，重复下载与版本归并）→检索入口（tags/实体/来源/时间）。全程离线、哈希留痕、可复跑。
---

# 阅读批注与知识沉淀（Annotate → Structure → Link → Retrieve）

## 1. 用途与适用范围

- **做**：批注提取、笔记结构化、知识关联、后续检索的完整闭环。验收三件事：批注逐条回到原文具体页与位置；笔记论断指到支撑它的原文片段；沉淀条目可被真实问题检索到且他人可复跑。
- **不做**：文献检索发现、内容学术判断、写作润色、目录治理与归档制度建设。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、阅读材料目录（PDF/扫描件/Word/txt 批注清单）、笔记格式要求、输出要求。
2. 盘点：文件数、可读数、含批注的文件数、重复/版本文件组。
3. 无可读材料 → status=failed。

## 3. 工作流程（五步）

### Step 1 批注提取（`annot_extract.py` → annotations.json）
- **PDF 真实批注对象优先**：pypdf 遍历 `/Annots`，逐条取 subtype（Highlight/Underline/Text/Square/FreeText）、contents（批注文字）、颜色 C、页码、坐标 rect。
- **摘录文本**：Highlight/Underline 取被标注的 underlying text（按 rect 与页面文字对齐提取）；提取失败时如实记 `excerpt=null`，不猜。
- **文本类材料**（txt/md/csv）：按行内标记语法（`==高亮==`、`//批注:`、行尾 `#note`）提取，记行号作锚点。
- **扫描件无文本层/无批注对象**：记 `no_annot_layer`，OCR 降级仅作人工核看辅助，坐标标注 `ocr_unverified`。
- 每条批注记录：`{annot_id, file, sha256_8, page, subtype, color, contents, excerpt, rect, type_label}`——类型与颜色不混为一类。

### Step 2 锚点校验（提取脚本内完成）
- 每条带 excerpt 的批注在其所在页文本中做逐字匹配：命中 → `anchor=verified`；因换行/空格断行失配 → 归一空白后再匹配，命中标 `anchor=verified_normalized`；仍失配 → `anchor=anchor_shift` 并给出最接近页内片段（编辑距离最小），**不静默挂到相邻段**。

### Step 3 笔记结构化（模型辅助，≤4 次；产物 notes.json）
- schema：`{note_id, source_annot_ids[], kind: question|method|finding|reusable_point|open_issue, statement, evidence:[{annot_id, file, page, excerpt_snippet}], tags[], confidence}`。
- **批注→笔记多对一**：同页/同主题批注可合并为一条笔记，但 source_annot_ids 保留全链，可反查每条批注。
- statement 只写批注 contents + excerpt 能支撑的判断；批注无文字只有高亮 → kind=reusable_point，statement=摘录原文。

### Step 4 知识关联（产物 links.json）
- 关联依据三型：`same_source_file`（同文件）、`same_entity`（共享作者/方法/材料实体，实体从批注与摘录中抽取）、`same_topic`（共享 tags）。
- **控制过度连接**：仅凭 1 个术语重合不算关联；每条 link 带 `basis` 与强度（strong=多依据，weak=单依据）。
- 重复下载与版本：同哈希副本的批注归并到主文件（记 alias），版本链内批注按版本标注，不分裂。

### Step 5 入库与检索（产物 kb_notes.json + 检索说明）
- notes 全量入库，索引字段：note_id、tags、entities、kind、source file、date、statement。
- 检索入口：`annot_extract.py --query` 模式按 tags/实体/来源/时间过滤+文本匹配；召回不足时提示放宽哪个维度，误召回时给出排除建议。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "annotations": [{"annot_id": "A001", "file": "paper.pdf", "sha256_8": "ab12cd34", "page": 5,
                     "subtype": "Highlight", "color": [1, 0.9, 0.3], "contents": "重要：与本文方法一致",
                     "excerpt": "we used the same lysis buffer", "anchor": "verified", "type_label": "highlight+margin_note"}],
  "notes": [{"note_id": "N001", "source_annot_ids": ["A001", "A002"], "kind": "method",
              "statement": "两者使用相同裂解液配方，可复用", "confidence": "indicative",
              "evidence": [{"annot_id": "A001", "file": "paper.pdf", "page": 5, "excerpt_snippet": "we used the same lysis buffer"}],
              "tags": ["裂解液", "方法复用"], "date": "2024-05-01"}],
  "links": [{"from": "N001", "to": "N003", "basis": "same_entity:lysis buffer + same_topic", "strength": "strong"}],
  "kb": {"note_count": 0, "index_fields": ["tags", "entities", "kind", "source", "date"], "retrieve_example": "tags=裂解液"},
  "operation_evidence": {"hash_algo": "sha256", "annotations_file": "annotations.json",
                          "extraction_script": "annot_extract.py v1", "rerun_cmd": "..."},
  "skipped_or_failed": [{"file": "scan.pdf", "reason": "no_annot_layer", "recovery": "OCR 降级标注 ocr_unverified"}],
  "uncertainty": ["N 条批注 anchor_shift，摘录与页面文字对齐失败，已给最接近片段", "OCR 批注坐标未验证"]
}
```

## 5. 数字门槛

- 锚点可回链率 ≥90%：verified + verified_normalized 占比；anchor_shift 逐条列出（低于 90% → partial）。
- 类型不丢失率 100%：subtype/color/页码全部保留，无"混成一类"。
- 笔记证据率 100%：每条 note 的 statement 至少绑定 1 条批注/摘录；无支撑的判断不写。
- 关联可解释率 100%：每条 link 有 basis。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 加密/损坏 PDF | skipped + recovery，不入提取 |
| 扫描件无批注层 | no_annot_layer 记录，OCR 降级标注 ocr_unverified |
| OCR 置信度低 | 批注内容标 low_confidence，不进正式笔记 |
| 批注来自旧版本文件 | 版本标注 + 归并到版本链 |
| 摘录跨页/断行 | 归一空白后匹配；失败标 anchor_shift |
| 空批注文件 | 该文件 0 条记录，如实写 |

## 7. 自查清单

- [ ] case_id 原样；每条批注有 file+page+subtype。
- [ ] anchor 校验逐条完成，失配显式标注。
- [ ] 每条笔记 statement 有 evidence 回链；links 有 basis。
- [ ] 重复文件批注未分裂；annotations.json/notes.json 可复跑。

## 8. 效率约束

提取与锚点校验全脚本化（<1s/百页）；模型请求只用于笔记结构化与实体归一，≤6 次。先落 annotations.json（纯脚本产物），再做笔记。

## 9. 最小示例（示意输出，非正式案例结果）

`annot_extract.py extract <材料目录> --out annotations.json`
→ `{"annot_id": "A001", "file": "paper.pdf", "page": 5, "subtype": "Highlight", "contents": "方法一致", "excerpt": "we used the same lysis buffer", "anchor": "verified"}`
`annot_extract.py query annotations.json --tags 裂解液` → 返回 N001 及关联笔记。
