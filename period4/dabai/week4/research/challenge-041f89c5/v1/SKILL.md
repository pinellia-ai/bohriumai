---
name: research-topic-novelty-assessor
description: |
  科研选题与创新性评估 Skill：把研究设想推进到可决策的评估结论，四项交付齐全且一致：可检验的问题定义、已有工作比较矩阵、
  逐条新颖性对照（与最近工作划清边界）、带前提与风险标注的可行性判断。方法主线：PICO 式问题结构化→比较矩阵（任务/方法/数据/
  评价/结论五维）→创新点四分类（方法/数据/场景迁移/结论修正）并逐条判定是否被覆盖→可行性前提逐条标注
  verified（材料可查）/assumption（无来源，显式假设）/unverifiable（查不到）。冲突证据登记不回避，不把"检索不到"说成"尚无人研究"。
---

# 科研选题与创新性评估（Define · Compare · Novelty · Feasibility）

## 1. 用途与适用范围

- **做**：立项/投稿/申报前的选题评估：问题定义、已有工作比较、创新点识别、可行性判断。验收三件事：问题拆成可检验表述；创新点与最近工作逐条划界；可行性每个前提有来源或标为假设。
- **不做**：完整综述写作、实验设计、经费文书。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、研究设想（可能含糊）、给定文献集/材料、评估口径、输出要求。
2. 读 task.md：新颖性对照的时间窗（如近 3 年）、比较对象范围。
3. 文献集缺失 → 只能基于 case 提供材料评估，其余标 unverifiable。

## 3. 工作流程（五步）

### Step 1 问题定义（产物 problem_definition.json）
把模糊设想拆成五要素：研究对象（population/target）、关键变量（intervention/变量）、比较基线（baseline）、预期结论（outcome claim）、可证伪条件（falsifier：什么结果出现即推翻）。
- 产出可检验的问题陈述（PICO 化）；写不清可证伪条件的设想 → 标 `not_testable` 并说明缺什么。

### Step 2 已有工作比较（产物 comparison_matrix.csv）
- 从给定文献集（case 材料）逐条提取：任务、方法、数据、评价方式、结论五维字段，每格带来源 locator。
- 相似度判定：与设想共享 ≥2 维 → 列入"真正相近工作"；仅场景相似 → 列"可迁移但非同类"，写明无法直接比较的原因（如数据不可得、任务定义不同）。

### Step 3 创新点识别（产物 novelty_check.json，核心）
- 每条创新陈述判定类型：`method / data / scenario_transfer / conclusion_revision`。
- **逐条对照**最近相近工作：`{claim, type, nearest_works: [{ref, locator, overlap}], verdict: covered(已被覆盖) | partially_covered(部分) | novel(给定材料范围内未见) | indeterminate}`。
- **禁语规则**：verdict 只允许"在给定材料范围内未见"，绝不允许"尚无人研究"；verdict=novel 必须附检索/核对记录（比较矩阵中哪些维度查过）。

### Step 4 可行性判断（产物 feasibility.json）
前提清单逐条核查：数据可得性、算力、实验条件、时间窗、人员能力。
- 每条前提：`{premise, status: verified|assumption|unverifiable, source: locator 或 "无来源-显式假设"}`。
- 可行结论带条件：`{verdict: feasible|conditional|infeasible, conditions: [...], failure_risks: [{risk, trigger, mitigation}]}`。
- 只给"技术路线可行"一句话 = 不合格；必须逐前提。

### Step 5 冲突与交付（→ /app/output/result.json）
- 冲突证据登记表：结论相反文献并列（ref+locator+结论），写明本次评估取信与理由。
- 汇总 result.json（§4），问题定义/比较/创新/可行性四项交叉一致（如 novelty=covered 的维度不得再作为可行性依据）。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "problem_definition": {"statement": "PICO 化陈述", "population": "...", "variables": "...", "baseline": "...",
                          "expected_claim": "...", "falsifier": "...", "not_testable": false},
  "comparison_matrix": [{"ref": "Smith 2023", "locator": "...", "task": "...", "method": "...", "data": "...",
                          "evaluation": "...", "conclusion": "...", "closeness": "nearest|transferable|not_comparable",
                          "not_comparable_reason": null}],
  "novelty": [{"claim": "创新陈述", "type": "method", "nearest_works": [{"ref": "...", "locator": "...", "overlap": "方法部分重叠"}],
                "verdict": "novel|covered|partially_covered|indeterminate", "checked_dims": ["task", "method"]}],
  "feasibility": {"premises": [{"premise": "数据可得", "status": "verified", "source": "data/raw.csv#L1"},
                                 {"premise": "GPU 8×A100", "status": "assumption", "source": null}],
                   "verdict": "conditional", "conditions": ["GPU 数量减半时训练时长×2"],
                   "failure_risks": [{"risk": "...", "trigger": "...", "mitigation": "..."}]},
  "conflicts": [{"topic": "...", "side_a": {"ref": "...", "locator": "...", "finding": "..."},
                  "side_b": {...}, "resolution": "取信理由"}],
  "uncertainty": ["novel 判定仅限给定材料范围，未含开放检索（如 case 未提供检索工具）"],
  "operation_evidence": {"files": ["comparison_matrix.csv", "novelty_check.json", "feasibility.json"], "rerun_cmd": "..."}
}
```

## 5. 数字门槛

- novelty 逐条对照率 100%：每条 claim 有 nearest_works（可为空但必须说明查了什么）。
- 可行性前提三分率 100%：无 verified 来源的前提必须标 assumption，不得混写。
- 比较矩阵来源率 100%：每格字段带 locator（材料内位置）或标 missing。
- "尚无人研究"类表述出现 = 0。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 检索为空/文献过少 | 明确"材料范围受限"，verdict 降 indeterminate |
| 证据冲突 | conflicts 表并列 + 取信理由 |
| 创新陈述含糊 | 拆成多条可判定的原子陈述再对照 |
| 接口异常/权限不足 | 记 failed 项，可用部分照常交付 |
| 设想不可证伪 | problem_definition.not_testable=true 并说明 |

## 7. 自查清单

- [ ] case_id 原样；四项交付齐全且交叉一致。
- [ ] 每条创新点有类型+对照+verdict+checked_dims。
- [ ] 可行性逐前提 verified/assumption/unverifiable。
- [ ] 冲突已登记；无"尚无人研究"表述。

## 8. 效率约束

比较矩阵从材料批量脚本化抽取（见 scripts/），模型请求用于相似度判定与创新点拆解，≤10 次。先落 problem_definition + novelty 最小版，再补全。

## 9. 最小示例（示意输出，非正式案例结果）

设想："用对比学习改进 X 任务的表征。"
novelty 条目示例：`{"claim": "对比损失用于 X", "type": "method", "nearest_works": [{"ref": "Chen 2023", "overlap": "已在相邻任务 Y 用过对比损失"}], "verdict": "partially_covered", "checked_dims": ["task", "method", "data"]}`
