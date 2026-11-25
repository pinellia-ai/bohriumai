# challenge-2e2c5820 实验方案可行性评估 — v1 交付说明

## 交付标准清单（从题面提取）

- [x] SKILL.md：有效 YAML frontmatter，通用流程，无预制答案
- [x] 七类约束逐项审查：假设与变量、对照组、设备材料、时间成本、参数范围、风险与异常、伦理与安全
- [x] 审查落到方案具体章节/参数/清单行：每条判定必须带 plan_location + condition_source
- [x] "方案没写 ≠ 满足"：not_specified 独立判定态，列入需补充信息
- [x] 结论可执行：可行/有条件可行/不可行；conditional 的条件具体可判定
- [x] 资源四状态核验：已具备/可外协/需采购/不具备，blocking 项影响总评
- [x] 时间与样本算术估算：脚本求和复核，假设显式列出；样本"需求 vs 可得 vs 批件允许"三方比对
- [x] 量化评分：scripts/feasibility_score.py，七类分级计分+加权+blocking 压制，同一方案复跑结果一致
- [x] result.json 覆盖题面 output_contract 三块（实验方案/依据与风险/确认项）+ case_id + status + uncertainty
- [x] 异常表覆盖：方案缺页、参数缺失、设备信息不明、伦理状态未定、方案自相矛盾、超长文档、无报价、多版本
- [x] 复跑性：判定阈值与计分规则写死在脚本与 SKILL.md 中，换人可复算

## 文件

- `SKILL.md` — Skill 本体（6步流水线：检查项体系→逐项审查→资源四状态→算术估算→量化评分→输出）
- `scripts/feasibility_score.py` — 量化评分器+算术复核（Python3 标准库）
- `scripts/demo_review.json` — 最小自测输入（示意判定，非正式案例答案）

## 自测记录（2026-11-24）

1. frontmatter 可解析，name=experiment-feasibility-review ✓
2. output_contract 对照：题面输出表 3 块内容全部映射 ✓
3. feasibility_score.py：ast.parse 通过；demo 实跑：7 类计分正确（pass=100/conditional=60/not_specified=40/fail=0），blocking fail 将 overall 压至 59.9 → grade=不可行，blocking 列表与 condition_list 正确；--check-arithmetic 复核外部方案得 total_min=220/budget=660（与该方案独立核算一致）✓
4. na 项不计入分母；无评分时输出 grade=无法判定 ✓
5. 资源限额：4 文件 / <40KB ✓；SKILL.md 约 170 行 ✓
6. 无虚构：示例标注示意；不引题面外接口 ✓
