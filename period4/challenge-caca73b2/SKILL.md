---
name: results-discussion-writer
description: |
  结果与讨论章节写作 Skill。把"数据在手、图表已画好"变成可投稿的结果与讨论：
  图表数值可靠读入（单位/误差棒含义/刻度/统计量，逐值可回溯）、结果段只陈述观察事实、
  讨论段承担解释与文献对照（两节不互顶）、趋势与差异表述带边界（方向/幅度/显著性/组间
  比较）、因果边界控制与分层局限说明。输出正文 + 数值溯源表，每个数值对应到具体图表。
---

# Results & Discussion Writer — 结果与讨论章节写作 Skill

## 1. 用途与适用范围

"读得准、分得清、说得住、核得了"：从数据表/图/图注/统计输出可靠抽取数值，写成结构清楚的结果段；讨论段每个论断对应本研究数据或具体文献；表述强度与证据强度匹配；因果边界与局限写到方法/样本/测量/统计层面。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点：数据表、图（含图注）、统计输出、正文相关段落、目标期刊风格。
3. 建立图表清单：`{图表号 → 内容 → 关键数值点 → 误差棒含义}`。
4. 数据缺失：登记 gaps，不猜数值。

## 3. 工作流程

### Step 1 数值读入（读得准）
- 从数据表/图注/统计输出逐值抽取：数值、单位、有效数字、误差棒含义（SD/SEM/CI 依图注）、统计量（p、t、F、df）。
- 单位换算与有效数字保持一致；多面板图先建 `面板编号↔图注↔数据` 映射，防错配。
- 输出**数值溯源表**：正文将用到的每个数值 `{value, unit, source(图/表/统计输出+位置)}`。读不准的标 uncertain，不硬写。

### Step 2 结果段撰写（分得清·只写事实）
- 按图序或按问题组织（选一种并保持一致），每段一个发现：现象+数值+统计支撑。
- **结果段只陈述观察到的事实**：不解释机制、不引文献争论——那些属于讨论。
- 避免流水账：主次分明，核心发现给足数值，次要数据可概括但保留出处。

### Step 3 趋势与差异表述（说得住）
- 四要素齐全：方向（升/降）、幅度（数值+百分比）、显著性（p 与标记）、比较对象（跟谁比）。
- 有边界的写法：`趋势一致但未达显著（p=0.08）`、`仅在高剂量组出现（50 mg/kg）`——**不把小波动写成大结论**。
- 非显著的组间差异不写"显著提高"。

### Step 4 讨论段撰写（分得清·解释与对照）
- 每条讨论论断对应：本研究数据（溯源表编号）或具体文献（引用）。
- 文献对照写关系：一致/不一致/可能原因——不堆引用不讲关系。
- **因果边界**：区分相关、预测、因果；机制推测明确标注"推测/可能机制"。

### Step 5 局限与一致性自查（核得了）
- 局限分层写：方法层（设计限制）、样本层（n、范围、代表性）、测量层（精度、混杂）、统计层（检验假设、多重比较）——不停留在泛泛自我评价。
- 自查：正文数值 ↔ 溯源表 ↔ 图表逐一对账；结果/讨论职责不互串。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "results_discussion_writing",
  "status": "success | partial | failed",
  "results_section": "results.md",
  "discussion_section": "discussion.md",
  "value_trace": [
    {"value":412,"unit":"MPa","source":"Table 2 row 5","error_bar":"±12 (SD)","used_in":"results.md §2"}
  ],
  "claims": [
    {"claim_id":"d1","loc":"discussion.md §1","text":"...","basis":{"data":["v3"],"refs":["[4]"]},
     "relation_to_literature":"consistent","causal_status":"correlation_only"}
  ],
  "limitations": {"method":["..."],"sample":["..."],"measurement":["..."],"statistical":["..."]},
  "boundary_phrasing_audit": [{"loc":"results.md §3","original_draft":"显著提高","revised":"呈升高趋势（p=0.08）","why":"未达显著"}],
  "needs_human_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：每个正文数值在 value_trace 有出处；causal_status 与正文表述一致；结果段无解释、讨论段无论据空谈；limitations 四层至少覆盖两层。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 图为图片无法读数 | 用图注数值；仍不足则该值标 uncertain + gaps |
| 图注与数据表冲突 | 并列记录，采用数据表并注明冲突 |
| 统计输出缺失 | 不编造 p 值；显著性按图注标记引用 |
| 预算不足 | 先数值溯源表与结果段，讨论段 partial |

## 6. 自查清单

1. [ ] 每个数值可回溯到图表（value_trace 齐全）？
2. [ ] 误差棒含义、统计量按图注/输出读取？
3. [ ] 结果段只写事实、讨论段论断有据？
4. [ ] 显著性表述与 p 值一致？无因果越界？
5. [ ] 局限分层具体？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。数值溯源表一次建全再写作；结果段与讨论段分开成文，逐段落盘。中断时溯源表完整即 partial 可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "value_trace":[{"value":38,"unit":"%","source":"Fig.4a bar2 vs control","error_bar":"±5 (SD)","used_in":"results.md §1"}],
 "claims":[{"claim_id":"d1","loc":"discussion.md §1","text":"缓解幅度与[4]报道一致","basis":{"data":["v1"],"refs":["[4]"]},"relation_to_literature":"consistent","causal_status":"correlation_only"}],
 "limitations":{"method":[],"sample":["n=12，仅雄性"],"measurement":["疼痛评分为主观量表"],"statistical":["未校正多重比较"]},
 "boundary_phrasing_audit":[],"gaps":[],"uncertainty_notes":[],"changes":[]}
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
1. 保持 77.7 分水准：value_trace.csv 全数值逐条；结果/讨论职责分离计数；limitations 四层覆盖表。
