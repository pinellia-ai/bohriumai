---
name: citation-reference-manager
description: |
  参考文献与引用管理 Skill：对给定稿件+文献库完成引用插入定位、编号更新、
  文献去重、格式转换与来源核验。核心机制是"文内引用↔文末条目双向对账"脚本，
  每条引用带位置与匹配依据，去重给出可解释判据，不编造文献、不静默合并条目。
---

# 参考文献与引用管理（双向对账 + 可解释去重）

## 1. 用途与适用范围

- 适用：学术稿件（Markdown/LaTeX/Word 导出文本）+ 文献库（BibTeX/RIS/CNKI 导出/JSON）的引用整理。
- 方法主线：**先建账、再对账**。把文内引用点与文末条目做成两张可机读的清单，脚本双向核对。
- 硬约束：不编造文献条目；每条引用给出匹配依据与原文位置；合并去重必须给判据。
- 不适用：全文写作。只做引用相关动作，其他请求标 out_of_scope。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、材料路径、`output_contract` 全字段。
2. 读 `/input/task.md`（如有）：确认目标规范（GB/T 7714—2015 / 指定 APA 版本 / 顺序编码制等）。
3. 逐个真实读取稿件与文献库文件；文献库先转成统一中间格式（JSON 条目）再处理。
4. 材料缺失 → 落 `status=failed` result.json，说明缺口，不虚构。

## 3. 工作流程

### Step 1 条目清单化
- 文献库解析为条目列表：`{key, title, authors, year, venue, vol, issue, pages, doi, type_marker}`。
- 解析失败的条目记入 `parse_failures`，不丢弃不补造字段。

### Step 2 去重归并（判据可解释）
- 归并判据按顺序：DOI 相同 → 归并；DOI 缺失但 规范化题名（小写、去标点）+ 首作者 + 年份 均一致 → 归并候选。
- 预印本 vs 正式版：题名近似且 venue 一为 arXiv 一为期刊 → 以正式版为主条目，arXiv 信息记入 `also_in`。
- 同名作者不同文献（题名不同）**不合并**。
- 每次合并写记录：`{kept, merged, basis}`，歧义条目标 needs_confirmation。

### Step 3 文内引用点提取
- 扫描正文引用标记（`[n]` / `\cite{key}` / `(Author, Year)` / 上标），逐点记录：
  `{id, locus(章节+句号), raw_marker, resolved_keys, claim_snippet}`。
- 每个引用点带**所在句**的 10-30 字摘录（claim_snippet），作为"挂得对"的证据。

### Step 4 双向对账（核心，跑 scripts/cite_audit.py）
- 文内→文末：每个引用点解析出的 key 都须在条目清单中，缺失记 `dangling_citations`。
- 文末→文内：每条条目至少被引用一次，未引用记 `orphan_entries`。
- 编号检查：顺序编码制下正文编号须连续、首现顺序与文末列表一致，异常记 `numbering_issues`。
- 位置检查：引用标记落在**需要支撑的那句**内；落在段末/图注附近的记 `misplaced`，建议具体位置。

### Step 5 论断-文献匹配
- 逐点判断 claim_snippet 与所引条目的主题/结论是否对应，判定 `match / mismatch / uncertain`。
- mismatch 与 uncertain 逐条给出理由；材料无法核验的标 unverified，**不判定为不存在**。

### Step 6 格式转换与编号重排
- 按目标规范重排文末列表（顺序编码制按首现；著者-出版年按字母序）。
- 保留 DOI、卷期页、文献类型标识等关键字段；字段缺失标 `[字段缺失]` 而非补造。
- 输出同步更新后的稿件全文与文献表（可编辑格式，与输入同构）。

## 4. 输出契约（/app/output/result.json）

以 case.json 的 `output_contract` 为准，本 skill 保证以下字段存在：

```json
{
  "case_id": "原样保留",
  "status": "complete | partial | failed",
  "revised_manuscript": "更新后的稿件全文（编号同步、可继续编辑）",
  "reference_list": "同步更新后的文末文献表",
  "citation_points": [{"id":"","locus":"","raw_marker":"","resolved_keys":[],"claim_snippet":"","match":"match|mismatch|uncertain","note":""}],
  "entries": [{"key":"","title":"","authors":[],"year":"","doi":"","source_field_gaps":[]}],
  "merge_records": [{"kept":"","merged":"","basis":""}],
  "audit": {"dangling_citations": [], "orphan_entries": [], "numbering_issues": [], "misplaced": []},
  "unverified": [{"item":"","reason":""}],
  "sources": [{"change":"","evidence":"稿件/文献库路径+位置"}],
  "uncertainty": "整体说明"
}
```

