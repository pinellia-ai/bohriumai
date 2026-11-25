---
name: paper-to-academic-slides
description: |
  论文转学术 PPT：把固定论文/研究材料转换为主线成立、证据可追溯、模板合规、可编辑可放映的学术汇报。
  方法主线：主线抽取(问题/方法/证据/局限) → 页级主张+图表引用 → 讲稿备注互补 → 模板占位符填充
  → 可编辑 pptx + PDF 导出 + 逐页校验。全程离线，事实只来自输入材料，不可溯源的内容标 gap，
  不虚构图表、数字或评测结果。
---

# 论文转学术 PPT（paper-to-academic-slides）

## 1. 用途与适用范围

- 输入：一篇论文（PDF/文本/Markdown）+ 可选模板 pptx + case.json 任务说明。
- 输出：可编辑 deck.pptx、导出 deck.pdf、页级证据映射、result.json 三件套。
- 负责：论文内容如何变成"可讲、可核验、可编辑"的学术 PPT——主线重写、页结构、
  图表引用、讲解备注、模板约束、导出校验。
- 不负责：论文精读结论的再创作、科研绘图的美化设计、学术写作润色。
- 核心判断标准（题面原文）：①主线与论文自身贡献一致而非按段落搬运；②每页内容可回溯到
  论文的图/表/章节/数据；③成品在指定模板与软件中可打开、播放、编辑，他人可按记录复跑。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id（原样保留）、任务说明、材料路径、output_contract、页数/时长约束。
2. 读 `/input/task.md`（若存在）：补充的任务边界与修订。
3. 盘点材料：论文文件、模板文件、图表资源。逐一确认文件存在且可读。
4. 材料缺失 → `result_scaffold.py` 先落盘 `status=failed` 的 result.json，注明缺失项，不虚构。
5. 初始化工作目录：`/app/work`（过程），`/app/output`（产物）。
   **先跑 `result_scaffold.py` 落盘最小 result.json，再逐步充实**——保证任何中断都有可评分产物。

## 3. 工作流程（7 步流水线）

### Step 1 论文解析与定位坐标（产出 work/locator_index.json）
- 从论文提取段落级坐标：`{section, para_idx, text}`；图表清单：`{ref(Fig./Table N), caption, page}`。
- 公式为图片或 PDF 加密无法取文本 → 记入 uncertainty，用 OCR/人工可见部分定位，禁止补造数值。
- 验收断言：locator_index 非空；图表清单条目数与论文中 "Fig./Table" 出现数一致（±合理容差）。

### Step 2 主线抽取（产出 work/mainline.json）
- 四要素模板：`problem / method / evidence / limitation`（+`conclusion`）。
- 每个要素 ≤3 条，每条必须带 locator（章节+段落或图表号），区分主结论与支撑细节。
- **禁止按论文目录顺序搬运**；先问"这篇论文的贡献是什么"，再决定讲什么。
- 验收断言：四要素齐备（缺失要素标注 `gap: 论文中无对应内容`，而非编造）；每条有 locator。

### Step 3 页级规划（产出 work/slides_plan.json）
- 页序模板：封面 → 问题 → 方法(1-2页) → 主证据(每图/表可单独成页) → 局限 → 结论 → (备用页)。
- 每页字段：`idx, role, title(≤20字), claim(唯一主张一句话), bullets(≤4条,每条≤18字),
  notes(备注,不重复页面文字), figure{ref, action: reuse|redraw|omit}, evidence{locator, locator_type, quote}`。
- 页数约束：按 case.json 指定（如未指定，10-15 页）；每页信息密度：主张1句+要点≤4条。
- 图表引用规则：编号、单位、图注与论文原文逐字一致；示意图必须标 `action: reuse` 且备注注明
  "示意，非实验数据"；讲不到的图进备用页。
- 验收断言：每页有唯一 claim 与 evidence；quote 为原文 ≤60 字短引；figure.ref 与 locator_index 一致。

### Step 4 构建 pptx（产出 output/deck.pptx）
```bash
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx [template.pptx]
```
- 有模板：从模板母版/版式创建页面（继承主题字体与配色，不覆盖模板样式）。
- 无模板：使用默认版式，标题/正文占位符结构保持，他人仍可逐页编辑。
- 每页备注自动写入：`notes` + `[主张]` + `[证据] locator: quote`（可溯源）。
- 验收断言：脚本输出 `"ok": true`；slide_count == slides_plan 页数；每页备注非空。

### Step 5 导出 PDF（产出 output/deck.pdf）
- 优先用环境提供的导出工具（soffice/libreoffice/平台导出器），命令例如：
  `soffice --headless --convert-to pdf output/deck.pptx --outdir output/`
- 导出失败 → result.json `coverage.export=partial`，在 gaps 注明"PDF 未生成，pptx 已可编辑"，
  不伪造 PDF。

### Step 6 证据与导出校验（产出 work/lint_report.json, work/export_report.json）
```bash
python3 scripts/evidence_lint.py output/result.json work/locator_index.json source_plain.txt
python3 scripts/export_check.py output/deck.pptx [output/deck.pdf]
```
- evidence_lint：逐页 locator/quote 齐备、**数字保真**（页面数字必须能在论文原文找到，
  防"按印象取整"）、六要素 coverage 检查。FAIL 项逐条修复后重跑。
- export_check：pptx 可打开、备注页数一致、PDF 页数==幻灯片页数。
- 校验不过：修 slides_plan 或 result.json 后重跑，**不允许带 FAIL 提交 status=ok**。

