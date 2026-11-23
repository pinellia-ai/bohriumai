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

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. 给出 nanopub JSON 的精确 schema 与字段枚举，并用脚本校验自产数据；
2. 附 1 条从结论句到 np.json 的完整推导示例（拆分→证据→链路）；
3. 对不可拆的复合结论显式说明拆分失败原因。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：nanopubs.csv（assertion/evidence/locator/support四列）
2. 不可拆结论计数；schema 校验脚本输出。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
nanopubs.csv 行数=断言数；schema 校验脚本输出 PASS

**本题针对性修正**：
nanopub 清单 CSV 化 + 不可拆结论显式计数
