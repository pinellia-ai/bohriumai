---
name: topic-selection-evaluator
description: |
  科研选题与创新性评估 Skill。一体四面：问题可检验表述 → 别人做到哪（现状盘点）→
  增量在哪（与最近工作的差异定位）→ 现有条件能否做成（可行性对照）。四面互证，每面
  带文献/材料证据与定位；创新性分级（增量式/组合式/全新式）不空喊"首次"。
---

# Topic Selection Evaluator — 科研选题与创新性评估 Skill

## 1. 用途与适用范围

立项/投稿/申报前的四连问：① 问题怎么表述才可检验；② 别人做到哪；③ 我的增量在哪；④ 现有条件能不能做成。四面互证——任何一面含糊即指出并给补强建议。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、候选选题描述、文献/材料、可用条件（数据/设备/人员）。
2. 建立现状盘点基准：文献集合的方法/结果/局限字段表。

## 3. 工作流程

### Step 1 问题可检验化（四面之一）
- 选题表述 → 可检验命题：`{自变量, 因变量/指标, 对照/比较基准, 判定标准}`。
- 不可检验表述（"探索 X 的应用"）→ 改写建议 + 原表述问题说明。

### Step 2 现状盘点（四面之二）
- 已做到哪：按最近工作列 `谁+做了什么+到什么程度+局限`（逐条文献定位）。
- 与选题直接相关的**最近邻工作**重点标出——创新性对照对象。

### Step 3 增量定位（四面之三）
- 选题 vs 最近邻工作：差异逐项（对象/方法/条件/指标）。
- 创新性分级：`incremental（增量改进）| combinatorial（组合迁移）| novel（全新问题/方法）`——分级依据=差异项数量与性质；禁用"首次/领先"空词。

### Step 4 可行性对照（四面之四）
- 需要什么（数据规模/设备/方法/人时）vs 有什么（清单）→ 逐项匹配；缺口=风险项，给补齐路径或降级建议。

### Step 5 综合裁定
- 四面互证：问题清晰但增量弱 → 建议聚焦差异；增量强但条件缺 → 缓做建议。输出分级建议（建议立项/需补强/不建议）+ 依据。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "topic_selection_evaluation",
  "status": "success | partial | failed",
  "testable_form": {"statement":"可检验命题","variables":{"iv":"...","dv":"..."},"baseline":"...","criteria":"..."},
  "state_of_art": [{"paper":"...","did":"...","extent":"...","limitation":"...","locator":"..."}],
  "nearest_neighbors": [{"paper":"...","overlap":"...","diff":"..."}],
  "novelty": {"grade":"incremental | combinatorial | novel","diff_items":["对象不同：材料体系","条件不同：常温"],"banned_phrasing_removed":true},
  "feasibility": {"needs":{"data":"...","equipment":"..."},"have":{"..."},"gaps":[{"item":"缺少对照数据","mitigation":"与合作组共享"}]},
  "verdict": {"recommendation":"go | strengthen | pass","basis":"四面互证结论"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：testable_form 可判定；nearest_neighbors 明确（不挑软柿子）；novelty 分级有依据且无禁用词；feasibility 缺口有缓解路径；verdict 四面互证。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文献覆盖不足 | 现状盘点声明局限，结论降级 |
| 条件信息缺失 | feasibility 该项标 unknown |
| 预算不足 | 可检验化+增量定位优先 |

## 6. 自查清单

1. [ ] 命题可检验（变量/基准/标准齐）？
2. [ ] 最近邻工作真实对照？
3. [ ] 创新性分级有依据、无空词？
4. [ ] 可行性缺口有缓解路径？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。可检验化+增量定位优先；可行性对照其次；裁定最后。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
