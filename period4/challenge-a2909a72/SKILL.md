---
name: multi-round-literature-search
description: |
  学术文献检索 Skill。将研究问题拆解为多轮检索计划：子问题→查询式（含同义词/缩写/
  变体扩展）→执行→评估覆盖→收敛或补检。仅依据组织方提供的文献语料与元数据快照执行
  （无实时数据库），每条结果保留来源与相关性依据，重复文献按标识符去重，无结果/冲突/
  缺失元数据如实登记。输出 result.json（含 output_contract 全部字段）。
---

# Multi-round Literature Search — 学术文献检索 Skill

## 1. 用途与适用范围

把复杂科研问题变成"多轮、可收敛、可追溯"的检索流程：查询规划、关键词扩展、执行、去重与来源记录。**离线约束（组织方修订）**：语料为组织方提供的真实文献与元数据响应快照——**不声称实时联网检索、不声称全球覆盖、不编造全文/引用/收录状态**；语料即检索全集。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：**output_contract 全部字段**（result.json 逐字段落实）、case_id、研究问题、语料清单。
2. 盘点语料：`ls /input/`，统计文献记录数、元数据来源（Crossref/EuropePMC/出版商响应）、可用字段（标题/作者/年份/DOI/摘要/参考文献）。
3. 检查增量导入状态（如提供）：哪些记录属于哪一批快照。
4. 材料缺失：status=failed，不虚构记录。

## 3. 工作流程

### Step 1 问题拆解与查询规划（第一轮）
- 研究问题 → 子问题清单（对象/机制/方法/时间范围/证据要求），每个子问题独立可检索。
- 每个子问题生成查询式：核心词 + 同义词 + 缩写 + 变体；规划检索顺序（先核心后外围）。

### Step 2 执行检索（对语料）
- 在语料上逐查询匹配：标题/摘要/关键词字段优先，作者与年份作辅助过滤。
- 每轮记录：`{查询式, 匹配字段, 命中数, 命中记录ID}`——检索过程可复跑。

### Step 3 覆盖评估与收敛（多轮）
- 轮末评估：子问题覆盖情况、新命中占比。**新增命中趋零且子问题全部覆盖 → 停止**（停止条件显式写出）。
- 补检策略：换字段、扩术语、放松时间窗——每轮补检必须带来新增命中，空转轮如实标注。

### Step 4 去重与来源记录
- 同一论文多标识符（DOI/PMID/标题变体）按标识符归并，保留主记录。
- 每条结果：`{record_id, title, 来源(语料文件+字段), 相关性依据(匹配了哪个子问题的哪些词), 引用原文短句}`。

### Step 5 汇总输出
- 无结果/冲突/缺失元数据如实登记（gaps）；不把"没找到"当"不相关"。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "literature_search",
  "status": "success | partial | failed",
  "query_plan": [{"round":1,"subquestion":"...","query":"...","fields":["title","abstract"],"hits":12}],
  "results": [{"record_id":"...","title":"...","match_subquestion":"...","relevance_basis":"匹配词+原文短句","source":{"corpus_file":"...","field":"title"},"dup_of":null}],
  "dedup_log": [{"kept":"r1","merged":["r7"],"key":"doi:10.xxxx/yyy"}],
  "coverage": {"subquestions_covered":3,"subquestions_total":4,"stop_reason":"新增命中趋零"},
  "gaps": [], "uncertainty_notes": ["离线语料检索，不代表全局覆盖"], "changes": []
}
```

硬性要求：query_plan 每轮可复跑；relevance_basis 引用语料原文；不编造语料外文献；coverage 不宣称全局。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 语料为空/损坏 | status=failed |
| 子问题无命中 | 如实登记 + 已尝试变体列表 |
| 元数据缺失（无摘要等） | 降级用标题匹配 + 登记 |
| 预算不足 | 已完成轮次结果落盘 partial |

## 6. 自查清单

1. [ ] 查询计划多轮且可复跑？停止条件显式？
2. [ ] 每条结果有来源与相关性依据？
3. [ ] 去重按标识符、log 完整？
4. [ ] 无实时检索/全球覆盖的虚假声明？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。语料索引进 /app/work 一次建立；匹配批处理；先落盘第一轮结果再迭代。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
