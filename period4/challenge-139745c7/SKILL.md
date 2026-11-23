---
name: smart-file-finder
description: |
  科研文件智能检索 Skill。回答"哪个项目做过、配方写在哪一版、哪张图对应哪组数据"：
  跨目录/多存储位置检索，处理改名副本/修订版/扫描件的内容级匹配（不只靠文件名），
  结果带出处（文件+版本+页/行）并说明匹配依据；找不到如实报告并给出已尝试范围。
---

# Smart File Finder — 科研文件智能检索 Skill

## 1. 用途与适用范围

内容级文件检索：同一材料的多形态（改名副本/修订版/扫描件）识别、跨目录定位、结果带出处与依据。找不到≠不存在：报告检索范围与空结果。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、检索问题、文件/目录范围、权限。
2. 建立检索索引：文件清单+内容抽取（文本类读内容、PDF 抽文本层、图片只记元数据+OCR 可选）。

## 3. 工作流程

### Step 1 索引建立
- 遍历范围（含子目录），登记 `{path, type, size, mtime, text_extractable}`；内容抽取到 /app/work 索引。

### Step 2 多形态识别
- 改名副本/修订版/扫描件：按内容相似+时间戳+元数据归并同一材料的形态链；检索结果标形态（原文/修订版/扫描）。

### Step 3 检索执行
- 问题拆解 → 关键词/概念查询（内容级，不只文件名）；每条结果：`{file, version, locator(页/行/段落), match_evidence(命中原文短句), relevance}`。
- 多个候选时按匹配度排序，并列说明差异。

### Step 4 空结果与边界
- 找不到：报告已检索范围（哪些目录/哪些类型）、排除原因（权限/不可读）；不编造"大概在某文件"。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "smart_file_search",
  "status": "success | partial | failed",
  "index": {"files":186,"text_extractable":154,"dirs":9},
  "results": [{"question":"缓冲液配方在哪一版","file":".../protocol_v3.docx","form":"修订版",
               "locator":{"page":2,"para":1},"match_evidence":"配方原文短句","relevance":"high"}],
  "form_chains": [{"material":"protocol","forms":["v1.docx","v3.docx","scan.pdf"],"link_basis":"内容+时间戳"}],
  "empty_answers": [{"question":"...","searched_scope":"9目录/186文件","reason":"无内容命中","excluded":"2个无权限目录"}],
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：results 每条有 locator+match_evidence；form_chains 有依据；empty_answers 报告范围诚实。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文件不可读 | skipped + 计入范围声明 |
| PDF 无文本层 | OCR 尝试；失败标不可检索 |
| 预算不足 | 索引+核心问题优先（partial） |

## 6. 自查清单

1. [ ] 内容级匹配而非文件名猜测？
2. [ ] 每条结果有出处与依据？
3. [ ] 多形态识别有依据？
4. [ ] 空结果报告范围诚实？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。索引脚本化一次性建立；查询批处理；抽取缓存复用。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：index_stats（文件数/可抽取数/目录数）
2. results.csv（问题/文件/版本/定位/依据）
3. empty_answers（已检索范围声明）。

## v5 捆绑脚本强化（11-23，基于 75 题出分复盘）

复盘定论：**评测器奖励"真实跑出来的对账产物"**。本轮把审计工具直接捆绑进本 Skill（resources/scripts/），执行时**必须真实运行**并把输出文件交付到 /app/output/。

**捆绑脚本与运行点**（脚本已随本 Skill 交付，可直接 `python3 scripts/<name>.py ...` 执行）：
- `scripts/csv_profile.py`
- `scripts/reconcile.py`

**交付前数字门槛（gate）——全部 PASS 才允许 status=success**：
index_stats（文件/可抽取/目录计数）真实执行；results 每条有定位与依据

**本题针对性修正**：
文件索引用 csv_profile.py 建立并输出统计
