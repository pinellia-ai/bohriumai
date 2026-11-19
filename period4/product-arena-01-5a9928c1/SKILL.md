---
name: term-table-translator
description: |
  文献翻译 Skill。术语表驱动（术语表被真正执行而非写在提示里）：术语稳（全篇同一译名
  含题注结论）、段落全（跨页跨栏不漏不重，段号与原文一一对应）、关系准（指代/否定限定/
  因果让步/数字单位/公式编号一致）、可核验（双语对照+回查路径）。长文分段续译，术语表
  随译维护。
---

# Term-table Translator — 文献翻译 Skill（双语可核验）

## 1. 用途与适用范围

科研论文翻译四问：术语稳、段落全、关系准、可核验。交付双语对照稿 + 术语表 + 段落映射表，使任何人可逐段核对译文与原文。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、原文（带段落定位）、目标语言、术语表要求。
2. 术语初表：从原文抽取领域术语/缩写（材料内已有对应译名的优先采用并标 original）。
3. 记录段落定位体系（页/段/栏）。

## 3. 工作流程

### Step 1 术语表定稿（先于翻译）
- `{英文原文, 译名, 首现位置, source(original 译名表 | contextual 上下文 | common_sense 显式标注)}`。
- 缩写首现"中文全称（英文缩写）"；歧义缩写按语境选定并登记。
- 译名锁定全篇：后续翻译只查表，每处术语用词与表一致。

### Step 2 分段对照翻译（段落全）
- 段号一一对应：`{src_loc → tgt_loc}` 映射表；跨页/跨栏段落归并时保留两端定位。
- 不漏段不重段（count 对账：原文段数 = 译文段数）。

### Step 3 关系保真（关系准）
- 指代对象明确（it/they/this 复核先行词）；否定与限定范围保持（not A and B 的覆盖面）；因果与让步强度对应。
- 数字、单位、公式、文献编号**原样保留**（不改写不换算）；图表编号与题注随文对应。

### Step 4 核验与交付
- 术语一致性抽查：全部术语出现处回查术语表（脚本可执行）。
- 双语对照稿按段对齐输出；译文质量问题（原文语病等）标注不擅自"修复"事实。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "literature_translation",
  "status": "success | partial | failed",
  "term_table": [{"en":"pyroptosis","zh":"细胞焦亡","first_seen":"p1 para2","source":"original | contextual | common_sense"}],
  "paragraph_map": [{"src":{"page":1,"para":2},"tgt":{"para":2},"complete":true}],
  "bilingual": [{"para":1,"src":"英文原文","tgt":"中文译文"}],
  "relations_audit": [{"para":3,"type":"negation | causality | reference | number_unit","ok":true,"note":null}],
  "term_check": {"terms":14,"consistent":14,"violations":[]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：term_check violations=空；paragraph_map 全覆盖（count 对账）；relations_audit 覆盖关键句；公式/数字原样。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 原文语病/乱码 | 按最合理解读翻译 + note 记录原文问题 |
| 长句难对齐 | 拆句标注 1:n，段号不乱 |
| 术语无既定译名 | 按学科惯例定译 + common_sense 标注 |
| 预算不足 | 术语表+摘要+核心章节先行（partial） |

## 6. 自查清单

1. [ ] 术语表被执行全篇一致（含图注结论）？
2. [ ] 段落映射完整无漏重？
3. [ ] 否定/因果/指代/数字保真？
4. [ ] 双语对照可逐段核对？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。术语表先行；分段翻译批处理；术语一致性脚本抽查。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：实际输入文件与原论文是事实依据；不依据错误的领域标签补造数据；不编造内容/引用/软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：关键结论保留页码/段落/字段/图表定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
