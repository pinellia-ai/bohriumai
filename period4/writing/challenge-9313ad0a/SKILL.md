---
name: mindmap-builder-traceable
description: |
  思维导图 Skill。从科研材料构建可编辑、可追溯的思维导图：识别核心概念/研究问题/方法/
  证据/结论（不把装饰词当节点）、合理根节点与层级粒度（分类不交叉、节点不重复）、显式
  关系标注（因果/依赖/对比/时间/引用/支持/冲突，无依据不连线）、关键节点挂证据
  （页码/段落，区分事实/概括/推断）、输出 Markdown 大纲 + Graphviz/Mermaid 源码
  （可编辑可渲染）。
---

# Mindmap Builder — 思维导图 Skill（证据可追溯）

## 1. 用途与适用范围

五个硬标准：抓得准、理得清、连得对、证据可追溯、实际有用。聚焦**论文/综述结构整理**主线：研究问题、方法、结果、局限与研究空白——每个关键节点可回溯原文。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id。
2. 盘点材料：论文/综述/纪要/计划文本，记录页码或段落编号体系。
3. 确定导图目的（论文梳理/方案规划/知识体系）——目的决定根节点。
4. 材料缺失：status=failed。

## 3. 工作流程

### Step 1 核心要素抽取（抓得准）
- 识别：核心概念、研究问题、方法、证据（数据/文献）、结论、局限、任务/待办。
- 过滤装饰性词语（背景性套话、重复修饰）不当节点。
- 每个候选节点登记：`{node, 原文位置, 类型(事实/概括/推断)}`。

### Step 2 层级组织（理得清）
- 根节点 = 导图目的（如"论文X的结构"）。
- 一级分支按功能域（问题/方法/结果/局限/空白），同级粒度一致（同为方法级或同为具体步骤级）。
- 规则：分类不交叉（一个节点只归一个父节点）、节点不重复（重复表述合并）、重要信息不埋没（深度≤4层，核心结论在前两层可见）。

### Step 3 关系标注（连得对）
- 显式关系类型：`因果 / 依赖 / 对比 / 时间 / 引用 / 支持 / 冲突`。
- **材料没有依据的关系不连线**；推断性关系标注 inferred 并给推断依据。
- 冲突关系（材料内部矛盾）用 conflict 边并列双方位置。

### Step 4 证据挂接（可追溯）
- 关键节点（结论/数据/主张）挂证据：页码/段落/引用；区分事实（原文可查）、概括（多出综合）、推断（标注依据）。
- 无证据的推断节点显式标记，不冒充原文结论。

### Step 5 可编辑交付（实际有用）
- 输出三种形态：
  1. Markdown 缩进大纲（任何编辑器可改）；
  2. Mermaid mindmap 源码（可渲染、可改）；
  3. result.json（结构化节点与关系）。
- 自查后交付。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "mindmap_building",
  "status": "success | partial | failed",
  "outline_md": "mindmap.md",
  "mermaid_src": "mindmap.mmd",
  "nodes": [
    {"id":"n1","parent":null,"text":"论文X结构","depth":0,"type":"root","node_kind":"fact","evidence":null},
    {"id":"n5","parent":"n2","text":"催化剂用量5 mg","depth":2,"type":"fact",
     "evidence":{"locator":{"page":4,"paragraph":2},"quote":"5 mg of catalyst was used"}}
  ],
  "edges": [{"from":"n5","to":"n8","type":"supports","note":"数据支持结论","basis":"para 4 -> para 9"}],
  "inferred_nodes": [{"id":"n12","basis":"由方法与结果对比推断","risk":"低"}],
  "coverage_check": {"research_question":true,"methods":true,"results":true,"limitations":true,"gaps_identified":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：edges 每条有 basis；inferred 节点不与 fact 混淆；outline_md 与 mermaid 与 nodes 三者一致；层级≤4、无交叉分类。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 材料无段落编号 | 用"页码+段落序"定位 |
| 关系依据不足 | 不连线，两节点并列在不同分支 |
| 材料过长 | 分域抽取后合并，gaps 记录未覆盖部分 |
| 预算不足 | 先大纲（功能域+核心节点），关系与证据 partial |

## 6. 自查清单

1. [ ] 装饰词未成节点？核心要素五类齐？
2. [ ] 同级粒度一致、无交叉分类、无重复节点、深度≤4？
3. [ ] 每条关系有依据？无依据不连线？
4. [ ] 关键节点证据可回溯？事实/概括/推断区分？
5. [ ] 三种输出形态一致？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。抽取与大纲一步完成（一次通读标记）；Mermaid 由大纲脚本化生成，不二次消耗。中断时大纲完整即 partial 可交。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "nodes":[{"id":"n1","parent":null,"text":"论文结构","depth":0,"type":"root","node_kind":"fact","evidence":null},
          {"id":"n5","parent":"n2","text":"产率提升至92%","depth":2,"type":"fact","node_kind":"fact",
           "evidence":{"locator":{"page":5,"paragraph":3},"quote":"yield reached 92%"}}],
 "edges":[{"from":"n5","to":"n8","type":"supports","note":"产率数据支持优化有效","basis":"p5->p8"}],
 "inferred_nodes":[],"coverage_check":{"research_question":true,"methods":true,"results":true,"limitations":true,"gaps_identified":true},
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
