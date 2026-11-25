---
name: template-fit-adaptor
description: |
  学术 PPT 模板与格式适配：把论文内容真正套进指定模板——先盘点母版/版式/占位符结构
  （template_audit.py），按槽位填充内容并继承主题字体配色，再用 fit_check.py 做版式约束
  校验（溢出/字号下限/长标题），批量一致性规则统一全册页脚页码标题层级，最后导出
  PDF 并逐项校验渲染一致。产物 pptx+PDF+模板审计报告+逐页偏差记录+result.json。
  离线执行，可溯源，不虚构。
---

# 学术 PPT 模板与格式适配（template-fit-adaptor）

## 1. 用途与适用范围

- 场景：给定模板（master/layout 结构）与论文材料，交付"真正套用模板"的可编辑 pptx + 导出件。
- 负责：模板套用、版式约束、字体颜色、图表适配、批量一致性、导出渲染六件事。
- 不负责：论文内容主线再创作（引用相邻课题方法）、科研绘图美化、PPT 软件开发。
- 判断标准（题面）：①指定模板被真实套用（母版/版式/占位符继承关系可查）；
  ②页内内容与源论文和图表对得上；③整册版式与导出可被他人按记录复跑逐页核对。
- 本题是 slides 赛道前人弱项（68.3），执行标准从严：每个适配动作留机器可查的痕迹。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id（原样保留）、任务说明、**模板路径**、材料路径、
   output_contract、页数/受众约束。
2. 读 `/input/task.md`：版式要求、字体要求、导出要求的补充修订。
3. 盘点：模板 pptx 必须存在——**无模板是本题最关键异常**，见 §6；论文/材料缺失 → failed。
4. `/app/work` 过程、`/app/output` 产物；Step 0 末尾先落盘最小 result.json。

## 3. 工作流程（7 步）

### Step 1 模板审计（产出 work/template_audit.json + work/slot_map.json）
```bash
python3 scripts/template_audit.py <template.pptx> work/template_audit.json
```
- 报告内容：幻灯片尺寸、母版数、每版式名称+占位符(idx/type/name)、主题字体(latin/ea)、
  主题色、无占位符版式告警。
- 由审计报告产出 slot_map：**每类页面(role) → 用哪个版式名**（如 cover→"Title Slide"，
  content→第一个含 TITLE+BODY 的版式），占位符缺失的版式标记替代方案。
- 验收断言：template_audit.json 存在且 masters/layouts 非空；slot_map 覆盖 plan 中出现的所有 role。

### Step 2 内容映射（产出 work/slides_plan.json）
- 论文内容按主线四要素(问题/方法/证据/局限)映射到页，字段同通用 schema
  （idx/role/title/claim/bullets/notes/figure/evidence）。
- 长标题规则：title >40 字符改写为短标题+副题进 bullets；多图并列页每图独立 evidence。
- 验收断言：每页 claim+evidence 齐备；quote ≤60 字；title ≤40 字符。

### Step 3 槽位填充构建（产出 output/deck.pptx）
```bash
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx <template.pptx>
```
- **必须传模板路径**：从模板版式创建页面，继承主题字体与主题色，0 处覆盖模板样式；
  图表按容器等比缩放（plan_to_pptx 内置），图号与正文引用一致。
- 验收断言：脚本 ok=true；输出 template_used 为实际模板文件名（非 default）。

### Step 4 版式约束校验（产出 work/fit_report.json）
```bash
python3 scripts/fit_check.py output/deck.pptx --min-font 12 --max-title 40
```
- 逐 shape 校验：溢出风险（字符量 vs 容量启发式）、字号下限（<12pt 拦截，防"压字号硬塞"）、
  长标题。
- 有 risk → 减要点/调字号/换版式后重建（回 Step 3），**禁止以 fit_check FAIL 状态交付 ok**。
- 启发式声明：fit_check 为字符量估算，非渲染级精判；报告随产物交付供复核。

### Step 5 批量一致性（产出 work/consistency_report.json）
- 全册统一规则逐项检查（fit_check + 人工可见项）：页脚/页码/标题位置/留白/字号层级
  逐页一致——用 template_audit 的主题字体色对照，页脚页码由模板母版继承而非逐页手写。
- 检查项写为 checklist：每项 {item, rule, result: pass|fix}，fix 项回 Step 3。
- 验收断言：checklist 覆盖页脚/页码/标题位置/留白/字号 5 项；无未处置的 fix。

### Step 6 导出与渲染一致性（产出 output/deck.pdf + work/export_report.json）
```bash
# 优先环境提供的导出器，例如:
soffice --headless --convert-to pdf output/deck.pptx --outdir output/
python3 scripts/export_check.py output/deck.pptx output/deck.pdf
```
- 校验 PDF 页数==pptx 页数、pptx 可打开、备注覆盖；字体替换/图片丢失现象记入
  rendering_notes（如环境能检测），无法检测如实说明"本地无法验证字体嵌入"。
- 导出失败 → coverage.export=partial，不伪造 PDF。

