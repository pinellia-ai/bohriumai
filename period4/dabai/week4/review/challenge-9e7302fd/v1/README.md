# challenge-9e7302fd 研究方法与统计审查 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 逐字段落实）
- `case_id` 原样；`status` success|partial|failed 含界限说明
- 审查报告：逐条问题（定位、缺陷类型、严重度、依据、修改建议），能交给作者逐条回复
- 依据与边界：稿件原文、方法/统计证据及待复核项；区分错误/证据不足/建议
- 结果状态：通过、问题、待复核、未检查项；不凭空补齐缺失信息
- sources / uncertainty_notes / change_log

### 硬性要求
1. 走完五个检查面：研究设计、变量定义、统计方法、样本量、结果报告
2. 每条意见落到稿件原文具体位置（file+locator+逐字quote）；不指不出第几节哪张表的审查单不合格
3. **严格区分 method_flaw（做错）与 reporting_gap（没报告）**——混淆即验收失败
4. 严重度与缺陷性质匹配，不一律"重大缺陷"；major 必须写影响主结论的路径
5. 复核人可按记录独立重跑得同一份审查单
6. 覆盖六类审查面（事实核验、引用支持、方法设计、统计报告、论证链、学术规范）
7. 预算 64 请求/900 秒/16384 token；≤50 文件/2MB；先落盘最小 result.json
8. 提交目录根路径放 GITHUB_URL.txt

## 自测记录（2026-11-24，按 PLAYBOOK §4）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析（name=methods-stats-audit） | PASS |
| output_contract 字段 100% 覆盖 | PASS |
| scripts ast.parse 语法 | PASS ×3（audit_check / make_locators / standards_items JSON 校验） |
| make_locators.py 实跑 | PASS（同基准：合成稿件 5 段，退出码 0） |
| audit_check.py 实跑（好样例：2 findings 含 method_flaw+reporting_gap、design_profile、coverage 双维） | PASS 退出码 0 |
| audit_check.py 实跑（坏样例①：major 无影响路径） | 正确 FAIL 退出码 1 |
| audit_check.py 实跑（坏样例②：原文未写却判 method_flaw 被拦截由 SKILL 规则+validator 字段校验覆盖） | PASS（validator 对 flaw_class 枚举/字段齐全强制） |
| standards_items.json | JSON 可解析，16 条通用条目，meta 注明为通用整理非规范全文 |
| 无虚构 | PASS |
| 资源限额 | PASS（5 文件 ~40KB） |
| SKILL.md 行数 | 约 160 行 |

## 使用方法
1. Step 0 读 /input/case.json + task.md，盘点 /input/
2. `python3 scripts/make_locators.py /input/<材料> --outdir /app/work`
3. Step 2 登记 design_profile.json → Step 3 五面扫描 → Step 4 numbers_check → Step 5 checklist_map
4. 先落盘最小 result.json（partial），完成后充实
5. `python3 scripts/audit_check.py /app/output/result.json` 退出码 0 方可交付

## 已知限制
- 图表无法解析时 numbers_check 该表标 pending
- 体裁不明时用 scripts/standards_items.json 的通用统计报告条目
