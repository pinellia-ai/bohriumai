---
name: litbench-kit
description: |
  文献阅读 Benchmark 与评测工具 Skill。把一次评测失败改造成可复核的对照：定义题卡
  （任务/输入材料/参考答案/评分规则/难度/授权）、统一运行器（固定权限/提示/预算/输出格式）、
  评分表（0/1/2 逐题计分 + 判分依据 + 争议说明）、失败样例库与版本对比。输出原始结果、
  逐题得分与失败分析，每个分数可沿题目 ID 追溯到原始输出与运行配置。
---

# LitBench Kit — 文献阅读 Benchmark 与评测工具 Skill

## 1. 用途与适用范围

建设可运行、可复用、可版本化的文献阅读题集与评测工具，做到"判得动、跑得一致、查得回、改得动"。聚焦**题卡 + 评分表 + 统一运行器约定 + 失败分析**这一最小可用闭环。

边界约束（组织方修订）：
- 提供的来源材料是**段落/表格文本**，不是 PDF 像素级金标——题卡参考答案必须锚定到段落文本。
- 技术合成检查器的日志**不等于** DSH 分数或独立语义验证——报告里不得混称。
- 平台固定运行 3 个案例；本 Skill 在每个案例上执行评测构建/运行/评分流程并输出可复核产物。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder（如提供），记录 case_id。
2. 盘点来源材料：段落/表格文本、题目草稿、既有评测脚本或日志。逐文件记录路径与版本标识。
3. 若提供 checker 日志：仅作为"技术性检查通过/失败"参考，报告中标注 `[technical-check]`，不作为语义分。
4. 材料缺失：登记 gaps，status=partial，不虚构题目或参考答案。

## 3. 工作流程

### Step 1 题卡（判得动）
每个题目一张题卡，字段齐备：
`item_id, task_type（抽取/问答/判断/排序/比较）, input_ref（来源段落ID）, question, reference_answer（含定位：段落+句子）, scoring_rule（0/1/2 明确分档标准）, difficulty, license/source（数据授权）`。
- 参考答案必须能在给定段落文本中逐字或逻辑定位；定位不了的题**不收**（判不动的题宁可不出）。
- 评分规则写成第三方可执行：0/1/2 每档给"什么样的输出得这个分"的正例与反例描述。

### Step 2 统一运行器（跑得一致）
- 固定：工具权限、系统提示、资源预算、输出格式（JSON schema）。
- 被评对象输出归一到统一结果目录：`runs/<run_id>/<item_id>.json`，run_id 含配置哈希。
- 重复运行 ≥2 次，记录逐题分数波动；波动>0 的题在报告中解释（采样类 vs 判分边界类）。

### Step 3 评分表（查得回）
- 逐题 0/1/2 计分 + 判分依据（引用输出中的关键句）+ 争议说明（边界情况怎么裁）。
- 汇总：按题型/难度给出分数分布，不只报总分。
- 溯源链：`分数 → item_id → runs/<run_id>/<item_id>.json → 输入材料位置`，任何分数可回查。

### Step 4 失败分析（改得动）
- 每个失败题归到具体题型与失败模式（定位错/条件丢失/单位错/超范围推断），进失败样例库：`{item_id, 原始输出摘录, 错误类型, 根因, 建议专项题}`。
- 版本建议：把本次失败转化为下一版题集的专项题卡草稿（标注 draft），只列受影响题目，说明历史分数可比范围。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "benchmark_kit",
  "status": "success | partial | failed",
  "item_cards": [{"item_id":"litqa-001","task_type":"qa","input_ref":"para 12-14",
    "question":"...","reference_answer":"...","answer_location":{"paragraph":13,"sentence":2},
    "scoring_rule":{"2":"...","1":"...","0":"..."},"difficulty":"basic","license":"provided by organizer"}],
  "run_config": {"tools":"fixed","prompt_hash":"...","budget":"64 req/900s","schema":"v1"},
  "runs": [{"run_id":"r1","per_item":[{"item_id":"litqa-001","score":2,"evidence_quote":"...","controversy":null}]}],
  "score_summary": {"by_type":{"qa":{"mean":1.4,"dist":{"2":5,"1":3,"0":2}}},"fluctuation_notes":["..."]},
  "failure_cases": [{"item_id":"...","output_excerpt":"...","error_type":"unit_loss","root_cause":"...","followup_item_draft":"draft-001"}],
  "version_notes": {"comparable_history":"...","changed_items":["..."]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：每个分数有 evidence_quote 与溯源路径；checker 日志标注 [technical-check] 不冒充语义分；draft 题明确标 draft；不虚构运行分数——未运行的 run 输出 null 并注明。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 参考答案无法定位到段落 | 该题不入题集，登记 gaps |
| 判分争议 | controversy 字段记录双方理由，给保守分 |
| 输出不合 schema | 判 0 并记录 schema 违规点 |
| checker 日志与人工判分矛盾 | 两者并列展示，以人工判分为准，标注矛盾 |
| 预算不足 | 先题卡与评分表（静态可交），运行部分 partial |

## 6. 自查清单

1. [ ] 题卡六字段齐备，参考答案可定位？
2. [ ] 评分规则 0/1/2 三档有正反例描述，第三方可复判？
3. [ ] 分数可溯源（item → run 文件 → 输入）？
4. [ ] 波动与争议有记录？checker 与语义分未混淆？
5. [ ] 失败样例含根因与专项题草稿？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。题卡与评分表静态可先产出；运行器只做 1-2 次小规模试跑验证判分一致性；失败分析优先覆盖 0 分题。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"partial",
 "item_cards":[{"item_id":"litqa-001","task_type":"qa","input_ref":"para 5",
   "question":"催化剂用量是多少？","reference_answer":"5 mg","answer_location":{"paragraph":5,"sentence":1},
   "scoring_rule":{"2":"数值+单位都对","1":"数值对单位错","0":"错误或未答"},"difficulty":"basic","license":"organizer"}],
 "runs":[],"score_summary":{},"failure_cases":[],
 "version_notes":{"comparable_history":"首版","changed_items":[]},
 "gaps":["运行器试跑未完成——预算"],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。
