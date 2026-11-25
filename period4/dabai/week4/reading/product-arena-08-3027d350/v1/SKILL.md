---
name: scientific-pdf-parse-structured
description: |
  文献文档解析：把科研 PDF 解析成"元数据/节/段/表/图"五层结构化 JSON，不是纯文本堆砌。
  每个元素带页码定位与 bbox 级锚点，处理多栏阅读顺序、页眉页脚剔除、跨页表格合并、
  公式与特殊字符保真；读不出的部分如实标 unresolved，不猜补。
  全程先落盘最小 result.json 再充实；离线执行，不虚构解析内容。
---

# 文献文档解析 Skill — 五层结构化 JSON（v1）

## 1. 用途与适用范围

- 适用：单篇科研 PDF（含双栏/多栏排版）解析为结构化 JSON：标题/作者/摘要/章节层级/段落/表格/图注/公式/参考文献/页眉页脚，每个元素带页码定位。
- 不适用（不做也不报）：图表科学含义理解（图表按结构元素处理）、全文语义问答、扫描件高保真 OCR 重排（受限时如实标 partial）。
- 四个验收问题（主线）：
  1. **提得全**：正文、题注、脚注、参考文献逐字提取，页眉页脚不混入正文。
  2. **排得对**：多栏按阅读顺序输出，不串栏不错行。
  3. **拆得清**：章节层级、表格行列、公式上下标还原为结构。
  4. **核得回**：每段每表指回页码+区块，读不出如实标注。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：提取 `case_id`（**原样保留**）与 `output_contract` 全字段清单——result.json 逐字段落实；case.json 优先于本文任何默认值。
2. 读 `/input/task.md`：确认本次解析范围（全文或指定页区间）与证据要求。
3. `ls -la /input/` 盘点材料；用 `file` 与 `pdffonts`（或 PyPDF2）探测：是否有文字层、是否加密、页数。
4. 判型分支：
   - 加密/损坏 → result.json `status=failed`，`failure_reason` 写明，不虚构。
   - 无文字层扫描件 → 走 OCR 分支（Step 2b），置信度逐元素记录，整体标 partial。
   - 正常文字层 → 主流水线 Step 1。

## 3. 工作流程（六步流水线）

### Step 1 逐页原始提取（→ /app/work/raw_pages/page_N.txt）

- 用 PyMuPDF（fitz，预装 scientific-python 环境）`page.get_text("blocks")` 提取，**保留每个 block 的 bbox 与 page_no**——这是后续一切定位的物证。
- 原始块不做判断直接落盘，供回查。
- 验收断言：文件数=页数；每页非空。

### Step 2 版面分类与阅读顺序（→ /app/work/blocks_classified.jsonl）

- 每 block 标注：`kind ∈ {header, footer, title, section_heading, paragraph, table_region, figure_caption, formula, footnote, reference_entry, page_number}`。
- 页眉/页脚判定：处于页顶/页底 5% 区域、跨页重复出现、或匹配 `^\d+$` 页码模式 → 剔出正文，单独存 `headers_footers.json`（不删除，保留核验）。
- 多栏排序：页面宽度中点分左右栏；同栏内按 bbox.top 排序；跨栏元素（表格/宽图/通栏标题）先于其后内容插回——**每 block 记录 `reading_order` 整数**。
- 跨页续段：页末段与下页首段若句号缺失且同章节 → 合并，标 `merged_across_pages: true`。
- 验收断言：reading_order 无重复且连续；正文块无 header/footer。

### Step 3 章节层级重建（→ /app/work/sections.json）

- 以编号模式（`^\d+(\.\d+)*\s`、`^\d\.\d`）+ 字号/加粗特征判定层级：1 → 1.1 → 1.1.1。
- Abstract / References / Acknowledgments 无编号标题单独识别。
- 每节记录：`section_id`（S01…）、`level`、`title`、`page_no`、`parent`。
- 验收断言：层级编号单调不跳级（跳级登记 warning）；段落全部归属某节，归属不了的进 `unsectioned`。

### Step 4 表格结构还原（→ /app/work/tables.json）

- 检测：块含多列对齐文本或 `page.find_tables()`（PyMuPDF 内置）。
- 还原为 `{"table_id","page_no","n_rows","n_cols","cells":[{"row","col","text","is_header"}],"merges":[...]}`；多层表头拆成多行 header。
- 跨页续表：表头重复或行样式连续 → 合并，标 `merged_pages:[p,q]`；不能确定是否同一表 → 分开保留，不猜。
- 同时输出 Markdown 渲染版（`tables.md`）便于人工复核。
- 验收断言：每表行列计数与单元格文本非空率对账；单元格字符数异常（>500）标 warning。

### Step 5 图注/公式/参考文献（→ /app/work/figures.json, formulas.json, references.json）

