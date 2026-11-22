---
name: auto-classifier-renamer
description: |
  文献与资料自动分类 Skill。批量整理成百上千文件：按内容归入正确目录层级、补齐元数据
  （标题/作者/年份/期刊/DOI）、统一规则重命名、识别重复下载与预印本/正式版版本差异。
  分类依据可解释、批量可复跑、原文件不动（映射登记）。
---

# Auto Classifier — 文献与资料自动分类 Skill

## 1. 用途与适用范围

混杂目录（期刊 PDF/预印本/会议/学位论文/补充材料/数据集/扫描件）→ 结构化资料库：分类、元数据补齐、统一重命名、去重、版本区分。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、目录清单、分类规则/目标层级、重命名规则。
2. 盘点全量文件 + 类型探测（文本抽取/元数据读取）。

## 3. 工作流程

### Step 1 分类判定（依据可解释）
- 每文件：`{type判定依据(内容/元数据特征), 目标层级}`——依据引用文件内证据（题名行/期刊名/DOI 前缀）。
- 无法判定（内容缺失/纯图片）：uncertain 组 + needs_human_review，不硬分。

### Step 2 元数据补齐
- 从文件内容/文件名/路径抽取：标题、作者、年份、期刊、DOI；缺失字段标 null（不猜）。
- 预印本 vs 正式版：按 DOI 前缀/版本标记区分并链接。

### Step 3 统一重命名
- 规则化：`{年份}_{第一作者}_{标题缩写}_{类型}{版本}`；重命名=映射表登记（原→新），不实际删除/覆盖原文件。

### Step 4 去重与批量执行
- 重复下载（同内容多份）：按哈希/标识符识别，保留主份+dup 记录。
- 批量执行报告：处理数/跳过数/冲突数对账；操作可重跑（映射表驱动）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "auto_classification",
  "status": "success | partial | failed",
  "classified": [{"file":"...","type":"journal_pdf","target_dir":"papers/2024/","basis":"含 DOI 10.x 与期刊名","meta":{"title":"...","authors":"...","year":2024,"doi":"...","journal":"..."},"new_name":"2024_Zhang_TitleAbbrev_journal.pdf","rename_map":"原→新"}],
  "uncertain": [{"file":"...","reason":"无文本层","needs_human_review":true}],
  "versions": [{"material":"...","preprint":"...","published":"...","link_basis":"DOI 关联"}],
  "duplicates": [{"kept":"...","dups":["..."],"key":"sha256"}],
  "reconciliation": {"total":823,"classified":795,"uncertain":18,"renamed":795,"duplicates":41,"match":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：分类依据引内容证据；reconciliation 对账；重命名映射可回溯；uncertain 不硬分。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 元数据字段全缺 | null + needs_human_review |
| 重命名规则冲突（同名目标） | 加序号后缀 + 冲突登记 |
| 预算不足 | 分类+重命名优先（partial） |

## 6. 自查清单

1. [ ] 分类有内容证据？uncertain 不硬分？
2. [ ] 元数据缺失如实 null？
3. [ ] 版本区分（预印本/正式版）？
4. [ ] 对账成立？映射可回溯？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。内容探测与分类脚本化批处理；映射表驱动重命名；对账自动。

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
1. 交付量化对账：reconciliation（total=classified
2. uncertain）
3. rename_map.csv（原→新）
4. duplicates.csv（哈希键）
5. 元数据缺失字段计数。