### Step 7 result.json 与逐页偏差记录（产出 output/result.json）
- version_log 记录每处版式适配动作（哪页、什么偏差、怎么修）；uncertainty/gaps 如实。
- status：模板真实套用+全部校验过 → ok；无模板/导出缺 → partial；材料缺 → failed。

## 4. 输出契约（result.json）

| 字段 | 要求 |
|---|---|
| case_id | 原样保留 |
| status | ok/partial/failed |
| deliverables | {source_pptx, exported_pdf} |
| slides[] | 逐页 {idx, role, title, claim, bullets, notes, figure, evidence{locator, locator_type, quote}} |
| template | {file, audit_report, slot_map{role→layout}, theme_fonts, theme_colors} |
| consistency_checklist[] | {item, rule, result} 五项以上 |
| rendering_notes | 字体/图片/页脚的导出现象记录 |
| coverage | mainline/page_structure/figure_refs/narration/template/export 六要素 |
| version_log[] / uncertainty[] / gaps[] / sources[] | 如实记录 |

示例（**示意输出，非正式案例结果**）：
```json
{"case_id": "<case.json>", "status": "ok",
 "deliverables": {"source_pptx": "deck.pptx", "exported_pdf": "deck.pdf"},
 "template": {"file": "template.pptx", "audit_report": "work/template_audit.json",
   "slot_map": {"cover": "Title Slide", "content": "Title and Content"},
   "theme_fonts": {"majorFont": {"latin": "Calibri", "ea": "DengXian"}},
   "theme_colors": ["4472C4", "ED7D31"]},
 "slides": [{"idx": 2, "role": "method", "title": "方法", "claim": "一句话",
   "bullets": ["要点"], "notes": "讲解",
   "figure": {"ref": "Fig.2", "action": "reuse"},
   "evidence": {"locator": "Section 3", "locator_type": "figure", "quote": "原文短引"}}],
 "consistency_checklist": [{"item": "page_footer", "rule": "由母版继承", "result": "pass"}],
 "rendering_notes": [], 
 "coverage": {"mainline": "done", "page_structure": "done", "figure_refs": "done",
              "narration": "done", "template": "done", "export": "done"},
 "version_log": [], "uncertainty": [], "gaps": [], "sources": ["paper.pdf", "template.pptx"]}
```

## 5. 数字门槛（从严）

| 门槛 | 通过线 |
|---|---|
| 模板真实套用 | 100% 页由模板版式创建；template_used 非 default |
| 母版继承可查 | template_audit.json + slot_map 落盘 |
| 溢出/字号 | fit_check 0 个 overflow/small-font |
| 批量一致性 | checklist 5 项全 pass |
| 数字保真 | 页面数字 100% 见于原文（evidence_lint exit 0） |
| 图表适配 | 等比缩放无拉伸；图号与正文引用一致 |
| 导出一致 | PDF 页数 == pptx 页数 |

## 6. 异常处理表

| 情况 | 识别 | 处置 |
|---|---|---|
| 模板缺失 | Step 0 | **不冒充模板**：status=partial，用默认版式交付并 gaps 注明"未提供模板" |
| 模板缺版式/占位符不足 | template_audit 告警 | slot_map 标记替代方案（文本框），version_log 记录 |
| 文本框溢出 | fit_check overflow | 减要点→调字号→换版式，三级处置后重建 |
| 字体缺失 | 导出错乱/环境告警 | 用模板主题字体（ea 字体优先），rendering_notes 记录替换 |
| 图表源文件失效 | 图片路径不存在 | figure.action=reuse 引用论文原图编号，gaps 注明 |
| 文本框/占位符写不进 | 脚本报错 | 降级为默认版式并 version_log 记录，不中断交付 |
| 导出失败 | soffice 报错 | coverage.export=partial，gaps 注明 |
| 材料缺失 | Step 0 | status=failed + gaps |

## 7. 自查清单

- [ ] case_id 一致；output_contract 全字段落实
- [ ] template_audit.json + slot_map 落盘；母版/版式继承关系可查
- [ ] fit_check exit 0；checklist 5 项 pass
- [ ] evidence_lint exit 0；export_check exit 0（或如实 partial）
- [ ] 图表无拉伸变形；图号与正文引用一致
- [ ] pptx 可打开可逐页编辑；每处版式适配动作在 version_log 可查

## 8. 效率约束（64 请求 / 900 秒）

- 模板审计与映射 ≤6、内容规划 ≤10、构建 ≤4、校验修复循环 ≤10（允许两轮）。
- 中间件固定 6 个（audit/slot_map/plan/fit/consistency/export）；先落盘最小 result.json。

## 9. 最小示例（示意，非正式结果）

```bash
python3 scripts/template_audit.py tpl.pptx work/template_audit.json
# → {"template": "tpl.pptx", "masters": [{"layouts": [...]}], "theme_fonts": {...}, ...}
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx tpl.pptx
# → {"ok": true, "slide_count": 12, "template_used": "tpl.pptx"}
python3 scripts/fit_check.py output/deck.pptx
# → {"ok": true, "risks": [], "note": "启发式估算..."}
```
scripts/ 共 7 个脚本真实可运行（依赖 python-pptx≥0.6；pypdf 可选）。
