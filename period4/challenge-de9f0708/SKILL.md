---
name: compliance-checker
description: |
  学术规范与合规检查 Skill。逐条比对式检查：引用真实性与格式合规、方法/统计交代清楚、
  论证链成立、受限数据处理（人类数据/隐私）、图片与代码授权、目标期刊/会议投稿要求。
  反两个极端：不报泛泛提醒（每条具体到位置与条目），不大面积误报（风格差异/学科惯例/
  个人表述不判为不端）。无法确认标 needs_review。
---

# Compliance Checker — 学术规范与合规检查 Skill

## 1. 用途与适用范围

投稿/结题/答辩/发布前的规范清单检查：引用合规、方法统计透明度、论证链、受限数据、图片代码授权、投稿要求。原则：**每条问题具体到位置与条目**；风格/惯例差异不误报为不端。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、材料、目标期刊/会议要求（如有）、规范清单。
2. 建立检查项清单（题目给定项优先）：逐项定义"什么算违规、什么算惯例差异"。

## 3. 工作流程

### Step 1 逐项检查
- **引用合规**：逐条引用可追溯、格式与目标要求一致、无虚构（对照文献库）。
- **方法统计透明**：方法可复算要素齐（对照 methods 清单）、统计量报告齐。
- **受限数据**：涉及人类/隐私数据的声明（伦理批号/知情同意）有无；个人信息暴露点。
- **图片与代码授权**：图片来源标注、代码/数据可用性声明与许可。
- **投稿要求**：目标期刊/会议的格式必查项逐条核对（字数/图表数/声明字段）。

### Step 2 误报防线
- 每条问题必须引用具体位置与规则条目；风格差异/学科惯例（如不同领域的引用风格）→ 记入 notes 不计问题。
- 判"不端"级问题（抄袭/造假）需证据充分——证据不足一律 needs_review，不扣帽子。

### Step 3 输出
- 问题单：`{loc, 检查项, 规则依据, 问题, severity, 修复建议}`；合规项也简报（通过 N 项）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "compliance_check",
  "status": "success | partial | failed",
  "checklist_results": [
    {"item":"citation_integrity","result":"pass | issues","issues":[{"loc":"§2","rule":"目标要求R3","problem":"引用[9]不在文献库","severity":"major","fix":"补条目或删引用"}]}
  ],
  "restricted_data": {"human_data_declared":true,"ethics_statement":"有（§Methods）","pii_exposure":[]},
  "rights": {"images_licensed":true,"code_availability":"声明缺失","fix":"补充可用性声明"},
  "submission_requirements": {"venue":"...","checks":{"字数":"pass","声明字段":"缺ORCID","图表数":"pass"}},
  "style_notes": ["领域惯例差异（非问题）"],
  "needs_review": [{"item":"图片版权归属","reason":"材料内无授权信息"}],
  "stats": {"passed":9,"issues":4,"needs_review":2},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：checklist_results 逐项有结果；issues 每条有 loc+规则依据+severity；不端级判断证据充分否则 needs_review；style_notes 记录非问题差异。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 目标要求缺失 | 按通用学术规范检查 + 声明口径 |
| 授权信息缺失 | needs_review，不判违规 |
| 预算不足 | 引用合规+受限数据优先 |

## 6. 自查清单

1. [ ] 逐项检查、每条问题具体到位置与条目？
2. [ ] 误报防线（惯例差异不入问题单）？
3. [ ] 不端级判断证据充分？不足进 needs_review？
4. [ ] 投稿要求逐条核对？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。清单项批处理；引用核对脚本辅助；输出按 severity 排序。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
