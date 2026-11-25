---
name: research-trend-analyzer
description: |
  研究前沿与趋势分析 Skill：在同一主题跨年份文献集上交付四类可检查产物：时间趋势（年度分布+增长量化）、主题演化
  （出现/合并/分裂/衰退+阶段划分）、代表性工作（口径可说明、覆盖各阶段）、研究空白（有排除证据）。
  方法主线：题录规范化（年份归一+去重）→时间切片统计（脚本化、可复算）→主题词表驱动归并（防同名异义）→
  增长量化（YoY/CAGR，区分波动与拐点）→每条趋势/演化/空白判断回链到具体文献与统计行。不把检索前几条当前沿、
  不把关键词热度当趋势、不把"没检索到"当空白。全程离线、统计表可复算。
---

# 研究前沿与趋势分析（Time Slices · Evolution · Landmarks · Gaps）

## 1. 用途与适用范围

- **做**：判断一个方向"现在做到哪、往哪走、哪里还空着"：年度产出统计、主题演化追踪、各阶段代表作、有排除证据的空白。验收四件事：趋势由可核对年度分布支撑；演化说清"何时、因什么变化"；代表作口径可说明；空白有排除证据。
- **不做**：文献检索发现本身、单篇精读、综述正文写作。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、文献集（题录/PDF/CSV）、主题、时间窗、输出要求。
2. 盘点文献集：条数、年份分布、字段完整率（year/title/keywords 可用率）。年份缺失率 >20% → 先补录（从文件名/内容）并记入 uncertainty。
3. 文献集为空 → status=failed；**"没检索到"不等于空白**（空白判据见 Step 5）。

## 3. 工作流程（六步）

### Step 1 题录规范化（`trend_stats.py normalize` → corpus.json）
- 年份归一：取出版年（优先元数据字段，其次文件名/首页正则），同文献多版本取最早出版年。
- 去重：DOI > 标题+第一作者+年份 三级判据；去重后计数进 PRISMA 式流水（总→去重→入分析）。
- 每条记录：`{rec_id, title, year, authors[0], venue, keywords[], source_file, locator, dedup_status}`。

### Step 2 时间切片统计（`trend_stats.py yearly` → yearly_stats.csv）
- 按年份（或案例指定时间窗）统计：产出量、主题占比、增长率。
- 增长量化：YoY（逐年）、CAGR（窗口内复合增长率，n≥3 才计算，否则标 insufficient_window）。
- **拐点判据写死**：|YoY| ≥50% 且随后一年同向 → 候选拐点；单年波动不叫拐点（离散波动 vs 真实拐点显式区分）。
- 数据口径声明：统计基于"在线发表/见刊/预印本"哪一年（字段 provenance），口径影响结论必须写明。

### Step 3 主题演化（`trend_stats.py topics` → topic_evolution.json）
- 主题词表驱动（scripts/topic_lexicon.json，按案例领域扩充）：每条主题=关键词组，含同义词合并与上下位；同名异义在词表里用限定词区分。
- 逐年主题占比矩阵 → 演化事件识别：出现（占比首次≥5%）、合并（两主题共现率跃升）、分裂（父主题占比下降且子主题上升）、衰退（占比连续 3 年下降且低于峰值 1/3）。
- 每个演化事件附证据：`{event, year, evidence: {stat_row, exemplar_refs[2+]}}`——"因为什么变化"尽量引文献内变化动因（如新数据集出现），无文献依据则标 descriptive。

### Step 4 代表性工作（→ landmarks.json）
- 口径显式：每阶段（切片期）选 N 篇，入选标准 = 阶段内被引最高（如元数据含被引）**或** 主题首创（词表内该主题关键词首次出现于标题/摘要）**或** 案例指定。
- 明确避免只用总被引排序：每阶段至少 1 篇"方法首创"型（长尾首创），入选理由逐篇写明（criterion + locator）。

