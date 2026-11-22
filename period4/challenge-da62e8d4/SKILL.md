---
name: reproduction-checklist-report
description: |
  论文复现与方法验证 Skill。围绕一篇有公开材料的真实论文，产出可核验的复现工作流：
  复现清单（材料/代码/数据/参数/依赖/许可证定位到版本，缺失显式登记）、参数复原表
  （区分论文明确给出/代码推断/自行设定三类）、结果对比表（事先声明容差）、差异归因条目
  （环境/数据/实现/论文描述不足）与分级复现结论（可复现/部分复现/不可复现）。
---

# Reproduction Checklist & Report — 论文复现与方法验证 Skill

## 1. 用途与适用范围

把"结果对不上"变成可核验的归因条目，把复现做成"找得齐、跑得对、对得上、讲得清"的流程。聚焦**复现清单 + 参数复原 + 结果对比表 + 归因报告**主线；论文正文、附录与仓库中的材料是唯一事实依据。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点材料类型：论文 PDF/文本、补充材料、代码仓库快照、训练日志、数据文件、README、requirements/environment 文件。
3. 建立来源清单：每个文件记录路径、版本（git commit / 文件哈希 / 版本号）、许可证。
4. **缺失显式登记**：论文声明的代码/数据/依赖找不到时进 `gaps`（missing_registered），不默默跳过。
5. 不实际联网拉取仓库；仓库材料以平台提供的快照为准。

## 3. 工作流程

### Step 1 复现清单（找得齐）
从论文正文 + 附录 + 仓库三处交叉抽取必需材料，形成可勾选清单：

| 项 | 来源位置 | 版本 | 状态 |
|---|---|---|---|
| 代码仓库 | 正文§4 / footnote | commit abc123 | ✓/✗ missing_registered |
| 训练数据 | 附录B | v2 | ... |
| 关键依赖 | requirements.txt | torch==1.13 | ... |
| 超参数 | 附录C Table C1 | - | ... |

每项标注来源（正文页码/附录节/仓库路径）；冲突时三处并列。

### Step 2 参数复原（跑得对）
参数三方核对：**论文正文 vs 附录表格 vs 代码默认值**，逐参数给出取值与依据，分三类：
- `paper_stated`：论文明确给出（引位置）
- `code_inferred`：从代码/配置推断（引文件与行）
- `self_set`：论文与代码都没给、自行设定（写理由，标高风险）
正文与代码默认值冲突时不静默任选——并列记录并按"论文优先"给出建议值 + 冲突登记。输出可执行参数表（config 草案），不用仓库默认值随手跑。

### Step 3 结果对比（对得上）
- 对齐论文关键指标表：指标名、论文值、复现值、绝对/相对偏差。
- **事先声明容差**（依指标性质：如准确率 ±0.5pp、损失 ±5%、曲线形状一致），写明比较口径（同一测试集？同一指标定义？宏平均还是微平均？）与统计方式（单次 run 的波动说明）。
- 区分数值波动（随机种子、采样）与方法性差异（实现不同、数据版本不同）。

### Step 4 差异归因（讲得清）
"结果对不上"拆成可核验归因条目，每条：
`{现象, 涉及指标, 假设原因(环境/数据/实现/论文描述不足), 验证方法, 验证结果, 置信度}`。
归因必须有验证动作（如换种子重跑、对齐数据版本再跑），不允许"可能是随机性"一笔带过。不实际执行长训练时，明确标注"静态分析结论，未运行验证"。

### Step 5 分级结论与报告
- `reproducible` / `partially_reproducible` / `not_reproducible`，给出依据与边界。
- 全流程记录：输入版本、环境快照要点、每步产物路径——他人可按记录独立复核。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "reproduction_verification",
  "status": "success | partial | failed",
  "paper": {"title":"...","venue_year":"...","declared_artifacts":["code","data","weights"]},
  "checklist": [{"item":"code","source":"p.7 footnote","version":"abc123","status":"available | missing_registered","license":"MIT"}],
  "environment": {"declared":"...","observed_from_repo":"...","mismatches":["..."]},
  "parameters": [
    {"name":"learning_rate","value":"3e-4","basis":"paper_stated | code_inferred | self_set",
     "source":{"page":8,"table":"C1"},"conflict_with_repo":"repo default 1e-3","decision":"paper priority"}
  ],
  "comparison": [
    {"metric":"accuracy","paper_value":92.1,"reproduced_value":null,"abs_dev":null,"within_tolerance":null,
     "tolerance_declared":"±0.5pp","note":"未运行，仅静态对齐"}
  ],
  "attribution": [{"phenomenon":"...","hypothesis":"data version mismatch","verification":"compare dataset hash","result":"...","confidence":"medium"}],
  "verdict": {"level":"reproducible | partially_reproducible | not_reproducible | not_run_static_only",
              "basis":"..."},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：未实际运行的指标 reproduced_value=null 并注明，**禁止编造复现数值**；缺失材料全部登记；参数三类依据逐条可查。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 仓库快照缺失 | checklist 登记 missing，参数按论文复原，verdict 降级并说明 |
| 论文与代码参数冲突 | 并列记录 + paper 优先建议 + 冲突登记 |
| 无法运行代码（环境不可用） | 静态复现（清单/参数/口径对齐），verdict=not_run_static_only |
| 日志与论文表格口径不一 | 先统一口径再比较，注明换算 |
| 预算不足 | 优先参数复原表与对比表骨架，status=partial |

## 6. 自查清单

1. [ ] 论文声明的材料逐项定位到版本？缺失项显式登记？
2. [ ] 每个关键参数有三类依据之一，冲突未静默？
3. [ ] 容差与比较口径事先声明？
4. [ ] 无编造的复现数值？未运行的如实标注？
5. [ ] 归因条目含验证方法与结果？
6. [ ] verdict 有分级依据？result.json 可解析？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。三处来源（正文/附录/仓库）并行盘点；参数表先骨架后补依据；静态分析优先，运行验证按预算裁剪。中断时输出 partial + 已完成部分。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"partial",
 "checklist":[{"item":"code","source":"p.7","version":"v1.2 (commit abc)","status":"available","license":"MIT"},
              {"item":"pretrained weights","source":"附录B","version":null,"status":"missing_registered"}],
 "parameters":[{"name":"batch_size","value":"64","basis":"paper_stated","source":{"page":8,"table":"C1"},"conflict_with_repo":"default 32","decision":"paper priority"}],
 "comparison":[{"metric":"F1","paper_value":0.842,"reproduced_value":null,"abs_dev":null,"within_tolerance":null,"tolerance_declared":"±0.01","note":"未运行"}],
 "verdict":{"level":"not_run_static_only","basis":"环境不可用，完成清单与参数复原"},
 "gaps":["权重文件缺失"],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`，主输出为 /app/output/result.json（含 case.json 的 output_contract 全部字段）。
4. **尽早落盘**：先用最小可用结果写一次 /app/output/result.json（含 case.json 的 output_contract 全部字段），再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（页/段/句/表号/图号或文件位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md（使用与方法说明）；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：checklist.csv（项/来源/版本/状态）
2. parameters.csv（三类依据计数）
3. 未运行指标显式 null 计数。
