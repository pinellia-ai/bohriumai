---
name: literature-kg-builder
description: |
  文献知识图谱构建 Skill。从论文抽取实体（研究者/材料/方法/任务/指标/结论——论文真实
  出现的，不凭常识补全）与关系（类型/方向/适用条件与原文一致，共现与转述不当直接证据），
  别名归一（不重复节点不错误合并），每节点每边绑定来源（论文位置+原文片段），支持真实
  查询并可增量更新。输出图谱数据 + 查询示例。
---

# Literature KG Builder — 文献知识图谱 Skill

## 1. 用途与适用范围

四问：抽得准（实体来自论文原文）、连得对（关系与原文一致，共现≠因果）、对得齐（别名归一不错合）、查得到回得去（可查询+全绑定）。聚焦一个子场景（抽取/归一/绑定/查询），本 Skill 覆盖最小闭环。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、主题范围、论文材料（带定位）。
2. 建立实体类型体系：`{researcher | material | method | task | metric | finding}`——每类的判定规则（什么样的词算该类实体）。
3. 材料缺失登记；不引入论文外的"常识概念"。

## 3. 工作流程

### Step 1 实体抽取（抽得准）
- 每个实体：`{entity_id, name(原文原词), type, locator(论文位置), mention_count}`。
- 只收论文真实出现的对象；泛化改写（"该材料"→ 具体名）需引用可定位处。

### Step 2 关系抽取（连得对）
- 关系类型固定枚举：`uses | measures | improves | causes | compared_with | part_of | reports`（可按题目扩展）。
- 每条边：`{from, to, type, direction, condition(适用条件), evidence(原文短句), locator, certainty(direct | transcribed | inferred)}`。
- **共现不当因果**：同段出现≠有关系；综述转述标 transcribed；推断标 inferred+依据。

### Step 3 别名归一（对得齐）
- 同一对象多写法（缩写/大小写/全称）→ 归一主名，别名表登记；同名不同对象（如两个 "Adam"）→ 加限定后缀区分。
- 归一依据：论文内指代关系（"X (以下简称 Y)"）。

### Step 4 绑定与查询（查得到回得去）
- 节点/边全部绑定 locator+quote。
- 支持基本查询：按实体查邻居、按关系类型过滤、按条件筛选——附 2-3 个查询示例与预期结果。

### Step 5 增量更新设计
- 新论文加入：实体对齐现有图（别名表复用），新增节点/边带 paper 来源；冲突处理留痕。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "literature_kg",
  "status": "success | partial | failed",
  "entities": [{"entity_id":"e1","name":"GSDMD","type":"material","locator":{"paper":"pA","page":3},"aliases":["GSDMD full name"],"merge_log":null}],
  "edges": [{"from":"e1","to":"e2","type":"causes","direction":"e1→e2","condition":"in vitro",
             "evidence":"GSDMD cleavage triggers pyroptosis","locator":{"paper":"pA","page":5},
             "certainty":"direct"}],
  "alias_table": [{"canonical":"e1","aliases":["GSDMD","gasdermin D"],"basis":"论文内定义"}],
  "queries": [{"q":"GSDMD 的下游效应","result_refs":["e3"],"how":"edge filter type=causes from=e1"}],
  "update_protocol": {"new_paper_steps":"抽取→对齐别名表→增量入图→冲突留痕"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：实体有 locator；edges 每条有 evidence+certainty；别名表归一有依据；查询示例可复现；无常识补全实体。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 实体指代不明 | 保守不建边 + uncertainty |
| 跨论文同名冲突 | 加限定区分，合并留痕 |
| 预算不足 | 实体+核心关系先行，查询示例 partial |

## 6. 自查清单

1. [ ] 实体全部来自原文？类型判定有规则？
2. [ ] 关系方向/条件与原文一致？共现未当因果？
3. [ ] 别名归一不错合不重复？
4. [ ] 查询示例可复现？全图可回原文？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。实体类型体系先行；抽取批处理；别名表随抽随建；查询脚本化验证。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 三元组输出为 CSV（head,relation,tail,evidence,locator）；
2. 别名表独立交付并给合并依据；
3. 附 2 个查询示例及预期结果。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：triples.csv（head/relation/tail/evidence/locator）
2. alias_table.csv
3. 2个查询示例及结果计数。
