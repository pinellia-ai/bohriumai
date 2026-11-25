---
name: academic-deck-generate-edit
description: |
  学术 PPT 生成与编辑：双模式流水线——生成模式从论文/提纲产出页级骨架与可编辑 pptx；
  编辑模式按指令(压缩/扩写/换受众/换语言)定位到页与字段做局部修改，术语与数字锁定。
  每轮迭代由 deck_diff.py 记录逐页变更，版本可比对、改坏可回退。全程离线、可溯源、
  不虚构内容；产物为 pptx+PDF+result.json 三件套。
---

# 学术 PPT 生成与编辑（academic-deck-generate-edit）

## 1. 用途与适用范围

- 场景：组会/开题/答辩/评审等需要把同一份研究材料"翻译"成幻灯片，并经历多轮修改。
- 生成模式：论文正文/结果段落/提纲 → 页序规划 → 可编辑整稿骨架。
- 编辑模式：按自然语言指令修改已有 deck——压缩、扩写、换受众、换语言，**只动指令指向的页与字段**。
- 迭代模式：多轮修改全程版本化，每轮产出变更记录，可回退到任一版。
- 不负责：论文精读与文献综述、数据可视化算法本身、文字润色、PPT 软件开发。
- 失败模式对照（题面列举，本 skill 逐条设防）：整段塞文本框→要点数上限；数字按印象取整→
  数字保真校验；占位图/凭空曲线→图表 action 必须有来源；改一页坏母版→只改内容占位符；
  导出崩版→导出校验；无法回到上一版→版本化 diff 记录。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id（原样保留）、任务说明、材料路径、output_contract、
   **判断模式**：无已有 deck → 生成模式；有 starting deck/计划 → 编辑或迭代模式。
2. 读 `/input/task.md`：页数上限、受众、语言、模板约束等任务边界。
3. 盘点：论文/提纲文件、已有 deck.pptx 或 deck_plan.json、模板。逐一确认存在可读。
4. 缺材料 → `result_scaffold.py` 落盘 `status=failed`，gaps 注明，不虚构。
5. 目录：`/app/work` 过程、`/app/output` 产物。**Step 0 末尾先落盘最小 result.json**。

## 3. 工作流程

### A. 生成模式（3 步）

#### A1 内容取舍与页序规划（产出 work/slides_plan.json）
- 叙事角色逐页指定：`cover / problem / method / evidence / result / limitation / conclusion / backup`。
- 取舍规则：关键结果单独成页；方法压到 ≤2 页；每页唯一 claim（一句话）；bullets ≤4 条且每条 ≤18 字；
  长段落改写为可讲述短语——**改写只做压缩，不改数字/术语/结论方向**。
- 图表决策：`figure.action ∈ reuse|redraw|omit`；redraw 仅限"有数据表支撑的图"，且必须
  记录数据来源 locator；凭空绘制 = 禁止。
- 验收断言：每页有 claim+evidence(locator,locator_type,quote)；页数 ≤ 任务上限。

#### A2 构建 pptx（产出 output/deck.pptx）
```bash
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx [template.pptx]
```
- 备注与页面内容互补：notes 写"过渡语、强调点、被追问时的补充证据"，不重复页面文字
  （plan_to_pptx 会把 claim+evidence 追加到备注尾部供溯源）。
- 验收断言：脚本 `"ok": true`；每页备注非空；模板样式未被覆盖。

#### A3 导出与校验（产出 output/deck.pdf + work/*_report.json）
```bash
python3 scripts/export_check.py output/deck.pptx output/deck.pdf   # 或仅 pptx
python3 scripts/evidence_lint.py output/result.json <source_plain.txt>
```
- 校验项与处置同 SKILL.md §6 异常处理表；FAIL 修复后重跑，不带 FAIL 交 ok。

### B. 编辑模式（4 步）

#### B1 指令解析（产出 work/edit_ops.json）
- 把自然语言指令解析为结构化操作：`{op: compress|expand|restyle|translate,
  target: {slide_idx 或 title 匹配, field: bullets|notes|claim}, detail}`。
- 指令指向不明确 → 在 uncertainty 记录假设（如"按标题匹配第 3 页"），不改错页。
- 验收断言：每个 op 有明确 target；target 页必须存在于现有计划。

#### B2 局部修改（产出 work/slides_plan_v{n}.json）
- **只改 target 字段**；术语/符号与论文一致（对照 locator_index 或原文摘录）；
  换语言时数字、单位、图表编号不翻译不改写。
- 术语锁定表：修改前建立 `work/glossary.json`（方法名/数据集名/指标名 原文写法），
  修改后逐项核对未走样。
- 验收断言：diff 结果只包含 target 字段变化（用 B3 验证）。

#### B3 版本记录（产出 work/changelog_v{n}.json）
```bash
python3 scripts/deck_diff.py work/slides_plan_v{n-1}.json work/slides_plan_v{n}.json work/changelog_v{n}.json
```
- changelog 记录新增/删除/移动/字段级 diff；version_log 写入"改了什么、为什么改"。
- 回退协议：任一版计划文件保留于 work/，回退 = 用旧版计划重跑 A2/B4。
- 验收断言：changelog 与指令意图一致；意外字段变化必须回退或修正。