- 图注：匹配 `^(Figure|Fig\.?|图)\s*\d+` 的块，绑 `figure_id` + 页码。
- 公式：块中含数学符号密度高（∑∫±×≤等 + 上下标字符）或独立居中行 → `{"formula_id","page_no","text_verbatim","display_type"}`；**逐字保留 Unicode 符号与上下标**，不做语义化重写；无法保留的结构记入 `lost_symbols`。
- 参考文献：References 节内按 `[N]` / `^\d+\.` 切分，逐条编号，页码记录。
- 验收断言：Figure 引用数与图注数对账（差值登记）；references 条数 ≥5 或标 warning。

### Step 6 result.json 组装（先最小后充实）

- 进入 Step 1 后立即写最小 result.json（`status=partial`，仅 case_id+status），此后每步完成刷新一次——任何中断都有可评分产物。
- 最终按 output_contract 全字段组装（见 §4）。

## 4. 输出契约

result.json（以 case.json output_contract 为最高优先，以下为基准全集）：

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "document": {
    "metadata": {"title": "", "authors": [], "affiliations": [], "abstract_section_id": "S00", "n_pages": 0, "has_text_layer": true},
    "sections": [{"section_id": "S01", "level": 1, "title": "", "page_no": 1, "parent": null}],
    "paragraphs": [{"para_id": "P0001", "section_id": "S01", "page_no": 1, "reading_order": 3, "text": "", "merged_across_pages": false}],
    "tables": [{"table_id": "T01", "page_no": 3, "n_rows": 4, "n_cols": 5, "cells": [], "merged_pages": []}],
    "figures": [{"figure_id": "F01", "page_no": 2, "caption": "", "caption_anchor": "page_no+block_index"}]
  },
  "evidence_and_boundary": {
    "locator_format": "page_no + block bbox + para_id/section_id/table_id",
    "unresolved": [{"element": "", "reason": "no_text_layer|ambiguous_layout|corrupt", "page_no": 0}],
    "headers_footers_removed": ["<逐页清单>"],
    "not_reported": ["<材料未提供项>"]
  },
  "run_status": {"state": "success|partial|failed", "failure_reason": "", "manual_intervention_point": ""},
  "sources": ["/input/...实际文件"],
  "uncertainty_notes": ["<OCR 置信度低的段落、跨页合并存疑项>"],
  "change_log": ["partial→完整版本变化"]
}
```

- 结构要求：**五层齐备**（metadata/sections/paragraphs/tables/figures），任何一层为空须写明原因；禁止只输出一整块纯文本。

## 5. 数字门槛（达不到诚实标 partial）

1. 段落 100% 有 page_no + reading_order；表格 100% 有 cells 结构。
2. 页眉页脚剔除有逐页清单；跨页合并逐条标注。
3. unresolved 条目逐条给原因码；数量与位置可复查（raw_pages/ 留存）。
4. 元数据五项（title/authors/affiliations/abstract/n_pages）取不到的逐项标 not_found。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 加密/损坏 PDF | status=failed + failure_reason，不猜测内容 |
| 无文字层 | OCR 分支，逐块置信度入 uncertainty_notes，整体 partial |
| 双栏串行风险 | 中点分栏+reading_order 显式记录，跨栏元素插回 |
| 图片型表格 | 登记 unresolved（reason=image_table），不虚构单元格 |
| 乱码字体（pdffonts 显示 Type3/缺 ToUnicode） | 相关段标 unresolved，不硬转 |
| 页码错乱/无页码 | 以物理页序为准，登记说明 |
| output_contract 与本文冲突 | 以 case.json 为准，run_log 记录 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 全字段落实
- [ ] 五层结构齐备且每元素带页码定位
- [ ] reading_order 连续无重复；页眉页脚未混入正文
- [ ] 表格有行列结构；公式符号逐字保留
- [ ] unresolved/not_found 如实登记，无猜补内容
- [ ] raw_pages/ 过程留存可回查

## 8. 效率约束

预算 64 请求 / 900 秒。策略：提取/分类/表格/组装全部脚本化（scripts/build_parse.py 一次跑通）；模型请求只用于疑难版式判断与章节语义校对；先落盘最小 result.json。资源限额 ≤50 文件 / 单文件 ≤500KB / 总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

```json
{"para_id":"P0012","section_id":"S03","page_no":4,"reading_order":17,"text":"We evaluate the proposed method on three benchmarks...","merged_across_pages":true}
{"table_id":"T02","page_no":5,"n_rows":6,"n_cols":4,"cells":[{"row":0,"col":0,"text":"Method","is_header":true}],"merged_pages":[5,6]}
{"element":"table near p.7 top","reason":"image_table","page_no":7}
```

（以上为格式示意，正式结果以实际材料运行为准。）
