---
name: pdf-structured-parser
description: |
  文献文档解析 Skill（PDF 结构化解析）。提取全：正文/题注/脚注/参考文献逐字提取，
  页眉页脚不混入；排得对：双栏/多栏/跨栏跨页按版面顺序输出，不串栏不串行；拆得清：
  章节层级、表格行列归属、公式上下标与希腊字母还原；扫描件走 OCR 并标注置信度。
  图表与公式按结构元素识别（不要求科学含义）。输出带定位的结构化文档。
---

# PDF Structured Parser — 文献文档解析 Skill

## 1. 用途与适用范围

三问：提得全（逐字提取，页眉页脚不混入）、排得对（多栏/跨页按原版面顺序）、拆得清（章节/表格/公式结构还原）。图表与公式按**结构元素**识别，不解读科学含义。聚焦一种版式或一个问题即可。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、PDF 文件位置。
2. 用 PDF 工具探测：页数、文本层有无、栏数、版式类型。
3. 扫描件（无文本层）→ OCR 路线，置信度逐页标注；OCR 失败页登记 gaps。

## 3. 工作流程

### Step 1 版面分析
- 识别栏结构（单/双/多栏）、页眉页脚区域、题注区、正文区边界（按页记录）。
- 阅读顺序重建：双栏先左栏后右栏；跨栏标题/图表按版面位置插入流。

### Step 2 逐字提取（提得全）
- 正文流：段落编号连续，**不漏行不丢段**；页眉页脚/行号/水印剔除并记录剔除规则。
- 图表题注、脚注、参考文献单独分区提取（与正文分开标注）。
- 特殊字符与希腊字母、上下标保真（Unicode 表示，不丢字母）。

### Step 3 结构还原（拆得清）
- 章节层级树：编号+标题+层级，与正文段落挂接。
- 表格：行列结构还原，合并单元格按归属拆分，表头与数据行区分——每个单元格带 `(row, col)` 坐标。
- 公式：按块提取，上下标层级与希腊字母还原（LaTeX 或 Unicode），不合并不丢项。

### Step 4 定位与校验
- 每个结构元素带源定位：`{page, region, bbox 或 段落号}`。
- 自查抽样：随机抽段落与表格回原文图像/文本层比对（字数+关键值）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "pdf_structured_parsing",
  "status": "success | partial | failed",
  "document": {"pages":12,"layout":"two-column","text_layer":true},
  "sections": [{"sec_id":"1","title":"Introduction","level":1,"children":[],"paragraphs":[1,6]}],
  "paragraphs": [{"p":1,"text":"原文文本","locator":{"page":1,"column":1},"type":"body | caption | footnote | reference"}],
  "tables": [{"table_id":"T1","page":4,"rows":5,"cols":4,"cells":[{"r":1,"c":1,"text":"..."}],"merged_cells_restored":true}],
  "formulas": [{"eq_id":"(1)","page":3,"latex_or_unicode":"...","subscript_ok":true}],
  "ocr_notes": [{"page":7,"confidence":0.86}],
  "extraction_rules": {"header_footer_removal":"...","reading_order":"left-column-first"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：paragraphs 连续编号无断档（剔除项有记录）；tables 单元格坐标齐；公式上下标保真；ocr 置信度如实。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 无文本层 | OCR + 置信度标注；失败页 gaps |
| 跨页表格/段落 | 归并并标注跨页位置 |
| 版面不规则 | 分区域处理 + uncertainty 说明 |
| 预算不足 | 版面分析+正文流优先（partial） |

## 6. 自查清单

1. [ ] 正文流连续无断档？页眉页脚剔除有规则？
2. [ ] 多栏顺序正确？跨栏跨页不串？
3. [ ] 表格行列/合并单元格还原？公式上下标保真？
4. [ ] 每个元素带定位？抽样回对通过？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。版面分析先行；文本提取脚本化批量；结构还原按类型分批。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
