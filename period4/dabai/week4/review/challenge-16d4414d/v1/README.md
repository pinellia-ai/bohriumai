# challenge-16d4414d 论文逻辑与论证审查 — v1 交付说明

## 交付标准清单（从题面提取）

### output_contract / 产出字段（result.json 逐字段落实）
- `case_id` 原样；`status` success|partial|failed 含界限说明
- 审查报告：带位置、类型、严重度和建议的问题清单，覆盖论点、证据、推理链与章节衔接
- 依据与边界：原文摘录、对齐判定及待复核项；区分错误/证据不足/建议
- 结果状态：通过、问题、待复核、未检查项；不凭空补齐
- sources / uncertainty_notes / change_log

### 硬性要求
1. 报出的问题真实存在、能回到原文某一句话（file+locator+逐字quote）
2. 定位精确到评审可直接核对，不只给章节名
3. 修改建议可执行：说清补什么证据、改哪一句、把哪个结论强度降下来；空话建议不允许
4. 防误报：作者有意设置的对照、明确标注的假设情形、转述他人观点不得报为作者自相矛盾（claim_source 三分）
5. 跨章节主张-证据对应：引言承诺↔结果交付、摘要↔结论、方法↔结果口径、图表↔正文
6. 严重度分级依据可解释（是否影响主结论/可修正/影响复现性）
7. 预算 64 请求/900 秒/16384 token；≤50 文件/2MB；先落盘最小 result.json；截断风险如实标 partial
8. 提交目录根路径放 GITHUB_URL.txt

## 自测记录（2026-11-24，按 PLAYBOOK §4）

| 项 | 结果 |
|---|---|
| YAML frontmatter 可解析（name=logic-argument-audit） | PASS |
| output_contract 字段 100% 覆盖 | PASS |
| scripts ast.parse 语法 | PASS ×2 |
| make_locators.py 实跑 | PASS（同基准：合成稿件 5 段，退出码 0） |
| audit_check.py 实跑（好样例：3 claims（author×2+cited×1）、2 alignment、1 finding、6 consistency pairs、coverage 六类） | PASS 退出码 0 |
| audit_check.py 实跑（坏样例①：author_claim C002 未对齐） | 正确 FAIL 退出码 1 |
| audit_check.py 实跑（坏样例②：recommendation="建议加强逻辑" 空话拦截） | 正确 FAIL 退出码 1 |
| 无虚构 | PASS |
| 资源限额 | PASS（4 文件 ~35KB） |
| SKILL.md 行数 | 约 165 行 |

## 使用方法
1. Step 0 读 /input/case.json + task.md，盘点 /input/，做长度检查
2. `python3 scripts/make_locators.py /input/<材料> --outdir /app/work`
3. Step 2 抽主张 → claims.json；Step 3 对齐 → alignment.csv；Step 4 推理链 findings；Step 5 consistency.csv
4. 先落盘最小 result.json（partial），完成后充实
5. `python3 scripts/audit_check.py /app/output/result.json` 退出码 0 方可交付

## 已知限制
- 引文原文不在 /input 时对齐判 undeterminable
- 图表无法读取时相关一致性对标 pending
