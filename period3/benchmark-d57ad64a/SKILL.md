---
name: writing-bench-kit
description: |
  学术写作 Benchmark 与评测工具 Skill。把一类真实写作工作拆成可判定题：题面带齐输入材料/
  指令/格式要求/必需要点，使两名评分员盲评能判出同一结论；参考答案覆盖合法变体并区分
  实质错误与风格差异；评分锚点写成可观察现象；双评+分歧裁定流程；固定输入与权限复现运行；
  报告逐题给得分/证据/失败类型/改进建议。输出题集 + 锚点表 + 运行与评分记录。
---

# Writing Bench Kit — 学术写作 Benchmark 与评测工具 Skill

## 1. 用途与适用范围

五个硬标准：题能判定、答案站得住、锚点打得齐、跑得可复现、报告说得清。聚焦**任务集设计 + 参考答案 + 评分锚点 + 双评流程**这一最小可用闭环，可聚焦单一写作任务类型（如结果段改写）。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点：写作任务样例、输入材料、既有评分尝试或失败记录。逐文件登记。
3. 从"一次真实评测失败"出发（若材料提供）：记录失败现象（判不了/分数对不上/结果找不回），改造为本次设计约束。
4. 材料缺失：登记 gaps，不虚构题目。

## 3. 工作流程

### Step 1 任务集设计（题能判定）
每道题的题面齐备：输入材料（完整、自包含）、任务指令（明确产物）、字数与引用要求、**必需要点清单**（缺哪条扣哪档）、可接受变体说明、完成判定标准。
- 判定性测试：两名评分员**不商量**盲评同一输出，能得出同一通过与不通过结论——题面信息不足的题先补题面再入库。

### Step 2 参考答案（答案站得住）
- 每题 1-2 份可接受答案，**覆盖合法写法变体**（语序、句式选择）。
- 显式区分：风格选择（可接受差异）vs 实质错误（事实错/要求缺失/引用错）——逐条列出，避免把唯一范文当唯一正解。

### Step 3 评分锚点（锚点打得齐）
把"准确、完整、可编辑、可复核"翻译成**可观察现象**：
- `fact-match`：稿件数值与输入材料逐个对得上（可数）；
- `coverage`：要求的小节/要点逐条在（可清单核对）；
- `editability`：保留层级/编号/引用格式，返修只需局部改动（可操作验证）；
- `traceability`：每条论断有出处（可抽查）。
锚点分歧集中处（试评后）修订锚点而不是改分数。

### Step 4 标注一致性与运行复现（跑得可复现）
- 双评流程：评分员A、B 独立盲评 → 分歧裁定（记录分歧集中在哪几条判据）→ 据此修订锚点。
- 运行复现：固定输入、工具权限、资源预算；保留原始输出与评分记录；同批题重跑得可解释的一致结论，波动记录并解释。

### Step 5 评测报告（报告说得清）
逐题：得分、证据（引用输出原句）、失败类型（题面问题/答案问题/锚点问题/执行问题）、改进建议——读者能判断差距在哪个环节，而非只看总分。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "writing_benchmark_kit",
  "status": "success | partial | failed",
  "task_cards": [{"item_id":"wq-001","input_ref":"...","instruction":"...","requirements":{"length":"...","citations":"..."},
    "must_have_points":["..."],"acceptable_variants":["..."],"pass_criteria":"..."}],
  "reference_answers": [{"item_id":"wq-001","variant":"A","text_ref":"refA.md","style_notes":"..."},
                          {"item_id":"wq-001","variant":"B","text_ref":"refB.md","style_notes":"变体：语序不同"}],
  "anchor_table": [{"anchor":"fact-match","observable":"数值逐个与输入对上","score_2":"全部一致","score_1":"1处不一致","score_0":"2处以上"}],
  "annotation_runs": [{"rater":"A","per_item":[{"item_id":"wq-001","score":2,"evidence_quote":"..."}]},
                       {"rater":"B","per_item":[]}],
  "disagreement_log": [{"item_id":"wq-001","anchor_in_dispute":"coverage","resolution":"...","anchor_revised":true}],
  "reproducibility": {"config_hash":"...","rerun_delta":"...","fluctuation_notes":[]},
  "report": {"per_item":[{"item_id":"wq-001","score":2,"evidence":"...","failure_type":null,"suggestion":null}]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：题卡必需要点可数；参考答案≥1 且变体区分明确；锚点全部可观察；分歧记录驱动锚点修订；无真实运行时分数输出 null 并注明，不编造评分结果。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 题面信息不足无法判定 | 补题面；补不齐则不入库，登记 gaps |
| 双评缺失（单人场景） | 自评分+自核分两次独立进行，标注局限 |
| 锚点争议无法收敛 | 保守分 + controversy 记录 |
| 预算不足 | 先题卡与锚点表（静态核心），status=partial |

## 6. 自查清单

1. [ ] 每题题面带齐六要素，两名评分员可盲评一致？
2. [ ] 参考答案区分风格差异与实质错误？
3. [ ] 锚点全部是可观察现象？
4. [ ] 分歧被记录并驱动锚点修订（而非改分）？
5. [ ] 未编造运行/评分结果？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。题卡与锚点表静态先行；试评只做 1-2 题验证锚点收敛；报告最后生成。中断时题卡+锚点完整即 partial 可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"partial",
 "task_cards":[{"item_id":"wq-001","input_ref":"data.csv","instruction":"写结果段","requirements":{"length":"150字","citations":"无"},"must_have_points":["数值38%","SD说明","比较对象"],"acceptable_variants":["语序自由"],"pass_criteria":"三点齐且数值准确"}],
 "anchor_table":[{"anchor":"fact-match","observable":"数值与data.csv逐个对上","score_2":"全对","score_1":"1处偏差","score_0":"2处以上"}],
 "annotation_runs":[],"disagreement_log":[],"reproducibility":{"config_hash":"demo","rerun_delta":null,"fluctuation_notes":[]},
 "report":{"per_item":[]},"gaps":["试评未完成"],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
