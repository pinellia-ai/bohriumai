---
name: conclusion-data-extractor
description: |
  文献结论与数据提取 Skill。把散落在正文/表格/图注的结论与数据按统一字段表还原为
  结构化结果：结论抽取区分明确结论/限制/推测（"可能""提示"不改写成确定事实）；条件
  抽取让每条数值带着成立条件；数值保留单位/误差/显著性；每个字段回原文定位，第二人可
  独立抽查，字段表与口径可复跑。
---

# Conclusion & Data Extractor — 文献结论与数据提取 Skill

## 1. 用途与适用范围

不是把论文压短，而是**按统一字段表还原**散落的结论与数据为可核对结构。五问：结论分级（明确/限制/推测）、条件绑定、数值保真（单位/误差/显著性）、证据定位（页/段/表行列/图注）、可复跑口径。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、论文材料、字段要求（如有指定字段表）。
2. 建立字段表：`{field_id, name, 定义, 取值规则, 单位规则, 证据粒度}`——先于抽取。
3. 材料缺失字段：登记 gaps；表格为扫描件 → OCR 尝试，失败登记。

## 3. 工作流程

### Step 1 结论抽取（分级不改写）
- 从摘要/结果/讨论抽取结论并分级：`explicit`（作者明确结论）/ `limitation`（作者自述限制）/ `speculative`（"可能/提示/有望"类推测表述）。
- **推测不得改写成确定事实**——保留原文限定词，speculative 结论的 claim_text 必须含原限定语。

### Step 2 条件抽取（数值不脱语境）
- 每个数值绑定成立条件：样本（n/人群/材料）、实验设置、数据来源、时间点、比较基线。
- 条件不明的数值标 condition_unknown，不默认填常见条件。

### Step 3 数值抽取（保真）
- 逐值保留：数值、单位、误差（±SD/SEM/CI 按原文）、显著性（p 值/标记）、范围值保留区间形式。
- 跨页表格、合并单元格：按单元格归属还原行列关系；"未报告"/"—"如实记录。

### Step 4 证据定位
- 每个字段回原文：`{page, section/paragraph, table_row_col, figure_note}`——粒度足以让第二人独立抽查。

### Step 5 复核与复跑
- 字段表+抽取规则分离存储；抽样自查（≥3 条回原文核对）；他人可按同一口径复跑。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "conclusion_data_extraction",
  "status": "success | partial | failed",
  "field_schema": [{"field_id":"f1","name":"主要结果数值","rule":"结果段/表格主指标","evidence_grain":"table_row_col"}],
  "conclusions": [{"claim_id":"c1","text":"保留原文限定语的结论","grade":"explicit | limitation | speculative",
                   "locator":{"page":5,"section":"Discussion para2"},"quote":"..."}],
  "data_points": [
    {"field_id":"f1","value":412,"unit":"MPa","error":{"type":"SD","value":12},"significance":"p<0.05",
     "conditions":{"n":12,"sample":"退火450°C试样","baseline":"未处理组"},
     "locator":{"table":"Table2","row":5,"col":2},"quote":"412 ± 12 MPa (n=12)"}
  ],
  "condition_unknown_count": 0,
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：conclusions 分级齐全且 speculative 保留限定词；data_points 每条带 conditions+locator+quote；数字与原文逐个回对（match=true 才定稿）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 表格跨页/合并单元格 | 按结构还原归属，失败登记 gaps |
| 数值正文与表格冲突 | 并列记录 + uncertainty，不择一 |
| 预算不足 | 字段表+主要数值先行（partial） |

## 6. 自查清单

1. [ ] 结论三级分级，推测未改成事实？
2. [ ] 每个数值带条件？条件不明的如实标？
3. [ ] 单位/误差/显著性保真？范围值未均值化？
4. [ ] 每字段定位可独立抽查？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。字段表先行；数值批量抽取脚本辅助；证据定位随抽随记。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
