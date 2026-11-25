# challenge-cf1995b5 实验方案生成与优化 — v1 交付说明

## 交付标准清单（从题面提取）

- [x] SKILL.md：有效 YAML frontmatter（name/description），通用流程，无预制答案
- [x] 覆盖六类要素：假设与变量、对照组、设备材料、时间成本、参数范围、风险和异常（+判读标准）
- [x] 每条方案决策带依据（sop/equipment_manual/literature/pretest/assumption 五类来源 + 位置定位）
- [x] 时间成本/预算：由 scripts/plan_check.py 真实算术核算（串行总时长、关键路径、预算求和），不手估
- [x] 参数：值/单位/区间/越界处置/依据来源齐备；对照案例给的有限参数域做越界校验
- [x] 三版本候选方案（v1初稿→v2修订→v3优化）+ 变更链（组织方修订要求 "3 versioned candidate plans"）
- [x] result.json 骨架覆盖题面 output_contract 三块：实验方案 / 依据与风险 / 确认项 + case_id + status + uncertainty
- [x] 材料缺失标 gap、缺价标 price_missing、假设标 assumption，全部进确认项，不写成可执行事实
- [x] 异常处理表覆盖：无设备参数、时间/样本冲突、依赖不可用、约束矛盾、超长材料、脚本报错
- [x] 资源限额：3 个文件（SKILL.md/README.md/scripts 内 4 个），总量 <100KB

## 文件

- `SKILL.md` — Skill 本体（9 节：用途/输入识别/7步流水线/输出契约/数字门槛/异常表/自查清单/效率约束/最小示例）
- `scripts/plan_check.py` — 方案结构与算术校验器（Python3 标准库，无第三方依赖）
- `scripts/demo_plan.json`、`scripts/demo_params.json` — 最小自测输入（示意数据，非正式案例答案）

## 自测记录（2026-11-24）

1. YAML frontmatter 可解析（python yaml + 人工核对 name 与目录用途一致）✓
2. output_contract 对照：题面"Skill 运行后的输出要求"表 3 块内容全部映射到 result.json 骨架字段 ✓
3. plan_check.py：`ast.parse` 通过；demo 正例实跑 FAIL=0（serial=220min, critical path=220min, budget=660）；越界参数负例正确报 `param_out_of_own_range`；空方案 exit=1 ✓
4. 无虚构：不引用题面外接口；示例标注为示意 ✓
5. 资源限额：`find v1 -type f | wc -l` = 5 ≤ 50；总大小 <2MB ✓
6. SKILL.md 行数 ~170，在 150-400 区间 ✓