### Step 5 研究空白（→ gaps.json）
空白判据三型（每型需排除证据，非检索遗漏）：
- `recurring_unsolved`：≥2 篇文献提出同一未解决问题（各带 locator）且后续年份无解法文献命中（排除检索式附上）。
- `method_failure`：方法在特定对象/尺度失效的明确陈述（原文 locator）。
- `conflict_unresolved`：结论冲突且双方均无后续调和文献。
- 每条空白：`{gap, type, evidence[], exclusion_query, uncertainty}`。

### Step 6 汇总（→ /app/output/result.json）
四类产物 + 每条判断回链（stat_row 或 locator）；趋势判断区分 material_fact（统计行）/ inference（解读）/ unverifiable。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "corpus": {"n_total": 0, "n_after_dedup": 0, "year_range": [2019, 2024], "year_missing_rate": 0.0,
              "provenance": "见刊年（元数据字段）"},
  "time_trend": {"yearly": [{"year": 2023, "count": 42, "yoy": 0.35, "topic_share": {"A": 0.4}}],
                  "cagr": {"window": [2020, 2024], "value": 0.28, "insufficient": false},
                  "inflections": [{"year": 2022, "yoy": 0.62, "sustained": true, "note": "数据集发布年"}]},
  "topic_evolution": {"events": [{"event": "emergence|merge|split|decline", "topic": "...", "year": 0,
                                    "evidence": {"stat_row": "...", "exemplar_refs": ["ref@locator", "ref@locator"]}}],
                        "lexicon": "scripts/topic_lexicon.json"},
  "landmarks": [{"stage": "2020-2021", "ref": "...", "locator": "...", "criterion": "cited|pioneering|designated", "reason": "..."}],
  "gaps": [{"gap": "...", "type": "recurring_unsolved|method_failure|conflict_unresolved",
             "evidence": ["ref@locator"], "exclusion_query": "...", "uncertainty": "..."}],
  "uncertainty": ["年份缺失 8% 已从文件名补录", "被引数据缺失，代表作以首创口径为主"],
  "operation_evidence": {"scripts": ["trend_stats.py"], "stats_files": ["corpus.json", "yearly_stats.csv", "topic_evolution.json"],
                          "rerun_cmd": "trend_stats.py normalize→yearly→topics 可复算全部统计"}
}
```

## 5. 数字门槛

- 统计可复算率 100%：yearly/topic 统计由脚本输出，重跑 diff=0。
- 回链率 100%：每条演化事件/代表作/空白有 locator 或 stat_row。
- 拐点不虚报：无 sustained 证据的单年波动记为波动不记拐点。
- 空白排除证据率 100%：每条空白有 exclusion_query。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 年份缺失 | 文件名/内容补录 + 补录率进 uncertainty；>40% 不可补 → partial |
| 主题歧义（同名异义） | 词表限定词区分，歧义条目单独列出 |
| 文献量爆炸 | 按案例时间窗+抽样规则（如每年 top-cited）收缩，口径声明 |
| CAGR 窗口 <3 年 | insufficient=true，不给复合增长率 |
| 被引数据缺失 | 代表作改首创/指定口径并声明 |
| 证据冲突 | gaps 的 conflict_unresolved 型登记 |

## 7. 自查清单

- [ ] case_id 原样；四类产物齐全。
- [ ] 统计重跑可复算；拐点有 sustained 判据。
- [ ] 每条演化/代表作/空白有回链；空白有排除检索式。
- [ ] 口径（出版年类型、被引有无）已声明。

## 8. 效率约束

normalize/yearly/topics 全脚本化（<2s/千条）；模型请求用于：词表定制 1 次、演化动因解读 ≤4 次、空白判读 ≤2 次。先落 yearly_stats.csv（纯脚本），再解读。

## 9. 最小示例（示意输出，非正式案例结果）

`trend_stats.py yearly corpus.json --out yearly_stats.csv`
→ `{"year": 2022, "count": 55, "yoy": 0.57}`；
inflection 示例：`{"year": 2022, "yoy": 0.57, "sustained": true, "note": "2021 大规模数据集发布（Smith 2021@p1）"}`
