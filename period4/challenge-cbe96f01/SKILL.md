---
name: citation-fact-verifier
description: |
  引用与事实核验 Skill。三件事：引用是否支持结论（supports/partial/related_only/
  contradicts）、事实来源是否可靠（与给定材料/文献库对照）、证据定位是否落到原文。
  每条核验给位置+依据；无法核验的如实标注（材料外事实不猜）。
---

# Citation & Fact Verifier — 引用与事实核验 Skill

## 1. 用途与适用范围

审查单式输出：每条核验 `{位置, 被核内容, 结论, 依据, 可信度}`。引用-结论匹配是核心（区分主题相关与真正支持）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、稿件、可对照材料（文献库/事实清单）。
2. 盘点可核验范围：材料内能核的（引用 vs 文献库、数值 vs 数据源）vs 材料外（标 unverifiable）。

## 3. 工作流程

### Step 1 引用-结论匹配
- 逐处引用：找被引文献的对应结论（材料内可及部分），比对稿件表述：
  `supports | partially_supports | related_only | contradicted | unverifiable`。
- 转引、跨页引用、摘要-正文不一致情形按规则处理（同 p3 证据核验规则）。

### Step 2 事实来源核验
- 数值/事实陈述与给定材料对照：一致/不一致/来源缺失。
- 来源可靠性：引用的来源本身是否在可信清单内（材料提供）。

### Step 3 定位核对
- 每条核验的证据定位回原文（文件/页/段）；定位失败的如实标注。

### Step 4 分级输出
- 类型分级：事实错误 / 证据不足 / 规范问题 / 建议；needs_review 单列（材料外、无法访问）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "citation_fact_verification",
  "status": "success | partial | failed",
  "citation_checks": [
    {"loc":"§2 para1","claim":"稿件论断","ref":"[4]","ref_claim":"文献实际表述","match":"supports | partially_supports | related_only | contradicted",
     "evidence":{"quote":"文献原文","locator":{"doc":"[4]","page":6}},"note":""}
  ],
  "fact_checks": [{"loc":"§3","fact":"X=42%","source_check":"与材料Table1一致 | 不一致(实际38%) | 来源缺失"}],
  "locator_audit": {"total":18,"located":16,"failed":[{"loc":"§5","reason":"被引文献全文不在材料内"}]},
  "needs_review": [{"item":"外部事实Y","reason":"材料外"}],
  "stats": {"supports":12,"partial":3,"related_only":2,"contradicted":1,"unverifiable":2},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：citation_checks 全覆盖稿件引用；match 分级严格（related_only 不冒充 supports）；needs_review 不猜；对账 stats 与明细一致。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 被引文献不可及 | unverifiable + 登记缺失 |
| 事实超出材料 | needs_review |
| 预算不足 | contradicted/related_only 疑似项优先复核 |

## 6. 自查清单

1. [ ] 引用逐条匹配分级？主题相关未冒充支持？
2. [ ] 事实与材料对照？来源可靠性检查？
3. [ | 定位核对覆盖？失败如实？
4. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。引用映射脚本化初筛；可疑项精核；输出按问题严重度排序。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
