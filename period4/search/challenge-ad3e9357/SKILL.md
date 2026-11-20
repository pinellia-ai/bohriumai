---
name: patent-tech-search
description: |
  专利与技术文献检索 Skill。一次检索回答五件事：保护什么（权利要求）、同族关系、法律
  有效性、同主题谁在做、访问与展示权限。多数据源字段口径不一致逐一处理；基于组织方快照
  语料（专利族数据+技术文献），不编造法律状态与全文。输出五问齐备的检索报告。
---

# Patent & Tech Literature Search — 专利与技术文献检索 Skill

## 1. 用途与适用范围

技术查新/专利研究五问：① 保护什么（权利要求解读）；② 同族关系（优先权链/成员）；③ 有效性状态（材料内数据）；④ 同一技术主题还有谁；⑤ 信息访问与展示权限。**离线约束**：组织方快照（专利族+技术文献+元数据响应）；**不编造法律状态、全文内容或实时有效性**。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、技术主题、专利/文献快照。
2. 盘点：专利记录（公开号/申请号/族成员/权利要求文本/法律状态字段如有）、技术文献记录、各源字段口径。
3. 权限信息（使用许可）如有：逐条登记。

## 3. 工作流程

### Step 1 技术主题界定
- 从检索需求提取技术要素（结构/方法/用途），形成主题要素表——查新比对的基准。

### Step 2 五问逐项处理
- **Q1 保护什么**：解读独立权利要求（材料内文本）→ 保护范围要点（技术特征分解），引用原文条号。
- **Q2 同族关系**：按族标识/优先权号归并成员，输出族谱（成员/国家/日期），依据=快照字段。
- **Q3 有效性**：只用快照内的法律状态字段，标注"截至快照日期"；材料无此字段 → 如实登记，不编造。
- **Q4 同主题玩家**：技术要素在快照内匹配其他专利与文献——每条给要素重合依据。
- **Q5 权限**：逐源登记许可状态；不明标 unknown。

### Step 3 字段口径与冲突
- 同一专利在不同源的字段差异（公开号格式/日期口径）并列处理；冲突不静默择一。

### Step 4 汇总输出
- 五问各有一节结论 + 依据定位；不可用实时核验处显式声明。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "patent_tech_search",
  "status": "success | partial | failed",
  "tech_elements": {"structure":["..."],"method":["..."],"use":["..."]},
  "q1_protection": [{"publication":"CN101X","claim_feature":["特征1","特征2"],"loc":"claims claim1"}],
  "q2_family": [{"family_id":"F1","members":[{"pub":"CN101X","country":"CN","date":"2020-01"}],"basis":"快照族字段"}],
  "q3_status": [{"pub":"CN101X","status_field":"有效（截至快照2024-06）","snapshot_only":true,"no_data":false}],
  "q4_landscape": [{"record_id":"p5","type":"patent | literature","overlap_elements":["特征1"],"basis":"摘要短句"}],
  "q5_rights": [{"source":"...","license":"登记值 | unknown"}],
  "field_conflicts": [{"pub":"CN101X","field":"admission_date","values":[...],"note":"口径差异"}],
  "gaps": [], "uncertainty_notes": ["有效性为快照时点状态，非实时"], "changes": []
}
```

硬性要求：五问各有结论或如实 no_data；q1 引权利要求条号；q3 带 snapshot_only 标记；q4 逐条要素重合依据；权限 unknown 不编造。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 权利要求文本缺失 | Q1 登记无法解读，不猜测保护范围 |
| 族字段缺失 | 按公开号前缀推断 + 标 inferred |
| 预算不足 | Q1/Q4（查新核心）优先 |

## 6. 自查清单

1. [ ] 五问齐备？no_data 如实？
2. [ ] 权利要求解读有条号定位？族关系有字段依据？
3. [ ] 法律状态标 snapshot_only？
4. [ ] 同主题匹配逐条有要素依据？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。技术要素表先行；族归并与要素匹配脚本化；五问并行填充。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **离线语料约束**：检索/筛选/覆盖率判定仅依据组织方提供的语料快照与导入状态——**不声称实时联网检索、全球覆盖或最新性；不编造文献记录、引用关系、全文内容、法律状态**。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（语料文件/记录ID/字段/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