### Step 7 result.json 充实与版本记录
- 逐字段落实 §4 契约；version_log 记录每轮修改（改了哪页、为什么）；uncertainty/gaps 如实填写。
- status 判定：全部校验过 → ok；PDF 缺失/部分页 gap → partial；材料缺失/构建失败 → failed。

## 4. 输出契约（result.json 逐字段）

| 字段 | 要求 | 来源 |
|---|---|---|
| case_id | 原样保留 /input/case.json 的 case_id | Step 0 |
| status | ok / partial / failed，诚实判定 | Step 7 |
| deliverables.source_pptx | 可编辑 pptx 相对路径 | Step 4 |
| deliverables.exported_pdf | 导出 pdf 相对路径（可为 null） | Step 5 |
| slides[] | 每页 {idx, role, title, claim, bullets, notes, figure, evidence{locator, locator_type, quote}} | Step 3 |
| coverage | mainline/page_structure/figure_refs/narration/template/export 六要素 done/partial/na | Step 6 |
| version_log[] | 每轮修改记录 {round, changed, reason} | Step 7 |
| uncertainty[] | 无法确认的事项（公式为图片、图表无法提取等） | 各步 |
| gaps[] | 材料缺失/论文中不存在的必需内容 | 各步 |
| sources[] | 引用的输入材料文件清单 | Step 0 |

示例（**示意输出，非正式案例结果**）：
```json
{
  "case_id": "<来自case.json>",
  "status": "partial",
  "deliverables": {"source_pptx": "deck.pptx", "exported_pdf": null},
  "slides": [{"idx": 1, "role": "cover", "title": "标题", "claim": "一句话主张",
    "bullets": ["要点"], "notes": "讲解提示",
    "figure": {"ref": "Fig.1", "action": "reuse"},
    "evidence": {"locator": "Section 1 / Fig.1", "locator_type": "figure",
                 "quote": "原文短引"}}],
  "coverage": {"mainline": "done", "page_structure": "done", "figure_refs": "done",
               "narration": "done", "template": "partial", "export": "partial"},
  "version_log": [{"round": 1, "changed": "初稿", "reason": "-"}],
  "uncertainty": ["公式为图片无法取文本，数值以图为准未复核"],
  "gaps": [], "sources": ["paper.pdf", "template.pptx"]
}
```

## 5. 数字门槛（达不到诚实标 partial）

| 门槛 | 通过线 | 处理 |
|---|---|---|
| 页级溯源率 | 100% 页有 evidence.locator+quote | 缺失页降级 partial |
| 数字保真 | 页面数字 100% 见于原文 | evidence_lint exit 1 必须修 |
| 备注覆盖 | 100% 页有非空备注 | 缺失页先补再交付 |
| PDF 一致性 | PDF 页数 == pptx 页数 | 不一致修导出，无导出工具标 partial |
| 模板合规 | 有模板时 0 处覆盖模板样式 | 覆盖即修 |

## 6. 异常处理表

| 情况 | 识别 | 处置 |
|---|---|---|
| PDF 加密/无法取文本 | 解析报错 | 记 uncertainty；用可见部分定位；status=partial |
| 图表为位图无法取数 | 图表清单无对应数据 | 该页 action=reuse，只引用不改写数值 |
| 公式为图片 | 无公式文本 | 图注引用公式编号，不复现推导 |
| 模板占位符不足 | plan_to_pptx 输出或人工检查 | 用文本框替代，version_log 记录替代原因 |
| 页数超限 | 页数 > case 约束 | 合并支撑细节进备用页，主证据不删 |
| 字体缺失 | export_check 警告或导出错乱 | 换模板主题字体，记录替换 |
| 导出失败 | soffice 报错 | coverage.export=partial，gaps 注明 |
| 材料缺失 | Step 0 | status=failed + gaps，不虚构 |

## 7. 自查清单（提交前逐项过）

- [ ] result.json 含 case_id 且与 /input 一致
- [ ] output_contract 全字段落实；status 判定有依据
- [ ] 每页 claim 唯一、bullets ≤4 条、quote ≤60 字
- [ ] 图表编号/单位/图注与论文逐字一致；示意图未当实验数据
- [ ] evidence_lint.py exit 0；export_check.py exit 0（或如实 partial）
- [ ] deck.pptx 可打开可编辑；PDF 存在且页数一致
- [ ] uncertainty/gaps/version_log 如实，无编造

## 8. 效率约束（64 请求 / 900 秒内）

- 请求预算分配：解析与定位 ≤8、主线与页规划 ≤10、构建与导出 ≤6、校验修复 ≤8、余量留修复。
- 文件预算：产物三件套 + work 中间件 ≤15 个；脚本目录只含随附 scripts（≤7 文件）。
- 先落盘最小 result.json（Step 0 末尾），每完成一步即增量写回，任何中断均可评分。

## 9. 最小示例（示意，非正式结果）

输入：论文 PDF（含 Section 4.2 "accuracy 92.3% on DatasetX, latency 41ms"）+ 无模板。
```bash
python3 scripts/result_scaffold.py demo-case output/
# → {"ok": true, "path": "output/result.json", "action": "created"}
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx
# → {"ok": true, "slide_count": 3, "output": "output/deck.pptx", "template_used": "python-pptx default"}
python3 scripts/evidence_lint.py output/result.json work/source_plain.txt
# → {"ok": true, "status": "ok", "checks": [...], "number_mismatches": []}
```
skill 使用：Agent 按本文档 Step 0→7 顺序执行；scripts/ 目录下 5 个脚本均为真实可运行
（依赖 python-pptx≥0.6、pypdf 可选；见 scripts/ 各文件 docstring 的用法与退出码约定）。
