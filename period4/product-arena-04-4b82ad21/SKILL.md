---
name: intro-related-work-writer
description: |
  引言与相关工作写作 Skill。立得住（背景指向真实研究脉络与具体未解决问题，拒绝"近年来
  受到广泛关注"式空转铺垫）、分得清（相关工作按问题/方法/路线分组比较，准确转述结论/
  适用条件/局限，不逐篇拼接）、说得实（研究空白由已引文献支撑推导）、引得全（引用覆盖
  与贡献表述一致）。输出引言+相关工作稿与空白论证链。
---

# Intro & Related Work Writer — 引言与相关工作写作 Skill

## 1. 用途与适用范围

立得住、分得清、说得实、引得全。核心交付：有真实脉络的背景 + 分组比较的相关工作 + 由文献推导的研究空白 + 与工作匹配的贡献表述。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、领域材料/文献、本文工作要点、引用要求。
2. 从文献提炼**研究脉络**：谁做了什么→哪些问题已解决→哪些未解决（每条带出处）。
3. 文献不足处登记 gaps，不编造文献与结论。

## 3. 工作流程

### Step 1 背景脉络（立得住）
- 拒绝空转铺垫：每句背景绑定具体文献/事实，形成"已知→局限→问题"递进链。
- 背景深度服务后文：铺垫到"读者能理解本文要解决什么"即止。

### Step 2 相关工作分组（分得清）
- 按问题/方法/技术路线**分组比较**（不是逐篇摘要拼接）：每组内文献按方法异同对比。
- 每篇转述三要素：结论 + 适用条件 + 局限——准确转述，不改写结论强度。

### Step 3 空白论证（说得实）
- 研究空白 = 从已引文献的局限**推导**：`文献A止步于X（引）→ 文献B未覆盖Y（引）→ 因此 Z 未被解决（本文切入）`。
- 空白句每一步可回查文献；无文献支撑的空白不写。

### Step 4 贡献表述（引得全）
- 贡献与实际工作一致（不夸大）；贡献列表与正文结构呼应。
- 引用覆盖检查：脉络中提到的关键文献都已在正文/相关工作出现；无材料外文献。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "intro_related_work",
  "status": "success | partial | failed",
  "background_chain": [{"sentence":"...","evidence":"文献[2]结论/事实","locator":"[2] §3"}],
  "related_groups": [{"group":"方法组：X 类","papers":[{"ref":"[4]","conclusion":"...","conditions":"...","limitation":"..."}],
                      "comparison":"组内异同一句话"}],
  "gap_argument": [{"step":"文献A止步于X","evidence":"[4] §5 局限段"},{"step":"...","evidence":"..."}],
  "contributions": [{"text":"...","matches_actual_work":true,"backed_by":"正文§3"}],
  "coverage_check": {"key_refs_cited":true,"external_refs":0,"orphans":[]},
  "files": {"intro":"introduction.md","related":"related_work.md","editable":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：background_chain 每句有证据定位；related_groups 分组比较（非拼接）；gap_argument 逐步可回查；无材料外文献；贡献不夸大。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文献不足以支撑空白论证 | 如实声明材料局限，不硬造空白 |
| 组内文献少于 2 篇 | 如实小组并说明覆盖限制 |
| 预算不足 | 脉络+分组先行，空白论证其次 |

## 6. 自查清单

1. [ ] 背景无空转铺垫？每句有出处？
2. [ ] 相关工作分组比较、三要素转述准确？
3. [ ] 空白由文献推导可回查？
4. [ ] 贡献与实际工作一致？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。脉络提取先行；分组比较批量；空白链与贡献最后组装。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：事实底稿/配置/日志/文献是事实依据；不为行文顺畅补造数值或文献；不编造软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（稿件文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：事实、数字、引用保留来源或修改记录。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
