---
name: nanopub-assertion-builder
description: |
  Nanopublication Skill。把论文关键结论拆成原子断言（每条可独立判断真假），为每条断言
  绑定最小充分证据（原文位置可指认），构建 断言-证据-论文-作者-年份-版本 完整链路，
  输出可机器读取结构（nanopub 风格 JSON）。拆得细、对得上、追得回、读得懂。
---

# Nanopublication Builder — 断言拆分与证据绑定 Skill

## 1. 用途与适用范围

把"整段结论塞一个字段"变成**原子断言流**：每条断言独立可判真假、有最小充分证据、链路完整可追溯、导出结构机器可读。聚焦一个子场景（生成/校验/绑定/导出均可），本 Skill 主打"生成+绑定"。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、论文材料、目标结论范围。
2. 建立文献元数据：题名/作者/年份/版本/DOI（材料内信息）——追溯链的节点。
3. 材料缺失登记；不编造作者/年份。

## 3. 工作流程

### Step 1 断言拆分（拆得细）
- 每段结论 → 原子断言清单：`{assertion_id, text(独立可判真假), assertion_type(fact | comparison | causal | scope), 原文限定词保留}`。
- 拆分原则：不遗漏（复合句全拆）、不重复、每条不含多个可独立判断的命题。

### Step 2 证据绑定（对得上）
- 每条断言找**最小充分证据**：`{quote(逐字), locator(页/段/句/表), 支持程度(supports | partial | insufficient)}`。
- 主题相关≠支持；无证据断言标 unsupported_evidence（不是删除——诚实暴露）。

### Step 3 链路构建（追得回）
- 每条 nanopub：`{assertion → evidence → paper(题名/作者/年份/版本/DOI) → 原文位置}` 全链可走通。
- 版本信息（预印本/正式版）如实登记。

### Step 4 机器可读导出（读得懂）
- nanopub 风格结构化 JSON（字段子定义、枚举固定），可用脚本批量解析（附解析示例）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "nanopublication_generation",
  "status": "success | partial | failed",
  "paper": {"title":"...","authors":["..."],"year":2023,"version":"published","doi":"..."},
  "nanopubs": [
    {"np_id":"np1","assertion":{"text":"保留限定语的原子断言","type":"comparison",
      "source_text":"原结论句","paragraph":4},
     "evidence":[{"quote":"逐字片段","locator":{"page":5,"section":"Results","sentence":2},"support":"supports"}],
     "chain_complete":true},
    {"np_id":"np2","assertion":{"text":"...","type":"fact"},"evidence":[],"support":"unsupported_evidence",
     "note":"原文未提供可定位证据，诚实暴露","chain_complete":false}
  ],
  "machine_readable": {"format":"nanopub-json v1","parse_example":"示例脚本调用方式"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：断言粒度原子化（一段结论≥2 条或说明为何不可拆）；evidence 逐字+定位；unsupported 如实标注不删除；chain 字段完整；JSON 可脚本解析。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 结论句无法原子化（强耦合） | 保留为单断言并说明原因 |
| 证据跨页/图表引用 | 分条绑定并标注 |
| 预算不足 | 核心结论段先行（partial） |

## 6. 自查清单

1. [ ] 断言原子化、每条可独立判真假？
2. [ ] 每条有最小证据或诚实标 unsupported？
3. [ ] 链路字段完整（作者/年份/版本/位置）？
4. [ ] 导出 JSON 可被脚本解析？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。拆分先行；绑定批处理；导出格式一次定型。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
