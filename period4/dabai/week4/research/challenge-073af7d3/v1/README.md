# challenge-073af7d3 研究前沿与趋势分析 v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：研究产物（时间趋势/主题演化/代表作/空白四类可检查产物）、证据矩阵（stat_row+exemplar_refs locator）、不确定性（口径/补录/缺失声明）
- [x] result.json 含 case_id + status
- [x] 突破方向覆盖：时间趋势（YoY/CAGR+拐点判据写死+口径声明）、主题演化（词表驱动 emergence/decline 事件+动因证据）、代表性工作（口径显式：cited/pioneering/designated，避免只看总被引）、空白识别（三型判据+exclusion_query 排除证据）
- [x] 不把检索前几条当前沿、不把"没检索到"当空白
- [x] 统计全脚本化可复算；实跑通过

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=research-trend-analyzer。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：trend_stats.py PASS。
4. 构造 12 条题录实跑（跨 2017-2023，4 主题）：
   - normalize：去重流水+缺失年率 0；yearly：逐年 count/yoy/topic_share 正确；拐点判据：|YoY|≥50% 且持续同向，4 个候选均判"单年波动"（小样本下符合判据）
   - topics：4 主题 emergence 事件各带 stat_row+exemplar_refs：PASS
   - 重跑 diff=0（可复算）：PASS
5. 无虚构：CAGR n<4 时 insufficient；被引缺失时代表作换口径：PASS

## 调用方式

```bash
python3 scripts/trend_stats.py normalize <题录.json|文献目录> --out /app/work/corpus.json
python3 scripts/trend_stats.py yearly /app/work/corpus.json --out /app/work/yearly_stats.csv --topic-lexicon scripts/topic_lexicon.json
python3 scripts/trend_stats.py topics /app/work/corpus.json --lexicon scripts/topic_lexicon.json --out /app/work/topic_evolution.json
# Agent 补 landmarks/gaps（判据见 SKILL.md §3 Step4/5），汇总写 /app/output/result.json
```

## 边界与限制

- 统计口径（出版年类型/被引可得性）必须声明；年份缺失 >40% 不可补 → partial。
- 演化动因无文献依据时标 descriptive，不冒充因果。
