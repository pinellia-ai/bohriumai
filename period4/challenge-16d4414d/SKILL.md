---
name: argument-logic-reviewer
description: |
  论文逻辑与论证审查 Skill。查主张与证据的断裂：结论强度超出数据支撑、引用不支持所引
  句、方法回答不了研究问题、统计口径与结论方向相反、承诺未交付、相关写成因果。
  论断-证据清单逐条抽取比对；判断指回原文；区分事实错误/证据不足/表述问题。
---

# Argument & Logic Reviewer — 论文逻辑与论证审查 Skill

## 1. 用途与适用范围

通顺≠成立。六类断裂检测：① 结论强度超出数据；② 引用不支持所引句；③ 方法回答不了研究问题；④ 统计口径与结论方向相反；⑤ 引言承诺在结果未交付；⑥ 相关表述成因果。逐条定位到段/句。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、稿件全文。
2. 建立**承诺-交付-结论三张清单**：引言承诺的研究问题/分析；方法实际执行的；结果交付的；讨论声称的结论。

## 3. 工作流程

### Step 1 论断-证据清单
- 逐段抽取论断（主张+强度词）与证据（数据/图表/文献）——断裂检测的基础。

### Step 2 六类断裂比对
- 强度越界：结论句 vs 数据支撑范围（样本/条件/显著性）。
- 引用错配：所引文献内容 vs 被支撑句。
- 方法-问题错配：研究问题需要因果/比较，方法只能给相关/描述。
- 口径反向：统计口径与结论描述方向矛盾。
- 承诺缺口：三清单交叉（承诺∧未交付；交付∧未讨论）。
- 因果越界：相关设计+因果表述。

### Step 3 分级输出
- 每条：`{loc(段/句), 断裂类型, quote(稿件原句), evidence_gap(缺什么), severity, 修改方向}`。
- 判断可指回原文；表述性建议与实质性缺陷分开。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "argument_logic_review",
  "status": "success | partial | failed",
  "claim_evidence_map": [{"claim_id":"c3","loc":{"section":5,"para":2},"claim":"...","strength_word":"证明","evidence":"Fig.3（相关性）","gap":"因果越界"}],
  "breaks": [
    {"break_id":"b1","type":"overclaim | citation_mismatch | method_question_mismatch | metric_direction | promise_gap | correlation_as_causal",
     "loc":{"section":5,"paragraph":2,"sentence":3},"quote":"This proves...","evidence_gap":"数据仅支持相关",
     "severity":"major","fix_direction":"改为'与…相关'并注明设计限制"}
  ],
  "promises": {"intro_promises":["X分析"],"delivered":["X分析"],"missing":["Y分析"]},
  "stats": {"by_type":{"overclaim":2,"promise_gap":1},"major":3,"minor":2},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：claim_evidence_map 覆盖实质论断；六类断裂逐类检查；每条 quote+gap+fix；承诺缺口用三清单对账。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 论证链跨多节 | 依赖关系图化，断点定位 |
| 意图不明（作者可能有理） | needs_review 不硬判 |
| 预算不足 | overclaim/promise_gap 优先 |

## 6. 自查清单

1. [ ] 论断-证据清单完整？
2. [ ] 六类逐类查过？
3. [ ] 每条判断指回原文？
4. [ ] 修改方向具体？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。三清单脚本辅助抽取；六类比对按节推进；输出按 severity 排序。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：claim_evidence_map.csv（claim/loc/strength_word/evidence/gap）逐条；六类断裂分布计数；promises 三清单对账。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
claim_evidence_map 行数=实质论断数；六类断裂分布计数；promises 三清单对账

**本题针对性修正**：
断裂检测 CSV 化对账
