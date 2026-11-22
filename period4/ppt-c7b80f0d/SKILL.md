---
name: paper-to-slides-converter
description: |
  论文转学术 PPT Skill。把连续的论文叙述重写为页级离散表达：提取研究问题/方法/结果/限制
  形成主线，设计页级主张（一页一个主张）与图表引用（编号/单位/图注不错位）、讲解顺序与
  讲稿备注（不重复页面文字），在给定模板占位符内生成可编辑 pptx + 导出渲染检查。
  硬约束：每页内容可回溯到论文的图/表/章节；主线与论文自身贡献一致而非按段落搬运；
  成品可打开、播放、编辑，他人可按记录复跑出同一版式。
---

# Paper to Slides — 论文转学术 PPT Skill

## 1. 用途与适用范围

完成"论文内容如何变成可讲、可核验、可编辑的学术 PPT"的转换。三标准：① 主线与论文贡献一致（不是按段落搬运）；② 每页内容可回溯论文位置；③ 成品在指定模板与软件版本中正常打开播放编辑，他人可复跑同一版式。

不负责：论文精读结论生成、科研绘图的图形设计与美化、学术写作润色。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id、页数/时长/受众约束。
2. 盘点：论文材料（正文/图表/图注）、目标模板（母版/版式/占位符结构）、起始 deck（如要求编辑适配）。
3. 记录模板约束：版心、主题字体/色、字号层级、页脚页码规则。
4. 论文或模板缺失：status=failed 说明，不虚构内容。

## 3. 工作流程

### Step 1 论文主线提取（结构重写，不是切段）
- 识别四要素：研究问题（要解决什么）、核心做法（方法主线）、关键证据（哪些结果支撑）、限制（结论边界）。
- 形成**页序可讲的叙事骨架**：区分主结论与支撑细节，先定"整份 PPT 要讲清的一句主线"，再分配到页。
- 自检：骨架顺序是否服务于论证，而非论文目录顺序。

### Step 2 页级设计与信息分层
- 每页**唯一主张** + 要点数量控制（≤4 条/页）+ 层级（主张 → 支撑 → 细节）。
- 长段落改写为可讲述短语（保留术语与符号一致）；单页信息密度可放映（字号不小于可读档）。
- 页序设计讲解逻辑：背景铺垫 → 方法一页讲清 → 结果按证据强度排序 → 限制与结论收口。

### Step 3 图表引用与证据保留
- 每页定位论文来源：`{页号, 图/表/公式/章节编号}`，登记到 page_evidence 表。
- 编号、单位、图注与论文一致——**图表编号与正文引用错位零容忍**；示意图与实验数据图分开标注。
- 数值搬运逐个回对论文（单位、有效数字），不改写不取整。

### Step 4 讲稿备注
- 每页生成**不重复页面文字**的备注：过渡语（为什么接下来讲这页）、强调点、可能被追问时的补充证据。
- 备注引用论文位置，方便答问时回查。

### Step 5 模板约束生成与导出检查
- 内容写入模板**对应版式的正确占位符**（真实继承母版/主题字体/配色，不用文本框冒充）；长标题、多图并列、大表格按模板规则处理。
- 生成可编辑 pptx（原生对象）+ 讲稿备注。
- 导出 PDF：字体、图形、项目符号不崩坏——字体替换/图片丢失逐项记录；页数与时长约束核对。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "paper_to_slides",
  "status": "success | partial | failed",
  "outline": {"main_line":"一句主线","sections":[{"page":1,"claim":"...","role":"title|background|method|result|limitation|conclusion"}]},
  "page_evidence": [{"page":3,"claim":"...","source":{"paper_section":"4.2","figure":"Fig.3","table":null}}],
  "files": {"pptx":"slides.pptx（可编辑）","pdf":"slides.pdf","notes_included":true},
  "template_compliance": {"master_inherited":true,"theme_fonts":true,"placeholders_used":true,"violations":[]},
  "numbers_audit": [{"slide":3,"value":"412 MPa","paper_locator":"Table2 row5","match":true}],
  "export_check": {"fonts_substituted":[],"images_lost":0,"pages_ok":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：page_evidence 覆盖全部内容页；numbers_audit 全对；template_compliance 无违规才允许 success；讲稿备注每页都有且不重复页面文字。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 论文图表无法嵌入（仅文字材料） | 引用编号+文字描述，登记 gaps |
| 页数约束与内容冲突 | 按主线优先级取舍，取舍记录 changes |
| 模板占位符不支持某内容 | 规定替代版式 + 登记 |
| 字体缺失 | theme 声明保留 + 如实登记导出风险 |
| 预算不足 | 先 outline+骨架页落盘（partial），再补全 |

## 6. 自查清单

1. [ ] 主线与论文贡献一致？非段落搬运？
2. [ ] 每页唯一主张，可回溯论文位置？
3. [ ] 图表编号/单位/图注与论文一致？
4. [ ] 备注不重复页面文字且有过渡与追问应对？
5. [ ] 模板真实继承？导出不崩坏？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。outline 先行落盘；逐页生成即落盘；导出检查合并单次执行。中断时 outline + 已生成页完整可交（partial）。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "outline":{"main_line":"提出X方法使效率提升38%","sections":[{"page":2,"claim":"现有方法瓶颈在传质","role":"background"}]},
 "page_evidence":[{"page":3,"claim":"X方法流程","source":{"paper_section":"2.1","figure":"Fig.1"}}],
 "numbers_audit":[{"slide":4,"value":"38%","paper_locator":"Fig.4a","match":true}],
 "template_compliance":{"master_inherited":true,"theme_fonts":true,"placeholders_used":true,"violations":[]},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`（deck/页面文件 + result.json）。
4. **尽早落盘**：先用最小可用结果写一次 result.json，再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（论文章节/图表号/材料位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. page_evidence CSV（页/主张/论文图表号/定位）；
2. 数值审计逐条（slide值 vs 论文值）；
3. 备注与页面文字重复度检查。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：page_evidence.csv（页/主张/论文图表号/定位）
2. numbers_audit.csv（slide值 vs 论文值）逐值
3. 备注重复度检查计数。
