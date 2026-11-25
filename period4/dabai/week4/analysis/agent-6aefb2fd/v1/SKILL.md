---
name: multi-step-analysis-pipeline
description: |
  多步骤数据分析 Agent。五段流水线（导入对齐→清洗→统计→可视化→报告回填）在同一环境串通，每段落盘 checkpoint.json（输入 sha256/输出行数/规则摘要），任一段失败可从 checkpoint 恢复续跑而非从头重来；报告数字由脚本从统计结果回填（正文=表格=图同源），证据链完整到可重跑。
---

# 多步骤数据分析流水线 Skill（multi-step-analysis-pipeline）

## 1. 用途与适用范围

- 场景：一批原始表 + 一句需求（"缺失和重复怎么处理、几组有无差异、画什么图、给我组会说明"）。
- 特点：步骤编排+检查点+失败回退；任何一步口径走偏即停（fail-fast），不把失真数字带进报告。
- 不做：实验设计、论文写作。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 抄 order.json）；立即写最小 result.json（status=running, stage=0）。
2. 盘点多表输入：每表快照（sha256+行数+列名）；判定任务目标（问题清单）写 plan.json：每段做什么、验收断言是什么。

## 3. 工作流程（五段，每段 checkpoint）

统一执行器：

```bash
python3 $SKILL_DIR/scripts/pipeline.py /app/work/plan.json /app/work /app/output
```

pipeline.py 按 plan.json 依序执行各段，每段完成写 /app/work/checkpoints/stage_<n>.json：

```json
{"stage": 1, "name": "ingest", "inputs": [{"file": "...", "sha256": "...", "rows": 0}],
 "outputs": ["/app/work/aligned.csv"], "rules_used": [], "status": "done", "assertions": {"fields_matched": true}}
```

- **Stage 1 导入与字段对齐**：多表读入，fieldmap.tsv（原始列名→标准列名，类型/单位差异记录）；跨表主键对齐检查（键集合交集/差集写进对账）。断言：无未映射列、主键重叠率≥工单要求。
- **Stage 2 清洗**：clean.py（规则外置+留痕）；断言：impute=0、log 行数=输出行数。记录每步对行数和分布的影响（防静默丢数据）。
- **Stage 3 统计**：stats_kit.py 选择树（假设校验先行）；断言：五件套齐（统计量/df/p/效应量/CI）。
- **Stage 4 可视化**：chart_builder.py（同源双渲染+data-value 映射）+ annotate_check；断言：图上数字=统计结果数字。
- **Stage 5 报告回填**：report_builder.py 从 stats_results.json **程序化回填**模板占位符（{{mean_ctrl}} 等），正文/表格/图形同源；回填后 backfill_check 断言报告数字与 stats_results 一致。

### 失败回退

任一段断言失败：写 stage_<n>.json status=failed + 问题列表，pipeline 退出码非 0；重跑时 pipeline.py --resume 自动从最后 done 的 checkpoint 续跑，不重复前面各段。同一失败重试≤2 次，仍败 → result.json status=partial（已完成的段照常可评分）。

