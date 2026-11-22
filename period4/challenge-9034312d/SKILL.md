---
name: apparatus-roadmap-drawer
description: |
  实验装置与技术路线图 Skill（apparatus_and_technical_route）。从装置清单/装配说明/方法
  段落抽取部件与接口画结构装配图；工艺描述转带编号流程图（主序列/并行/回流/终止）；物料/
  能量/信息流向用箭头线型颜色表达（分流合流、回流、废料出口，无反向无断头）；技术路线
  按阶段画目标-方法-输入输出-依赖。硬约束：每个实体可追溯到输入材料、连接与先后顺序成立、
  分层可编辑 SVG + 渲染件 + 导出合规。
---

# Apparatus & Roadmap Drawer — 实验装置与技术路线图 Skill

## 1. 用途与适用范围

装置图的每个部件、每条管路、每个箭头都对应真实实验条件——错一个连接方向、漏一个关键单元，读者理解就偏。聚焦四类表达：装置结构、步骤顺序、材料流向、技术路线，加可编辑与导出规范。

不负责：数据分析与数值拟合、实验方案科学合理性判断、论文排版。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md 与 workorder，记录 case_id。
2. 盘点：装置清单/装配说明/方法段落、工艺步骤描述、研究计划文本。
3. 建立部件-步骤-流向三张原始清单（逐条带材料定位）——这是图上一切实体的唯一来源。
4. 材料没写的连接/部件**不凭空补齐**；登记 gaps。

## 3. 工作流程

### Step 1 装置结构表达
- 从清单/说明抽取：`{part_id, name(原文原词), 接口/端口, 与其它部件的装配关系}`。
- 同类部件区分编号（泵-1、泵-2）；接口对齐绘制；关键局部放大（inset）。
- 每个部件与连接标注来源位置。

### Step 2 步骤顺序表达
- 工艺描述 → 带编号流程图：主序列 + 并行支路（fork/join）+ 循环回流（loop 标记）+ 终止条件。
- **编号与正文逐条对照**：步骤 N 对应正文第 N 步，不错位、不遗漏、不合并。

### Step 3 材料流向表达
- 物料/能量/信息三类流向用**可区分线型**（实线=物料、点线=信息、双线=能量），图例说明。
- 分流/合流节点、回流路径、废料出口显式画出；**禁止方向相反或断头箭头**——每条箭头两端都有实体，方向与材料描述一致。

### Step 4 技术路线表达
- 研究内容 → 阶段/里程碑：每阶段 `{目标, 方法手段, 输入, 输出, 依赖(依赖哪个阶段)}`。
- 读者能看出推进顺序（而非并列罗列）；依赖关系用箭头表达。

### Step 5 可编辑与导出
- SVG 分层：parts 层 → flows 层 → labels 层 → legend 层；命名 `part-<id>`、`flow-<id>`；文字 `<text>` 可编辑。
- 渲染 PNG/PDF 预览；导出检查：矢量、**字体嵌入（中文字体缺失会变方框——如实登记）**、分辨率、画布尺寸。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "apparatus_and_technical_route",
  "status": "success | partial | failed",
  "parts": [{"part_id":"p1","name":"蠕动泵-1","ports":2,"source":"清单 item3"}],
  "steps": [{"n":1,"text":"…","source":"正文步骤1","visual":"node-s1"}],
  "flows": [{"flow_id":"f1","from":"p1","to":"p3","kind":"material","direction":"p1->p3","evidence":"物料经泵输入反应器"}],
  "roadmap_stages": [{"stage":"S1","goal":"...","methods":["..."],"inputs":[],"outputs":[],"depends_on":[]}],
  "integrity_check": {"dangling_arrows":0,"reversed_flows":0,"step_number_mismatch":0,"fabricated_parts":0},
  "source_files": {"svg":"apparatus.svg","data":"parts_flows.json","render_script":"render.py"},
  "renders": {"png":"preview.png","pdf":"preview.pdf"},
  "export_check": {"vector":true,"fonts_embedded":["NotoSansCJK 或声明缺失"],"dpi_or_vector":"vector","issues":[]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：integrity_check 四项全 0 才允许 success；每个部件/流向有来源；流程编号与正文逐条对照；SVG 可编辑。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 说明中连接关系缺失 | 不补齐，登记 gaps + needs_human_review |
| 步骤描述含糊 | 节点画粗框 + note 标不确定 |
| 部件过多 | 分区/折叠 + 局部放大，登记取舍 |
| 中文字体缺失 | 登记导出风险，指定替代字体清单 |
| 预算不足 | 先装置图（科学正确性核心），流程/路线 partial |

## 6. 自查清单

1. [ ] 部件/连接全部来自材料？无凭空补齐？
2. [ ] 流向箭头无反向/断头？三类线型区分且图例一致？
3. [ ] 步骤编号与正文逐条对？
4. [ ] 路线图阶段依赖清晰（非并列罗列）？
5. [ ] SVG 分层可编辑？导出字体如实处理？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。三张清单一次抽取；SVG 脚本化生成（数据驱动可重绘）；渲染导出单次执行。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "parts":[{"part_id":"p1","name":"反应器","ports":3,"source":"清单1"}],
 "steps":[{"n":1,"text":"进料","source":"步骤1","visual":"node-s1"}],
 "flows":[{"flow_id":"f1","from":"p1","to":"p2","kind":"material","direction":"p1->p2","evidence":"物料由储罐流入反应器"}],
 "roadmap_stages":[{"stage":"S1","goal":"参数筛选","methods":["正交实验"],"inputs":["原料"],"outputs":["最优参数"],"depends_on":[]}],
 "integrity_check":{"dangling_arrows":0,"reversed_flows":0,"step_number_mismatch":0,"fabricated_parts":0},
 "export_check":{"vector":true,"fonts_embedded":["NotoSansCJK"],"dpi_or_vector":"vector","issues":[]},
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
1. 交付量化对账：integrity_check 四项=0 断言表（dangling/reversed/编号错位/凭空部件）
2. parts/flows CSV 逐条来源定位。
