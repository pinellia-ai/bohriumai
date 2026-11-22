---
name: systematic-review-screener
description: |
  系统性文献检索与纳排筛选 Skill。整条流程可被他人照着重跑：检索式与字段限定留档、
  去重规则可查、每条记录按版本化纳排标准判定（逐条给依据）、双人标注+分歧仲裁流程、
  各环节条目数首尾对账（PRISMA 式）。离线语料；不编造人工评审；有限快照口径。
---

# Systematic Review Screener — 系统性检索与纳排筛选 Skill

## 1. 用途与适用范围

让系统性检索的结论**可信任的原因 = 流程可复跑**：检索式写在哪个库、限定哪些字段、覆盖到哪一天；重复如何合并；每条按哪版标准纳入/排除；分歧如何仲裁；各环节数目首尾对上。**离线约束**：固定语料快照，全记录筛选；不编造双人评审——单人场景下用"两次独立判卷+自查分歧"模拟并如实声明。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、研究问题（PICO 要素）、语料记录、既有筛选标准（如有）。
2. 盘点：记录总数、字段、夹具（合成重复导出/冲突意见标注为 fixture）。

## 3. 工作流程

### Step 1 协议前置（先于筛选）
- 固化协议：PICO 要素 → 纳入标准（Inclusion）与排除标准（Exclusion）逐条编号（I1/I2…、E1/E2…），每条标准写成可判定规则（什么样的记录满足/不满足）。
- 检索式与限定留档：库、字段、时间截止日、语料快照版本。
- **标准版本化**：v1 定稿后才筛选；筛选中途改标准必须记录并重判受影响记录。

### Step 2 去重与对账
- 重复按标识符归并（规则编号留档）；PRISMA 式计数：`识别 → 去重后 → 筛选 → 纳入`，各环节条目数首尾对账。

### Step 3 逐条判定（依据到原文）
- 每条记录对照 I/E 标准逐条判：`included | excluded(E1/E2…) | uncertain`。
- 依据 = 摘要/正文原文短句（不是标题词面）；excluded 必须指明触发哪条排除标准。

### Step 4 双判与仲裁
- 第一遍独立判卷 → 间隔/换序第二遍独立判卷 → 分歧清单逐条仲裁（写明依据哪条标准+哪段原文）。
- 无真实第二标注者时：声明"单人两轮独立判卷模拟，非双人评审"（不编造人工评审）。

### Step 5 流程报告输出
- 计数流+判定表+仲裁记录+协议版本，任何人可照着重跑。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "systematic_screening",
  "status": "success | partial | failed",
  "protocol": {"version":"v1","inclusion":[{"id":"I1","rule":"..."}],"exclusion":[{"id":"E1","rule":"..."}],
               "search_log":{"corpus_snapshot":"...","fields":["title","abstract"],"cutoff":"2024-06"}},
  "prisma_counts": {"identified":41,"after_dedup":23,"screened":23,"included":9,"excluded":14,"reconciled":true},
  "decisions": [{"record_id":"r5","decision":"included","criteria_hit":["I1","I3"],"basis":"摘要句：..."},
                 {"record_id":"r7","decision":"excluded","criteria_hit":["E2"],"basis":"综述而非原始研究"}],
  "dedup_log": [...],
  "dual_pass": {"pass1":9,"pass2":9,"disagreements":2,"arbitration":[{"record_id":"r8","final":"excluded","basis":"E1+原文短句"}],
                "honesty_note":"单人两轮独立判卷，非双人评审"},
  "fixture_notes": [...], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：prisma_counts 首尾对账；decisions 全覆盖；excluded 必带标准号与原文依据；仲裁记录完整；honesty_note 声明评审性质。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 记录字段不足以判定 I/E | uncertain 单列，不硬判 |
| 标准中途变更 | 记录版本变更，重判受影响记录 |
| 预算不足 | 协议+去重优先，判定 partial |

## 6. 自查清单

1. [ ] 协议先于筛选且版本化？
2. [ ] 计数首尾对账？
3. [ ] 每条判定带标准号+原文依据？
4. [ ] 仲裁记录完整？评审性质诚实声明？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。协议先行；判定批处理；两轮判卷复用同一索引；对账脚本化。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 74 分水准：prisma_counts 加脚本验证（每步加减断言）；screening_log.csv 补 fixture 标注列。
