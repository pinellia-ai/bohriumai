---
name: reference-citation-manager
description: |
  参考文献与引用管理 Skill。挂得对（引用插到真正需要支撑的句子位置）、编得顺（插删调序
  后编号同步更新、连续、样式一致）、收得净（中英题名/预印本与正式版去重归并）、核得实
  （著录字段核验、来源可查、正文—文献表一一对应）。输出规范化文献表 + 引用位置审计 +
  一致性对账。
---

# Reference & Citation Manager — 参考文献与引用管理 Skill

## 1. 用途与适用范围

引用管理四问：挂得对、编得顺、收得净、核得实。同一稿件+同一文献库做前后对照可复跑。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、稿件、文献库/文献列表、目标引用样式。
2. 建立基线：正文引用位置清单、文献条目清单（题名/作者/年份/DOI/来源）。
3. 文献库缺失条目：如实登记，不编造文献。

## 3. 工作流程

### Step 1 引用位置审计（挂得对）
- 每处引用检查：是否落在**真正需要来源支撑的论断句**上（不是段末凑数/图表注旁误挂）。
- 论断-引用匹配：引用文献是否支撑该句结论（supports | partial | related_only | contradicts）。
- 误挂/装饰性引用 → 建议移位或删除，理由登记。

### Step 2 编号与样式（编得顺）
- 插入/删除/调序后**全文重新编号**：正文编号、上标/方括号样式统一、交叉引用（如 "见[3]"）同步更新。
- 文末列表顺序与正文首次出现顺序一致；编号连续无跳号。

### Step 3 文献去重归并（收得净）
- 同一文多形态（中英题名/预印本 DOI vs 正式版）按标识符+题名规范化归并，保留**正式优先**版本并记录合并链。
- 重复条目合并后正文引用指向统一条目。

### Step 4 著录核验（核得实）
- 逐条核验：作者/年份/期刊/卷期/DOI 与给定文献库一致；字段缺项登记。
- 正文-文献表对账：每处正文引用有对应条目、每条条目至少被引用一次（孤儿文献列出）。
- 结论被改写的引用（文献说了 A 稿件写成 B）→ 标 mismatch。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "reference_citation_management",
  "status": "success | partial | failed",
  "placement_audit": [{"loc":"§2 para3","sentence":"...","verdict":"correctly_placed | misplaced | decorative",
                       "support":"supports","suggestion":null}],
  "renumbering": {"citations_renumbered":23,"style":"numeric-superscript","continuous":true,"crossrefs_updated":5},
  "dedup_log": [{"kept":"[7] 正式版","merged":["[15] 预印本"],"key":"DOI 10.x/y","basis":"同文版本"}],
  "metadata_check": [{"ref":"[3]","authors_ok":true,"year_ok":true,"doi_ok":true,"issues":[]}],
  "consistency": {"in_text_without_entry":[],"orphan_entries":["[19]"],"mismatch_claims":[{"loc":"§4","note":"文献结论为X，稿件写为Y"}]},
  "files": {"references":"references_clean.md","manuscript":"manuscript_v2.md"},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：placement_audit 全覆盖；renumbering 后无跳号（可脚本验证）；dedup 保留链完整；in_text_without_entry 与 orphan_entries 双向对账；mismatch 逐条登记。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 文献库无对应条目 | 不编造；标记缺失引用 + needs_human_review |
| 著录信息冲突 | 并列记录，按库为准 + 登记 |
| 预算不足 | 编号对账+去重优先（partial） |

## 6. 自查清单

1. [ ] 每处引用位置与支撑关系审计过？
2. [ ] 编号连续、样式统一、交叉引用同步？
3. [ ] 去重归并有依据？正式版优先？
4. [ ] 双向对账（正文↔文献表）通过？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。基线清单脚本化；编号重排脚本执行；对账自动+抽样人工。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：事实底稿/配置/日志/文献是事实依据；不为行文顺畅补造数值或文献；不编造软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（稿件文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：事实、数字、引用保留来源或修改记录。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
