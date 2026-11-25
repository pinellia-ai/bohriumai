# challenge-cbe96f01 引用与事实核验 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 逐字段落实）
- `case_id` 原样；`status` success|partial|failed 含界限说明
- 审查报告：条目化问题清单（位置、原文、判定、严重度、修改建议），不是总体评价
- 依据与边界：稿件原文、引用证据及待复核项；区分错误/证据不足/建议
- 结果状态：通过、问题、待复核、未检查项；不凭空补齐缺失信息
- sources / uncertainty_notes / change_log

### 硬性要求
1. 每条结论能指到具体原文位置（file+locator+逐字quote）——**前代6分教训的核心修正：逐条引用原文位置，validator 强制**
2. 判定与引文语义一致；核心区分"引用存在"与"引用支持结论"
3. 引用支持四判定：fully/partially/unsupported/undeterminable
4. 覆盖六类：引用支持、事实来源可靠性、证据定位、数值统计一致性、论证链、学术规范
5. 输入外文献不检索不猜 → undeterminable；材料外内容标 unverifiable
6. 预算 64 请求/900 秒/16384 token；≤50 文件/2MB；先落盘最小 result.json
7. 提交目录根路径放 GITHUB_URL.txt

## 自测记录（2026-11-24，按 PLAYBOOK §4）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析（name=citation-fact-verify） | PASS |
| output_contract 字段 100% 覆盖 | PASS |
| scripts ast.parse 语法 | PASS ×2 |
| make_locators.py 实跑 | PASS（同 0999879e：5 段合成稿件，退出码 0/坏输入 2） |
| audit_check.py 实跑（好样例） | PASS：2 findings + 2 spots + 2 ledger，退出码 0 |
| audit_check.py 实跑（坏样例：ledger 缺 evidence_quote 的 unsupported） | PASS：正确 FAIL 退出码 1 |
| 无虚构 | PASS（判定枚举/字段均出自题面；示例标示意） |
| 资源限额 | PASS（4 文件 ~35KB） |
| SKILL.md 行数 | 约 150 行 |

## 使用方法
1. Step 0 读 /input/case.json + task.md，盘点 /input/
2. `python3 scripts/make_locators.py /input/<材料> --outdir /app/work`
3. Step 2 清点引用点 → citation_spots.csv；Step 3 逐条四判定 → citation_ledger.csv
4. Step 4-5 产出 findings.json；Step 6 coverage.json；先落盘最小 result.json
5. `python3 scripts/audit_check.py /app/output/result.json` 退出码 0 方可交付

## 已知限制
- 被引文献原文不在 /input 时一律 undeterminable（诚实优先于覆盖率）
- 扫描件无文本层时按页标 failed，result=partial
