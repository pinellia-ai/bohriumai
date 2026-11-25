---
name: academic-talk-content-planner
description: |
  学术汇报内容组织：以"报告目标+听众+时长"三约束驱动，从源材料组织出可直接上台的汇报——
  目标转可检查指标 → 听众画像定铺垫比例 → 叙事顺序取舍 → 页级主张+证据强度标注 →
  问答准备(备用页+追问口径)。每页论断可回溯源材料位置，取舍过程落盘可复核。
  产物：可编辑 pptx + PDF + 页级证据映射 + qa_pack + result.json。离线执行，不虚构。
---

# 学术汇报内容组织（academic-talk-content-planner）

## 1. 用途与适用范围

- 场景：组会（方法与进度）、答辩（创新点与边界）、评审（结论与证据强度）等汇报的内容组织。
- 负责：报告目标→听众→叙事顺序→重点信息→问答准备这条组织链路，以及成稿交付与导出校验。
- 不负责：论文精读、学术写作成稿、科研绘图素材生产（可用相邻课题产出作为输入）。
- 判断标准（题面）：①每页论断能在源材料找到对应位置；②叙事顺序服务于指定听众与时长；
  ③取舍过程可被他人复核。
- 与通用 PPT 生成的差异：多三个组织层——目标指标化、听众适配、问答准备。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id（原样保留）、任务说明、材料路径、output_contract。
2. 提取三约束：**目标**（case.json/task.md 明示，或按材料类型推断并记入 uncertainty）、
   **听众**（先验知识/关注点/可能质疑）、**时长与页数上限**（如 15 分钟 ≤18 页）。
   三约束缺失任何一项 → 在 result.json uncertainty 记录"采用默认值 XX，依据任务说明推断"。
3. 盘点源材料：论文/研究报告/结果数据。缺失 → result_scaffold.py 落盘 failed，不虚构。
4. `/app/work` 过程、`/app/output` 产物；Step 0 末尾先落盘最小 result.json。

## 3. 工作流程（6 步）

### Step 1 目标指标化（产出 work/talk_brief.json）
- 把"这次汇报要达成什么"转成可检查目标，例如：
  `{goal: "让评委认可方法新颖性", checks: ["方法页含与已有方法的对照表",
  "创新点有明确 claim+证据强度标注"], page_budget: 12, minutes: 15}`。
- 每个目标至少 1 条可检查项；页数预算按 分钟×1.2 页/分钟 上限。
- 验收断言：talk_brief.json 含 goal/checks/page_budget/audience 三段式结构。

### Step 2 听众画像（写入 talk_brief.json）
- 三字段：`prior_knowledge`（决定背景铺垫页数 0-2）、`concerns`（决定证据深度），
  `expected_questions`（决定问答准备范围）。
- 映射规则（写明依据，供复核）：同行→背景≤1页；跨领域→背景2页+术语表页；
  评审→结论前置、证据强度逐页标注。

### Step 3 叙事顺序与页级主张（产出 work/slides_plan.json）
- 主骨架"问题—方法—结果—结论"，按听众做取舍铺垫，形成起承转合，**不按论文目录搬运**。
- 每页字段：`idx, role, title(≤20字), claim(唯一主张), evidence_strength ∈
  {strong(直接实验证据)/medium(间接/对照)/weak(推断/示意)}, bullets(≤4条), notes,
  figure{ref,action}, evidence{locator, locator_type, quote}`。
- claim 与 evidence_strength 必须匹配：weak 证据不得表述为确定结论（"提示/可能"措辞）。
- 验收断言：每页 claim+strength+evidence 齐备；quote ≤60 字原文短引；页数 ≤ page_budget。

### Step 4 问答准备（产出 work/qa_pack.json）
- 按 `expected_questions` 与局限页生成 ≥3 组问答：`{question, slide_ref(指向页 idx),
  answer_key(口径一致的要点 ≤3 条), backup_slide(可选, idx=9x 编号的备用页)}`。
- 备用页进入 slides_plan（role=backup），放映可跳过但追问时可翻出。
- 口径一致性：answer_key 中的数字/结论必须与对应页面及源材料一致（Step 6 一并校验）。
- 验收断言：qa_pack ≥3 条；每条 slide_ref 指向真实页。

### Step 5 构建 pptx（产出 output/deck.pptx）
```bash
python3 scripts/plan_to_pptx.py work/slides_plan.json output/deck.pptx [template.pptx]
```
- 备注自动含 [主张][证据]溯源尾部；模板样式继承不覆盖。
- 验收断言：脚本 ok=true；slide_count == 计划页数（含备用页）。

