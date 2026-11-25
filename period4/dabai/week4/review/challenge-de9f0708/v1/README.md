# challenge-de9f0708 学术规范与合规检查 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 逐字段落实）
- `case_id` 原样；`status` success|partial|failed 含界限说明
- 审查报告：逐条问题（原文定位、判定依据、严重度、可执行修改建议），不是泛泛规范提醒
- 依据与边界：稿件原文、规范/指南/授权证据及待复核项；区分错误/证据不足/建议
- 结果状态：通过、问题、待复核、未检查项；不凭空补齐
- sources / uncertainty_notes / change_log

### 硬性要求
1. 报出的问题成立并能指回原文位置（file+locator+逐字quote）
2. 每条判定绑定可核对依据（basis_ref → basis_registry 登记的依据条目）；依据取不到标 needs_review，不判违规
3. **不编造条款、期刊要求或文献元数据**
4. 不把风格差异/学科惯例误判为违规；漏报与误报同等扣分
5. 六风险面逐项检查：学术诚信、引用规范、隐私与数据合规、版权与许可、伦理审查、投稿要求
6. 有目标期刊指南时拆条目映射并注明指南版本与日期；无指南标 na 不虚构
7. 预算 64 请求/900 秒/16384 token；≤50 文件/2MB；先落盘最小 result.json
8. 提交目录根路径放 GITHUB_URL.txt

## 自测记录（2026-11-24，按 PLAYBOOK §4）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析（name=norm-compliance-audit） | PASS |
| output_contract 字段 100% 覆盖 | PASS |
| scripts ast.parse 语法 | PASS ×2 |
| make_locators.py 实跑 | PASS（同基准：合成稿件 5 段，退出码 0） |
| audit_check.py 实跑（好样例：basis_registry 2 条、1 finding 绑定依据、declarations_check、coverage 双套键） | PASS 退出码 0 |
| audit_check.py 实跑（坏样例①：finding 的 basis_ref 未登记于 registry） | 正确 FAIL 退出码 1 |
| audit_check.py 实跑（坏样例②：basis_registry 缺失） | 正确 FAIL 退出码 1 |
| 无虚构 | PASS（不内置任何期刊具体要求；示例标示意） |
| 资源限额 | PASS（4 文件 ~35KB） |
| SKILL.md 行数 | 约 160 行 |

## 使用方法
1. Step 0 读 /input/case.json + task.md，确认目标期刊与材料
2. `python3 scripts/make_locators.py /input/<材料> --outdir /app/work`
3. Step 2 登记 basis_registry.json（依据源，无依据不阻断但需外部条款的判定标 needs_review）
4. Step 3 六面扫描 → findings.json；Step 4 declarations_check.csv；Step 5 submission_map.csv（如有指南）
5. 先落盘最小 result.json（partial），完成后充实
6. `python3 scripts/audit_check.py /app/output/result.json` 退出码 0 方可交付

## 已知限制
- 目标期刊指南不在输入时 submission_requirements 标 na，不虚构期刊要求
- 受限数据只做脱敏建议，不复制敏感内容