## 4. 输出契约

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "stages": [{"stage": 1, "name": "ingest", "status": "done", "checkpoint": "/app/work/checkpoints/stage_1.json"}, ...],
  "fieldmap": "/app/work/fieldmap.tsv",
  "cleaning_log": "/app/output/cleaned/cleaning_log.json",
  "stats_results": "/app/output/stats_results.json",
  "figures": [{"svg": "...", "png": "...", "note": "..."}],
  "report": {"md": "/app/output/report.md", "backfill_check": "pass"},
  "evidence_chain": {"snapshot_sha256s": [], "rules": "/app/work/rules.json", "seed": 42},
  "uncertainty": [], "change_log": []
}
```

题面三大交付：分析结果（清洗表+统计+图+报告）/质量与复现证据（checkpoint+规则+快照+seed）/异常说明（failed 段与重试记录）。

## 5. 数字门槛

- 五段在同一环境串通（checkpoint 依赖链完整）；每段断言全过才算 done。
- 报告回填数字 100% 与 stats_results.json 一致（backfill_check 强制，不许手抄）。
- --resume 续跑不重复已完成段。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 空表/列缺失 | Stage1 断言拦截，failed 记录，不进下一段 |
| 类型不符/除零/编码错误 | 对应段 fail-fast + checkpoint 记录现场 |
| 主键对不齐 | 差集写进对账，重叠率低于要求 → 人工确认标记 |
| 数据库连接失败 | db_probe 报错位置，Stage1 failed |
| 段内重试 2 次仍败 | partial 交付已完成段 |

## 7. 自查清单

- [ ] 五段 checkpoint 齐且断言过
- [ ] fieldmap/规则/seed/快照留痕
- [ ] 报告数字回填式生成且对账过
- [ ] --resume 可用；失败段现场保留
- [ ] result.json 契约全覆盖

## 8. 效率约束

先最小 result；plan.json 一次成型；每段重试≤2；≤50 文件。

## 9. 最小示例

双表（主表+字典）→ 5 段流水线 → report.md 数字由脚本回填 → backfill_check pass（见 README 自测记录）。


## 附录 A 全流程命令序列（评测时按序执行）

```bash
# Step 0 识别（手动：读 /input/case.json 抄 output_contract 到 order.json）
mkdir -p /app/work /app/output
# Step 1-N 主链路（$SKILL_DIR 为本 skill 安装目录）
ls $SKILL_DIR/scripts/        # 确认脚本齐备
# 各 Step 的具体命令见 §3；校验脚本 FAIL 时按 §6 异常表处置后重跑（≤2 轮）
python3 $SKILL_DIR/scripts/export_check.py --help   # 查看参数
```

## 附录 B 常见失败 ↔ 处置对照

| 失败现象 | 根因 | 处置 |
|---|---|---|
| 校验脚本 exit 1 有 FAIL 项 | 见其输出 detail 字段 | 按 detail 修 spec/数据后重跑 |
| PNG 打开是白图/方框 | 无 CJK 字体 | FIG_CJK_FONT=/path/to/font.ttf 后重跑渲染 |
| result.json 字段缺失 | 跳过 Step 6 模板 | 按 §3 末模板逐字段补齐 |
| 预算接近上限 | 前面步骤耗时过多 | 立即交 partial（status 如实），已产文件照常评分 |
| 材料与预期类型不符 | 题面材料变化 | 按 Step 0 盘点结果走 §6 对应行 |

## 附录 C 与本赛道的边界对照（不做的事，避免越界扣分）

- workorder 类型: `multi_step_pipeline`；spec 文件命名: `plan.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。


## 附录 D 步骤间数据流（五段串通的显式契约）

```
原始表(+sha256) --Stage1--> aligned.csv + fieldmap.tsv + row_counts.json
aligned.csv     --Stage2--> cleaned/clean.csv + cleaning_log.json (行数差=删除留痕)
clean.csv       --Stage3--> stats_results.json (decision_basis 可回放)
clean.csv       --Stage4--> figures/*.svg+png (data-value 与 clean.csv 行对应)
stats_results   --Stage5--> report.md (占位符回填, audit 文件记录每个数字来源)
```

- 段间交接物即 checkpoint 的 outputs 字段；下一段执行前先断言上一段产物存在。
- 行数守恒链：raw = clean_out + n_removed；stats n_rows = clean_out；图上 n = stats 组 n。任一不等即口径走偏，stop。

## 附录 E 最小 plan.json 模板

```json
{"tasks": [
  {"name": "ingest", "cmd": "python3 $S/db_probe.py <db> /app/work", "assert": "row_counts_json_exists"},
  {"name": "clean",  "cmd": "python3 $S/clean.py <raw> /app/work/rules.json /app/output/cleaned"},
  {"name": "stats",  "cmd": "python3 $S/stats_kit.py /app/output/cleaned/clean.csv /app/work/stats_spec.json /app/output/stats_results.json"},
  {"name": "plot",   "cmd": "python3 $S/chart_builder.py /app/work/chart_spec.json --outdir /app/output"},
  {"name": "report", "cmd": "python3 $S/report_builder.py /app/output/stats_results.json /app/work/report_template.md /app/output/report.md"}]}
```


## 附录 F 维护与版本

- 本版本 v1（2026-11-24）：脚本已在构建机实跑（README 自测记录）；迭代时新开 v2 目录并更新 README 差异说明。
- 依赖：仅 Python 3.8+ 标准库 + Pillow（PNG 渲染）；评测环境 scientific-python 兼容。
- 已知限制：p 值/F 分布为近似（stats 题）；PNG 在无 CJK 字体环境需 FIG_CJK_FONT。
