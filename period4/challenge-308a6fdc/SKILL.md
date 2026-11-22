---
name: academic-paper-writer-faithful
description: |
  学术论文写作 Skill。依据给定事实底稿生成/改写论文稿件：材料索引先行（每条事实、数字、
  引用都有来源锚点）、结果段与图注与原始数据严格一致（不把趋势写成因果）、引用逐条核对
  （作者/年份/期刊/DOI 真实可查、引用与论断匹配）、章节按学科模板齐备（缺失显式标注）、
  成稿保留可编辑结构（Markdown/Word 可继续修改并逐条复核）。输出稿件 + 来源追踪表。
---

# Academic Paper Writer — 学术论文写作 Skill（事实一致优先）

## 1. 用途与适用范围

解决"模型自行补全"的写作顽疾：稿件中每个数值、单位、样本量、图注、结论都来自给定材料，每条引用真实且与论断匹配，章节按学科模板齐备，成稿可直接编辑复核。

适用：研究材料组织、实验结果与图表转写、参考文献与引用管理、章节结构组织、事实一致性检查。不适用：无事实底稿的自由创作（拒答并说明需要材料）。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点事实底稿：实验记录、数据表、图表、既有草稿、参考文献列表。逐文件登记路径与要点。
3. 识别写作任务约束：目标文体（期刊论文/学位论文章节）、受众、语言、格式与字数要求。
4. 建立**材料索引**：`[材料编号 → 内容摘要 → 可支撑正文哪部分]`；冗余、口径冲突、缺失在此步显式登记。
5. 无底稿或底稿与任务无关：status=failed 说明，不虚构。

## 3. 工作流程

### Step 1 材料索引（写得实的基础）
- 每条可用事实登记：`{fact_id, content, source_file, locator(表号/行/图号/页), reliability}`。
- 冲突处理：两份材料口径不一致时并列登记，正文采用处标注冲突并说明取舍依据。

### Step 2 结果与图注转写
- 数值：从数据表/图逐个读取，**数值、单位、有效数字、误差范围与原始数据严格一致**；转写后逐个回对。
- 趋势表述不越界：方向+幅度+显著性按数据写；不把相关写成因果、不把趋势写成结论。
- 图注：编号、内容、显著性标记与图面一致。

### Step 3 引用管理（引得对）
- 每条实质性论断配引用：引用必须真正支撑该论断（强度与范围匹配）。
- 核对著录信息：作者、年份、期刊、卷期、DOI 与给定参考文献列表逐项一致；列表里没有的文献**不得引入**。
- 识别过度引用（一句堆 5 条）、装饰性引用（与论断无关）——改为恰当引用或删除。

### Step 4 章节组织（全得起来）
- 按任务要求的学科模板组织：摘要/引言/方法/结果/讨论/结论/参考文献/数据可得性声明。
- 每个必需部分写完或显式标注 `[待补充：<原因>]`——不省略字段、不用泛话填充。

### Step 5 事实一致性自查（核得了）
成稿后跑一致性检查：
- 正文数值 ↔ 数据表/图；摘要结论 ↔ 结果正文；方法描述 ↔ 实际材料步骤。
- 输出待核清单与人工复核点（材料里没有但稿件需要的表述）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "academic_paper_writing",
  "status": "success | partial | failed",
  "manuscript": "manuscript.md（可编辑源文件，保留章节层级/图表编号/引用格式）",
  "source_map": [
    {"claim_id":"s1","text":"正文句子","sources":[{"fact_id":"f3","locator":"Table2 row5"}],
     "type":"reported | inferred","note":""}
  ],
  "citation_check": [{"ref_key":"[12]","claim":"s1","supports":true,"metadata_verified":true,"issue":null}],
  "missing_sections": [{"section":"Data availability","reason":"材料未提供数据集信息"}],
  "consistency_report": {"numeric_checks":[],"abstract_vs_results":[],"method_vs_materials":[]},
  "needs_human_review": [],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：稿件中每个数值都能沿 source_map 追到材料；无来源的论断标 inferred 或删除；不在稿件中引入材料外的文献或数据；manuscript.md 为可编辑 Markdown（层级、编号、引用完整）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 材料不足以支撑某章节 | 保留结构 + 标注待补充，不编造 |
| 两份材料冲突 | 并列登记，正文取其一并注明取舍 |
| 引用列表不含所需文献 | 该论断降级为未引用推断或标 needs_human_review |
| 字数/格式约束冲突 | 优先事实完整性，冲突登记 |
| 预算不足 | 先结果段与图注（最易核验），status=partial |

## 6. 自查清单

1. [ ] 每个数值/单位/样本量可回溯到材料？
2. [ ] 引用真实、匹配、著录准确？无材料外文献？
3. [ ] 模板必需字段齐备或显式标注？
4. [ ] 结果段无因果越界？
5. [ ] manuscript.md 可编辑、结构完整？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。材料索引一次建全；写作按章节推进，每章完成即落盘（增量保存）；一致性检查合并成单次脚本/单次核对。中断时保证已完成章节完整可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "source_map":[{"claim_id":"s1","text":"复合材料的拉伸强度达到412 MPa。",
   "sources":[{"fact_id":"f7","locator":"Table 2, row 5"}],"type":"reported","note":""}],
 "citation_check":[{"ref_key":"[3]","claim":"s2","supports":true,"metadata_verified":true,"issue":null}],
 "missing_sections":[{"section":"Data availability","reason":"材料未提供数据集链接"}],
 "consistency_report":{"numeric_checks":["摘要412 MPa 与 Table2 一致"],"abstract_vs_results":[],"method_vs_materials":[]},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
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
1. 交付量化对账：source_map.csv（claim/数值/来源文件/表行）逐值；consistency 脚本自动比对输出；缺失章节占位清单计数。
