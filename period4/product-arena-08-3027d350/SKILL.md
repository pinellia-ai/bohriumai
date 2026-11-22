---
name: pdf-parse-executor
description: |
  文献文档解析 Skill（工具执行版）。用真实 PDF 工具链逐页解析：文本层探测 → pdftotext/
  PyMuPDF 逐页抽取（-layout 保版面顺序）→ 栏序重建 → 章节树/表格（pdfplumber 单元格
  坐标）/公式与特殊字符还原 → 扫描件 tesseract OCR（置信度标注）→ 抽样回对验证。
  交付结构化 Markdown + tables.csv + 章节树 + 运行日志，全部元素带 (page, bbox) 定位。
---

# PDF Parse Executor — 文献文档解析 Skill（工具执行版）

## 0. 运行契约（最高优先）

1. `/input/case.json` 的 `output_contract` 定义 result.json 必须字段——**逐字段原样落实**；`case_id` 原样读取。
2. 过程写 `/app/work/`；最终产物写 `/app/output/`。
3. 读取实际 PDF 文件，不按文件名/标签臆测内容；解析不了的页如实登记。
4. 预算 64 请求 / 900 秒：先落盘最小可用结果，再增强。

## 1. 输入探测（真实执行）

```bash
ls -la /input/
pdfinfo <pdf>            # 页数/版式
pdffonts <pdf>           # 字体（判断文本层质量）
python3 -c "import fitz; d=fitz.open('<pdf>'); [print(i, 'text' if p.get_text().strip() else 'NO-TEXT') for i,p in enumerate(d)]"
```
- 输出按结果分流：**有文本层 → 抽取路线**；**无文本层 → OCR 路线**（tesseract，逐页置信度）。

## 2. 解析流水线（逐步留痕）

### Step 1 逐页原始抽取
- `pdftotext -layout -f N -l N` 逐页抽取，原始文本存 `/app/work/page_N.txt`（版面顺序保留）。
- PyMuPDF 补充块坐标（bbox）→ 每段带 (page, x0,y0,x1,y1) 定位。

### Step 2 版面结构判定
- 用 bbox 分布判断栏数（左/右半页文本块分簇）→ 阅读顺序：左栏自上而下→右栏（跨栏标题按 bbox 高度插入流）。
- 页眉页脚剔除：按 y 坐标区间（页顶/底 5%）识别并记录剔除规则。

### Step 3 结构元素分离
- **章节树**：正则匹配编号标题（1. / 1.1 / I.），挂接段落区间 → sections.json。
- **表格**：pdfplumber `extract_table()` 逐表提取，单元格带 (row, col)；合并单元格按跨行/跨列还原归属；表题（Table N）挂接。
- **题注/脚注/参考文献**：按前缀（Figure/Fig./Table/注/References）分区提取，与正文分开。
- **公式与特殊字符**：数学区文本按块保留，希腊字母/上下标用 Unicode 还原（不丢字符）。

### Step 4 验证抽样（可复核）
- 随机抽 3 段+1 表：解析文本 vs 原页面内容比对（关键数值+字数）；抽检结果写进运行日志。

### Step 5 交付
- `parsed.md`（结构化全文：章节树+段落+题注+参考文献）、`tables.csv`（单元格坐标齐）、`sections.json`、`run_log.md`（每步命令与统计）。

## 3. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "pdf_structured_parsing",
  "status": "success | partial | failed",
  "probe": {"pages":12,"text_layer":true,"columns":2,"tool":"pdftotext+fitz+pdfplumber"},
  "sections": [{"sec_id":"1","title":"Introduction","level":1,"paragraph_range":[1,6]}],
  "paragraphs": [{"p":1,"text":"...","locator":{"page":1,"bbox":[40,60,300,90]},"type":"body"}],
  "tables": [{"table_id":"T1","page":4,"rows":5,"cols":4,"cells":[{"r":1,"c":1,"text":"..."}],"caption":"Table 1 ..."}],
  "formulas": [{"eq_id":"(1)","page":3,"content_unicode":"..."}],
  "ocr_notes": [{"page":7,"confidence":0.86}],
  "verification": {"sampled_paragraphs":3,"sampled_tables":1,"mismatches":0},
  "run_log": "run_log.md",
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：probe 来自真实执行；每元素带 (page, bbox) 定位；表格单元格坐标齐；verification 抽检有记录；run_log 真实命令。

## 4. 异常处理

| 情况 | 处置 |
|---|---|
| 无文本层 | tesseract OCR（psm 3），逐页置信度；<0.6 的页标 needs_review |
| 跨页表格/段落 | 归并 + 标注跨页 |
| 工具缺失 | 依 resources.yaml 可用工具替代；全缺则纯文本层输出 + gaps |
| 复杂版式（旋转页/嵌图） | 该页单独处理或 gaps |

## 5. 自查清单

1. [ ] probe 真实执行（页数/文本层/栏数）？
2. [ ] 逐页抽取落盘、bbox 定位齐？
3. [ ] 表格单元格坐标、合并还原？
4. [ ] 抽样回对通过？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 6. 最小示例（示意，非正式结果）

```json
{"case_id":"demo","probe":{"pages":2,"text_layer":true,"columns":1},
 "sections":[{"sec_id":"1","title":"Intro","level":1,"paragraph_range":[1,2]}],
 "tables":[{"table_id":"T1","page":2,"rows":2,"cols":2,"cells":[{"r":1,"c":1,"text":"5 mg"}],"caption":"Table 1"}],
 "verification":{"sampled_paragraphs":1,"sampled_tables":1,"mismatches":0}}
```

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：extraction_inventory.csv（页数/段落/表格/公式计数，前后对账）
2. verification 抽检表（样本数/mismatch=0）
3. run_log.md 真实命令逐条。
