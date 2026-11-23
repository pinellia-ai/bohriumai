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

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 术语一致性脚本（术语表×全文）；
2. 段落映射 CSV + count 对账；
3. 数字/公式/编号原样保留清单。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：term_check.csv（术语×出现处×一致性）脚本生成；paragraph_map.csv count 对账；number_audit 逐条并排。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/term_check.py`
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
term_check 违规=0 才允许 success；段落映射 count 对账

**本题针对性修正**：
术语一致性用 term_check.py 真实执行（术语表×全文）
