---
name: citation-fact-verify-run
description: |
  引用与事实核验 Skill（执行版）。对给定论文真实执行核验流水线：抽取全部文内引用并
  建立引用清单 → 从参考文献区建立条目表 → 逐条匹配与四级支持判定（完整支持/部分支持/
  不支持/无法判定）→ 数值一致性检查 → 输出四件套（可检查结论清单 + 原始输出 +
  运行日志 + 评分表）。每条结论指到具体原文位置，换人按记录复核可得同一批结论。
---

# Citation Fact Verify — 引用与事实核验 Skill（真实执行版）

## 0. 运行契约（最高优先）

1. `/input/case.json` 的 `output_contract` 定义 result.json 必须字段——**逐字段原样落实**；`case_id` 原样读取。
2. 过程写 `/app/work/`；最终产物写 `/app/output/`。
3. 只依据实际输入文件核验；材料外事实标 `unverifiable`，**绝不凭空补结论**。
4. 预算 64 请求 / 900 秒：先落盘最小可用 result.json，再增强。

## 1. 输入识别

1. `ls /input/` 确认：论文文件（PDF/文本）、参考文献材料、事实核对源（如有）。
2. 记录材料形态：有文本层的 PDF 直接抽取；扫描件先 OCR（标注置信度）；纯文本直接进流程。

## 2. 核验流水线（真实执行，逐步留痕）

### Step 1 引用清单（citations.csv）
- 用脚本从正文抽取**全部**文内引用：编号式（[n]/上标）、作者-年份式（(Author, 2020)）。
- 每条：`{cite_id, 原文标记, 所在句(完整句子), 所在位置(页/段), 被支撑的论断}`。
- 验收：脚本报告"正文引用标记总数"，清单行数必须与之相等。

### Step 2 参考文献表（refs.csv）
- 从参考文献区逐条解析：`{ref_no/作者年份, 题名, 作者, 年份, 期刊, DOI/标识}`。
- 验收：文献区条目数 = refs.csv 行数。

### Step 3 匹配与异常
- 文内引用 ↔ 文献表匹配；孤儿引用（正文引了但表中无）、未引用条目（表中列了但正文未引）分别列出。

### Step 4 支持度判定（四级）
- 对每条"引用+论断"对，用材料内可及的被引内容判定：
  `fully_supported | partially_supported | not_supported | unverifiable`。
- 判定依据 = 被引内容原文短句（逐字）+ 一句比对说明；**主题相关 ≠ 完整支持**（结论超出引文范围记 not_supported）。
- 被引内容不在材料内 → unverifiable（诚实标注，不猜）。

### Step 5 数值与统计一致性
- 正文数值 vs 表格 vs 摘要 逐个对账（脚本比对数字集合）；不一致逐条登记（位置双方+数值双方）。

### Step 6 四件套交付（题面硬性要求）
- **可检查结论清单**：findings.json（每条含位置/依据/分级/建议）。
- **原始输出**：citations.csv、refs.csv、数值对账表（脚本真实产物）。
- **运行日志**：run_log.md——每步操作、命令、耗时、命中数（真实执行记录）。
- **评分表**：scoring_sheet.csv——自查打分（正确性/完整性/可复现性三列，逐条核过）。

## 3. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "citation_fact_verification",
  "status": "success | partial | failed",
  "citation_inventory": {"in_text_total":23,"matched":21,"orphans":1,"unreferenced":2},
  "verifications": [
    {"cite_id":"c3","loc":{"page":3,"paragraph":2},"claim":"稿件论断","ref":"[4]",
     "verdict":"partially_supported","evidence_quote":"被引内容原文短句",
     "comparison":"论断称X导致Y，引文仅报告相关性","suggestion":"改为'与X相关'"}
  ],
  "numeric_audit": [{"loc_pair":["正文§4","Table2"],"detail":"42% vs 38% 不一致"}],
  "deliverables": {"findings":"findings.json","raw_outputs":["citations.csv","refs.csv","numeric_audit.csv"],
                    "run_log":"run_log.md","scoring_sheet":"scoring_sheet.csv"},
  "stats": {"fully_supported":12,"partially":5,"not_supported":2,"unverifiable":4},
  "needs_review": [], "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：引用清单行数=正文标记总数（脚本验收）；四级判定逐条有逐字证据；四件套文件全部真实存在于 /app/output；unverifiable 不猜。

## 4. 异常处理

| 情况 | 处置 |
|---|---|
| 被引文献内容不在材料内 | unverifiable + 登记缺失 |
| 无文本层 | OCR + 置信度 |
| 参考文献区解析不全 | 部分交付 + gaps 说明 |
| 预算不足 | Step 1-3（清单与匹配）优先落盘 |

## 5. 自查清单

1. [ ] 引用清单与正文标记数对账？
2. [ ] 四级判定逐条有逐字证据？related≠supported？
3. [ ] 数值对账做了？
4. [ ] 四件套齐全且为真实执行产物？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 6. 最小示例（示意，非正式结果）

```json
{"case_id":"demo","citation_inventory":{"in_text_total":3,"matched":3,"orphans":0,"unreferenced":0},
 "verifications":[{"cite_id":"c1","loc":{"page":2,"paragraph":1},"claim":"A提升B 50%","ref":"[1]",
   "verdict":"not_supported","evidence_quote":"B improved by 20% in [1]","comparison":"幅度不符","suggestion":"改为20%或引其他来源"}],
 "deliverables":{"findings":"findings.json","raw_outputs":["citations.csv"],"run_log":"run_log.md","scoring_sheet":"scoring_sheet.csv"},
 "stats":{"fully_supported":1,"partially":1,"not_supported":1,"unverifiable":0}}
```

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 保持 v2 重写路径：引用清单行数=正文标记数断言；四级判定分布计数；四件套（findings/raw_outputs/run_log/scoring_sheet）存在性校验。