### 触发与调用方式
- 触发条件：任务涉及引用插入/编号/去重/格式转换/来源核验/一致性检查任一动作。
- 调用：读 case.json → Step1-2 条目清单化与去重 → Step3-4 提取与双向对账（脚本实跑）→ Step5-6 修复与重排 → result.json 落 /app/output。
- 脚本调用：`python3 scripts/cite_audit.py <稿件纯文本> <bib.json> [--style numeric|author_year]`，
  输出 JSON 对账报告，问题存在时退出码 1；报告原样写入 result.json 的 audit 字段。

### 双向对账执行要点
- 引用点提取覆盖四种形式：`[n]`、`[n,m]`、`[n-m]`、`\cite{key}`；其余样式（上标数字、脚注）手工提取并记录。
- 每个引用点的 claim_snippet 取所在句前 80 字符，用于"挂得对"与论断匹配判定。
- 编号重排后必须重跑一次对账脚本，确认 dangling/orphan 清零后才允许交付 complete。
- 文内标记与文末列表两份清单（citation_points、entries）是中间产物，保留在 /app/work 供复核。

## 5. 数字门槛

- 引用点与条目 100% 提取（数量写进 audit 上下文），对账脚本必须实跑且结果写入 result.json。
- dangling / orphan / numbering 三类问题必须为空或逐条解释；带病交付标 partial。
- 每条合并有 basis；每条 mismatch/uncertain 有 note。
- 脚本退出码非 0 时不得标 complete。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 文献库字段缺失 | 条目保留，缺口字段记入 source_field_gaps，不补造 |
| DOI 解析失败 | 条目标 unverified（核验不可达），不判定真假 |
| 同名作者/同名条目 | 题名不一致一律不合并，记入 unverified 请作者确认 |
| 稿件格式不支持 | 提取纯文本处理，保留原格式说明；失败标 failed 并说明 |
| 编号冲突（手写编号与库序不一致） | 以正文首现顺序为准重排，冲突明细记 numbering_issues |
| 引用样式混杂（混用 [n] 与 (Author, Year)） | 统一为目标规范，逐处记录在 sources |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] cite_audit.py 实跑通过，结果进 result.json
- [ ] 双向对账：无 dangling、无 orphan（或逐条标注）
- [ ] 编号连续且首现顺序=列表顺序
- [ ] 每条合并有判据；无静默合并
- [ ] 每个引用点带位置+claim_snippet
- [ ] 未核验条目全部标 unverified，未编造任何文献

## 8. 效率约束

预算 64 请求 / 900 秒。先落最小 result.json（revised_manuscript+audit），再补 citation_points 细节。
脚本仅用标准库，≤50 文件、≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入稿件一句：`Transformer 架构显著提升了长文本处理效果 [3]。`
输入文献库：`{"key":"vaswani2017","title":"Attention Is All You Need","year":"2017","doi":"10.5555/3295222"}`（仅 1 条）
若 `[3]` 无对应条目 → audit.dangling_citations = ["[3] @ S1-02"]；
对账脚本输出 `{"ok":false,"dangling":[...],"orphans":["vaswani2017"],"numbering_issues":["编号3无首现"]}`，
skill 据此改稿并如实记录，不猜测 `[3]` 应该是哪篇。
### 最小 result.json 完整示意（示意，非正式案例结果）
```json
{"case_id": "示例占位", "status": "complete",
 "revised_manuscript": "……（全文，编号已同步）",
 "reference_list": "[1] …\n[2] …",
 "citation_points": [{"id": "CP1", "locus": "P2-S3", "raw_marker": "[1]",
   "resolved_keys": ["zhang2021"], "claim_snippet": "对比学习显著提升召回率",
   "match": "match", "note": ""}],
 "entries": [{"key": "zhang2021", "title": "Contrastive…", "authors": ["Zhang"],
   "year": "2021", "doi": "10.1/x", "source_field_gaps": ["pages"]}],
 "merge_records": [{"kept": "zhang2021", "merged": "Zhang2021preprint",
   "basis": "DOI 相同，预印本并入正式版"}],
 "audit": {"dangling_citations": [], "orphan_entries": [], "numbering_issues": [], "misplaced": []},
 "unverified": [{"item": "wang2020", "reason": "DOI 解析不可达，真实性未核验"}],
 "sources": [{"change": "重排编号 [3]->[2]", "evidence": "稿件 P2 首现顺序"}],
 "uncertainty": ""}
```