#### B4 重建与校验（产出 output/deck.pptx / deck.pdf）
```bash
python3 scripts/plan_to_pptx.py work/slides_plan_v{n}.json output/deck.pptx [template.pptx]
python3 scripts/export_check.py output/deck.pptx output/deck.pdf
python3 scripts/evidence_lint.py output/result.json <source_plain.txt>
```
- 每轮重建后必须过导出校验；不过则修复该轮变更，禁止"改坏再手动改回模板"。

### C. 迭代收尾

- result.json：`version_log[]` 逐轮记录 {round, changed, reason}；最终版计划即交付版。
- 交付版标记：result.json `deliverables.source_pptx` 指向最终轮 pptx。

## 4. 输出契约（result.json）

| 字段 | 要求 |
|---|---|
| case_id | 原样保留 |
| status | ok/partial/failed 诚实判定 |
| deliverables | {source_pptx, exported_pdf} 最终版路径 |
| slides[] | 最终版逐页 {idx, role, title, claim, bullets, notes, figure, evidence} |
| coverage | mainline/page_structure/figure_refs/narration/template/export 六要素 |
| version_log[] | 每轮 {round, changed, reason}——多轮迭代题的关键证据 |
| uncertainty[] | 指令歧义假设、无法执行的操作及原因 |
| gaps[] | 材料缺失项 |
| sources[] | 输入材料清单 |

示例（**示意输出，非正式案例结果**）：
```json
{"case_id": "<case.json>", "status": "ok",
 "deliverables": {"source_pptx": "deck.pptx", "exported_pdf": "deck.pdf"},
 "slides": [{"idx": 2, "role": "result", "title": "主结果", "claim": "一句话",
   "bullets": ["要点"], "notes": "补充证据提示",
   "figure": {"ref": "Fig.3", "action": "reuse"},
   "evidence": {"locator": "Section 4.2", "locator_type": "section", "quote": "原文短引"}}],
 "coverage": {"mainline": "done", "page_structure": "done", "figure_refs": "done",
              "narration": "done", "template": "done", "export": "done"},
 "version_log": [{"round": 1, "changed": "初稿 10 页", "reason": "生成"},
                 {"round": 2, "changed": "p3 bullets 压缩 6→4 条", "reason": "指令: 压缩方法页"}],
 "uncertainty": [], "gaps": [], "sources": ["paper.pdf"]}
```

## 5. 数字门槛

| 门槛 | 通过线 |
|---|---|
| 编辑局部性 | 修改后 diff 只含 target 字段，100% |
| 术语保真 | glossary 逐项一致，0 走样 |
| 数字保真 | 页面数字 100% 见于原文（evidence_lint exit 0） |
| 备注覆盖 | 100% 页非空且不复制页面文字 |
| 导出一致性 | PDF 页数 == pptx 页数 |
| 版本可回溯 | 每轮 changelog 落盘，work/ 保留全部版本计划 |

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 论文缺图/图无法提取 | figure.action=omit，notes 说明"图缺失，正文定位代替" |
| 图片为位图无法取数 | action=reuse 只引用；redraw 仅当有数据表 |
| 模板槽位不足 | 文本框替代 + version_log 记录 |
| 字体缺失/导出失败 | 换主题字体或标 partial，不伪造 PDF |
| 页数超限 | 支撑细节并入备用页 |
| 编辑指令与任务边界冲突（如要求删主证据页） | 执行但在 uncertainty 记录风险提示 |
| 材料缺失 | status=failed + gaps，不虚构 |

## 7. 自查清单

- [ ] result.json 含 case_id，output_contract 全字段落实
- [ ] 生成：页序有叙事角色，非按目录搬运
- [ ] 编辑：diff 局部性验证通过；术语锁定表核对通过
- [ ] 每轮 changelog 落盘；可指出任一版本的回退方式
- [ ] export_check / evidence_lint exit 0（或如实 partial）
- [ ] pptx 可打开可编辑；无母版损坏

## 8. 效率约束（64 请求 / 900 秒）

- 生成 ≤14 请求、每轮编辑 ≤6 请求、校验修复 ≤6；余量留异常。
- work/ 中保留所有版本计划（文本文件，体积小）；产物三件套固定。
- 先落盘最小 result.json；每轮结束即写回 version_log。

## 9. 最小示例（示意，非正式结果）

```bash
# 生成
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx
# → {"ok": true, "slide_count": 10, "output": "output/deck.pptx", ...}
# 编辑第3轮：压缩主结果页
python3 scripts/deck_diff.py work/slides_plan_v2.json work/slides_plan_v3.json work/changelog_v3.json
# → {"summary": "新增0页 删除0页 修改1页", "changed": [{"slide": "主结果", "fields": ["bullets", ...]}]}
python3 scripts/export_check.py output/deck.pptx output/deck.pdf
# → {"ok": true, "slide_count": 10, "pdf_pages": 10, ...}
```
scripts/ 共 5 个脚本真实可运行（依赖 python-pptx≥0.6；pypdf 可选用于 PDF 页数）。
