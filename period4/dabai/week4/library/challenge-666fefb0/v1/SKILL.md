---
name: lit-auto-classifier
description: |
  文献与资料自动分类 Skill：在真实文件批次上完成"分类归目录→标签生成→规范改名→去重与版本区分→批量整理"，交付可回滚的操作记录与清单。
  方法主线：plan→apply 两阶段（plan 只出清单不动文件）；分类与标签依据标题/摘要/关键词/正文的真实命中并给归属依据；
  改名按模板降级规则处理特殊字符/超长/缺字段；去重按内容哈希+DOI+标题作者年份三级判据，明确保留/归档；
  全程幂等可重跑、失败可续跑、输出未处理项。不凭空补作者年份 DOI，不做精读翻译。
---

# 文献与资料自动分类（Classify · Tag · Rename · Dedupe）

## 1. 用途与适用范围

- **做**：一批文献/资料文件的批量整理：归入目录层级、打标签、改规范名、识别重复下载与预印本/正式版差异、输出未处理项。
- **不做**：文献检索发现、单篇精读、翻译润色。
- **验收三件事**：归属和标签能用原文核对；改名/去重/移动留可回滚记录；换一批同类文件重跑结果一致（幂等）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、输入目录、目录层级规则（项目/主题/文献类型/年份维度）、命名模板、输出要求。
2. 读 `task.md` 确认分类维度与标签粒度要求。
3. 输入目录为空/不可读 → status=failed。

## 3. 工作流程（五步）

### Step 1 盘点（`classify.py scan` → inventory.json）
路径、大小、sha256、可读性；PDF/docx 抽首页文本（标题/作者/年份/DOI 候选），扫描件无文本层记 unreadable。

### Step 2 分类与标签（`classify.py classify` → classification.json）
- **文献类型**判定：文件名+内容特征（`preprint|arxiv`→preprint；`proceedings|会议`→conference；`学位论文|thesis|dissertation`→thesis；`supplementary|补充材料`→supplement；其余含期刊特征词→journal；无法判→unknown 不硬猜）。
- **主题分类**：关键词规则表（`tag_rules.json`，可按案例领域扩充）对标题+摘要+首页文本打分，取 top1 为主目录，top2-3 为标签；无规则命中 → `uncategorized/`（显式，不硬塞）。
- 每份文件记录 `basis`：命中了哪些规则/关键词、来自标题还是正文——归属可核对。
- **标签归一**：同义词合并（表内），单文件标签 ≤5 个防爆炸，含上下位关系字段。

### Step 3 去重与版本区分（并入 classify 阶段）
三级判据：① sha256 相同=完全重复，保留主路径、其余归 `duplicates/`（不删除！）；② DOI 相同=同文不同版（预印本 vs 正式版），正式版为保留对象，预印本归档并在版本关系里链接；③ 标题+第一作者+年份相同=疑似重复，标记 `needs_review` 由人工/模型确认，不自动删。

### Step 4 计划与执行（`classify.py plan` → plan.json；`classify.py apply` → manifest.json + ops_log.jsonl）
- plan：每文件 `{action: move|rename|archive|keep, src, dst, reason}`，目标冲突时加 `_v2` 不覆盖；**不动文件**。
- apply：逐条执行+回读校验+JSONL 日志；幂等（重跑时已处理文件跳过）；失败记录 `unprocessed` 清单。
- 回滚：`classify.py rollback manifest.json` 按 ops_log 逆向恢复原路径。

### Step 5 汇总（→ /app/output/result.json）
按 §4 契约；同时输出 `unprocessed.json`（未处理项+原因）。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "classification": [{"src": "原路径", "dst": "库内路径", "doc_type": "journal|preprint|conference|thesis|supplement|unknown",
                       "tags": ["CRISPR", "基因编辑"], "basis": {"title_hit": ["CRISPR"], "rule": "gene-editing", "from": "title"}},
                     ...],
  "renames": [{"src": "download (3).pdf", "dst": "Zhang-2023-CRISPR筛选.pdf", "template": "作者-年份-标题", "degraded": "缺作者→标题前20字"}],
  "dedupe": {"exact_groups": [{"kept": "...", "archived": ["..."], "key": "sha256:abcd"}],
              "version_pairs": [{"preprint": "...", "published": "...", "key": "doi:10.1xxx"}],
              "needs_review": [{"paths": ["..."], "key": "title+author+year"}]},
  "operation_evidence": {"sha256_algo": "sha256", "plan": "plan.json", "ops_log": "ops_log.jsonl",
                          "manifest": "manifest.json", "rollback_cmd": "python3 scripts/classify.py rollback manifest.json"},
  "unprocessed": [{"src": "...", "reason": "unreadable|no_text_layer|name_conflict_unresolved"}],
  "uncertainty": ["2 组疑似重复待人工确认（标题+作者+年份相同但哈希不同）"]
}
```

## 5. 数字门槛

- 批次覆盖率 100%：每份输入文件必须出现在 classification/unprocessed/dedupe 三者之一。
- 幂等性：同输入重跑 apply，second run 无新增操作（no-op）。
- 归属依据率 100%：classification 每条都有 basis；无依据的进 uncategorized/。
- 元数据缺字段走降级规则并标注 degraded，不编造。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 损坏/加密 PDF、扫描件无文本层 | unprocessed + reason，不猜测分类 |
| 中文/特殊字符/超长文件名 | sanitize 表 + 180 字符截断，保留中文 |
| 同名不同版本 | dst 加 `_v2`，版本关系记录，不覆盖不删除 |
| 规则无命中 | uncategorized/ 目录，不硬塞标签 |
| apply 中断 | 续跑：按 manifest 已完成跳过 |
| 权限不足 | unprocessed + recovery 提示 |

## 7. 自查清单

- [ ] case_id 原样；plan 阶段未动文件；apply 有日志可回滚。
- [ ] 每条分类有 basis；标签 ≤5 且同义归一。
- [ ] 去重未删除任何文件（只归档/移动）。
- [ ] 重跑幂等；unprocessed 全部列出。

## 8. 效率约束

文本抽取与规则匹配全部脚本化（<2s/百文件）；模型请求仅用于 needs_review 的疑似重复确认与 uncategorized 兜底归类，≤8 次。

## 9. 最小示例（示意输出，非正式案例结果）

`classify.py classify <输入目录> --rules scripts/tag_rules.json --out classification.json`
→ `{"src": "papers/download (3).pdf", "dst": "gene-editing/2023/journal/Zhang-2023-CRISPR筛选.pdf", "doc_type": "journal", "tags": ["CRISPR", "筛选"], "basis": {"title_hit": ["CRISPR"]}}`
