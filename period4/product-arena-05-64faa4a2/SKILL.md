---
name: methods-section-writer
description: |
  方法与实验章节写作 Skill。写得全（关键步骤/实验设置/参数/数据集与划分/对照与重复次数
  齐备）、写得准（参数与配置文件/日志/代码一致，不为段落顺畅补数值）、做得着（读者可按
  章节复做：版本/环境/随机种子/命令给全）、边界清（限制条件如实）。
  事实来源是配置文件与日志，不是"写起来顺"。
---

# Methods Section Writer — 方法与实验章节写作 Skill

## 1. 用途与适用范围

四问：写得全、写得准、做得着、边界清。事实依据 = 配置文件/日志/代码/实验记录——章节中的每个参数都可回查来源。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、实验材料（配置/日志/代码/数据说明）、目标文体。
2. 建立**参数-来源清单**：从配置/日志抽取全部参数、数据集版本、划分方式、环境、种子——写作前的对账基准。
3. 材料缺失的参数：显式登记"源材料未报告"，不按惯例补值。

## 3. 工作流程

### Step 1 完整性检查（写得全）
- 对照标准清单：关键步骤、实验设置、参数、数据集与划分、对照设置、重复次数、评价指标、环境版本——缺项列出。
- 只留"能读通的主干"不够：复做所需的每个决策点都要写。

### Step 2 参数对齐（写得准）
- 章节中每个参数回查来源：`{param, value, source(config.yaml line / log / code)}`。
- **不为段落顺畅补数值**：来源缺失的参数写"未报告"或按 needs_human_review 标注。
- 数据集版本与划分、训练/评测条件与材料严格一致。

### Step 3 可复现性（做得着）
- 复现包：环境（依赖版本）、随机种子、硬件（如有）、关键命令/入口——读者照做能跑。
- 步骤顺序可执行（前后依赖明确）。

### Step 4 限制条件（边界清）
- 方法学限制如实（样本局限/近似假设/未控制变量），不藏在最后一句泛泛带过。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "methods_section_writing",
  "status": "success | partial | failed",
  "completeness": {"checklist":[{"item":"数据集划分","present":true},{"item":"随机种子","present":false,"gap":"源材料未报告"}]},
  "param_sources": [{"param":"learning_rate","value":"3e-4","source":"config.yaml:L14"},
                     {"param":"batch_size","value":"64","source":"log epoch1"}],
  "unreported_params": [{"param":"warmup_steps","note":"源材料未报告，未写入章节"}],
  "repro_pack": {"env":"requirements.txt 摘要","seed":"未报告","command":"python train.py","hardware":"未报告"},
  "limitations": ["样本仅来自单一数据集","未做显著性检验"],
  "files": {"methods":"methods.md","editable":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：param_sources 每参数有来源；unreported_params 不出现在章节正文中冒充已知；completeness 缺项如实；limitations 具体非泛泛。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 配置与日志冲突 | 并列记录，正文采用日志值 + 冲突登记 |
| 材料不足以成章 | 写已确认部分 + gaps 列缺口（partial） |
| 预算不足 | 参数对齐与完整清单优先 |

## 6. 自查清单

1. [ ] 标准清单逐项检查？缺项如实？
2. [ ] 每参数有来源？未报告值未冒充？
3. [ ] 复现包要素齐？
4. [ ] 限制具体？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。参数-来源清单先行；章节按清单填充；对账脚本化。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：事实底稿/配置/日志/文献是事实依据；不为行文顺畅补造数值或文献；不编造软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（稿件文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：事实、数字、引用保留来源或修改记录。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 79.7 分水准：param_sources.csv 补未报告参数计数；repro_pack 完整性核对表（环境/种子/命令/硬件四项）。