### Step 6 校验（产出 work/lint_report.json + output/deck.pdf）
```bash
python3 scripts/evidence_lint.py output/result.json <source_plain.txt>   # 数字保真+溯源
python3 scripts/export_check.py output/deck.pptx output/deck.pdf          # 导出一致
python3 scripts/qa_check.py work/qa_pack.json work/slides_plan.json       # 问答引用闭合
```
- qa_check 校验 slide_ref/backup_slide 均指向真实页；answer_key 数字见于源材料。
- FAIL 逐条修复重跑；status=ok 不允许带 FAIL。

## 4. 输出契约（result.json）

| 字段 | 要求 |
|---|---|
| case_id | 原样保留 |
| status | ok/partial/failed |
| deliverables | {source_pptx, exported_pdf} |
| slides[] | 逐页 {idx, role, title, claim, evidence_strength, bullets, notes, figure, evidence} |
| talk_brief | {goal, checks[], audience{prior_knowledge,concerns,expected_questions}, page_budget} |
| qa_pack[] | {question, slide_ref, answer_key[], backup_slide} |
| coverage | mainline/page_structure/figure_refs/narration/template/export 六要素 |
| version_log[] / uncertainty[] / gaps[] / sources[] | 如实记录 |

示例（**示意输出，非正式案例结果**）：
```json
{"case_id": "<case.json>", "status": "ok",
 "deliverables": {"source_pptx": "deck.pptx", "exported_pdf": "deck.pdf"},
 "talk_brief": {"goal": "让评审认可结论与证据强度",
   "checks": ["主结果页 strength=strong 且附对照"], "page_budget": 12,
   "audience": {"prior_knowledge": "domain expert", "concerns": "baseline fairness",
                "expected_questions": ["对照设置", "样本量"]}},
 "slides": [{"idx": 5, "role": "result", "title": "主结果", "claim": "方法A优于基线",
   "evidence_strength": "strong", "bullets": ["92.3% vs 88.1%"], "notes": "强调对照公平性",
   "figure": {"ref": "Table 2", "action": "reuse"},
   "evidence": {"locator": "Section 4.2", "locator_type": "table", "quote": "accuracy 92.3%"}}],
 "qa_pack": [{"question": "样本量是否足够？", "slide_ref": 7,
   "answer_key": ["120 样本，局限页已说明"], "backup_slide": 91}],
 "coverage": {"mainline": "done", "page_structure": "done", "figure_refs": "done",
              "narration": "done", "template": "done", "export": "done"},
 "version_log": [], "uncertainty": [], "gaps": [], "sources": ["paper.pdf"]}
```

## 5. 数字门槛

| 门槛 | 通过线 |
|---|---|
| 页级溯源 | 100% 页有 evidence.locator+quote |
| 证据强度标注 | 100% 页有 evidence_strength；weak 不用确定措辞 |
| qa_pack | ≥3 条且引用 100% 闭合 |
| 数字保真 | 页面/answer_key 数字 100% 见于源材料 |
| 时长适配 | 页数 ≤ page_budget（分钟×1.2） |
| 导出一致 | PDF 页数 == pptx 页数（含备用页） |

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 目标/听众未明示 | 按材料类型推断默认值，uncertainty 记录依据 |
| 论文缺图 | figure.action=omit，notes 说明 |
| 图表分辨率不足 | action=reuse + notes 注明"原图引用，未重绘" |
| 公式/符号丢失 | 引用编号不复现推导，uncertainty 记录 |
| 模板与内容冲突 | 占位符适配内容优先级：主张>要点>图示，version_log 记录 |
| 字体缺失/导出失败 | 主题字体替代或标 partial |
| 超时（预算紧张） | 保 slides_plan+result.json 最小交付，砍备用页 |

## 7. 自查清单

- [ ] case_id 一致；output_contract 全字段落实
- [ ] talk_brief 三段式齐备；goal 有可检查项
- [ ] 每页论断有源材料位置；evidence_strength 与措辞匹配
- [ ] qa_pack ≥3 且引用闭合、口径一致
- [ ] evidence_lint / export_check / qa_check exit 0（或如实 partial）
- [ ] pptx 可打开可编辑；PDF 页数一致

## 8. 效率约束（64 请求 / 900 秒）

- brief+画像 ≤4、页规划 ≤10、qa_pack ≤5、构建导出 ≤6、校验修复 ≤8。
- 产物固定三件套 + talk_brief/qa_pack 两个中间件；先落盘最小 result.json。

## 9. 最小示例（示意，非正式结果）

```bash
python3 scripts/qa_check.py work/qa_pack.json work/slides_plan.json
# → {"ok": true, "n_qa": 3, "unresolved_refs": []}
python3 scripts/export_check.py output/deck.pptx output/deck.pdf
# → {"ok": true, "slide_count": 12, "pdf_pages": 12, ...}
```
scripts/ 共 6 个脚本真实可运行（依赖 python-pptx≥0.6；pypdf 可选）。
