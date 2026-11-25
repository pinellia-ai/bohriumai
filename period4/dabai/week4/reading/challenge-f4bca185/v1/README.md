# challenge-f4bca185 · 文献数据清洗与标准化（v1）

## 交付标准清单（自题面提取）

- output_contract 全字段逐字段落实 result.json（评测时以 /input/case.json 为最高优先），case_id 原样保留。
- 端到端交付：可统计数据表（clean_data.csv）+ 行级变更记录（change_log.jsonl）+ 待人工确认清单（needs_review.jsonl），不是只演示换算脚本。
- 规则库有编号/有优先级/可增删（rules.jsonl），每条带适用条件与失效情形。
- 换算纪律：原值永不改动，输出 value_raw/unit_raw/value_std/unit_std/formula/precision_note；复合单位、前缀、区间值逐一处理；unknown_unit 不猜。
- 去重按可解释判定键（物质+指标+条件），区分"重复记录"与"重复实验"，数值不一致 needs_review 不自动取值。
- 科学冲突不裁决，双列保留转人工；缺值空缺不填0不插值。
- 行级追溯：每个改动沿 rule_id 回到输入行（file+line_no）；行数守恒。
- 资源限额：≤50 文件 / 2MB。

## 自测记录

- YAML frontmatter 可解析：name=literature-data-clean-standardize，通过。
- scripts/clean_pipeline.py 语法（ast.parse）通过；`--selftest` 实跑通过：三组单位换算往返误差 <1e-9 spot-check 通过，bar→kPa 前向换算正确（1 bar=100 kPa），合法行 reconcile 干净。
- output_contract 覆盖：SKILL.md §4 基准全集（case_id/status/cleaning/conversions/dedup/anomaly_report/traceability/evidence_and_boundary/run_status/sources/uncertainty_notes/change_log），声明 case.json 优先。
- SKILL.md 约 190 行，含数字门槛（§5）、异常处理表（§6）、自查清单（§7）、最小示例（§9）。
- 文件数 3、总量 <2MB，通过。

## 版本说明

v1 初版：规则库→字段规范化→单位换算→重复检测→异常报告与导出→result.json 六步流水线 + 换算往返校验脚本。
