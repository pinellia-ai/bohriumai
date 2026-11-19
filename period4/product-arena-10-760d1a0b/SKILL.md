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
