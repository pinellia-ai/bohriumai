# challenge-0999879e 论文质量审查 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 必须逐字段落实）
- `case_id`：从 /input/case.json 原样读取，不得改写
- `status`：success | partial | failed，含诚实状态与界限说明
- 审查报告：逐条问题、位置、严重度和修改建议；覆盖题目要求的检查项（六类：事实核验、引用支持、方法设计、统计报告、论证链、学术规范）
- 依据与边界：稿件原文、引用/数据/方法证据及待复核项；区分 fact_error / insufficient_evidence / norm_issue / suggestion
- 结果状态：通过、问题、待复核和未检查项；不凭空补齐缺失信息
- `sources` / `uncertainty_notes` / `change_log`：运行状态与不确定性

### 硬性要求（题面 §1 四条 + Harbor 运行契约）
1. 按检查项逐条审查输入，不是整篇评语
2. 每个问题提供原文位置和判断依据（file + locator + 逐字 quote）
3. 区分事实错误、证据不足、规范问题和建议性意见
4. 无法确认的条目标待复核，不凭空补结论
5. 输入 /input/case.json + task.md；过程 /app/work；产物 /app/output
6. 预算 64 请求 / 900 秒 / 16384 token；资源 ≤50 文件 / 单文件 500KB / 总 2MB
7. 不提交预制答案；skill 为通用流程
8. 提交目录根路径放 GITHUB_URL.txt

### 检查项覆盖要求（题面五个突破方向映射）
- 整体质量与结构完整性 → structure_check.csv
- 事实一致性与引用支持 → fact_verification / citation_support
- 方法设计与统计报告 → method_design / statistical_reporting
- 论证链与逻辑一致性 → argument_chain
- 学术规范与可发表性 → academic_norm

## 自测记录（2026-11-24，均按 PLAYBOOK §4）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析，name=paper-quality-audit 与目录用途一致 | PASS（python 解析 name/description 非空） |
| output_contract 字段 100% 覆盖 | PASS（case_id/status/审查报告/依据与边界/结果状态/sources/uncertainty_notes 均在 §4 基准全集） |
| scripts 语法检查 `ast.parse` | PASS（make_locators.py / audit_check.py） |
| audit_check.py 实跑（合成 result.json+findings.json+coverage.json） | PASS（合法样例退出码 0；缺 quote/缺 coverage 键/计数不一致的坏样例均退出码 1 且逐条报错） |
| make_locators.py 实跑（合成 txt 稿件 5 段） | PASS（paragraphs.csv 5 行，locator P001-P005，退出码 0；空输入退出码 2） |
| 无虚构（不编造接口/字段/数据） | PASS（仅用题面/runtime contract 出现的路径与字段；示例标注为示意输出） |
| 资源限额 | PASS（4 文件，约 30KB < 2MB） |
| SKILL.md 行数 | 约 170 行（150-400 区间内） |

## 使用方法

1. Agent 按 SKILL.md §2 Step 0 读 /input/case.json 与 task.md，盘点 /input/
2. `python3 scripts/make_locators.py /input/<材料> --outdir /app/work` 生成段落定位器
3. 按 SKILL.md §3 Step 2-4 逐类扫描，落盘 structure_check.csv / findings.json / evidence.csv / coverage.json
4. 进入扫描前先落盘最小 result.json（status=partial），完成后充实
5. `python3 scripts/audit_check.py /app/output/result.json` 退出码 0 方可交付

## 已知限制
- PDF 图表内容无法 OCR，相关一致性检查标 pending
- 引文原文不可得时不判"不支持"，标 pending_review
