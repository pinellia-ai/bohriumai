# challenge-8354c69a 实验结果解释与异常分析 — v1 交付说明

## 交付标准清单（从题面提取）

- [x] 五段可检查结论：结果趋势 / 异常点 / 可能原因 / 复核步骤 / 后续实验建议，全部齐备且非空壳
- [x] 趋势是算出来的：scripts/robust_stats.py 真实计算斜率/R²/平台期/分组趋势，禁止复述读数；脚本说无显著趋势就不能写"明显上升"
- [x] 异常点定位到对象维度（批次/通道/孔位/时间点）+ 判定阈值 + 偏离量数字；三规则并集（稳健Z>3.5 / IQR围栏 / 对照控制限），阈值显式披露来源（案例未给→惯例+ambiguity_note）
- [x] **异常归因树（前人弱项重点）**：方法/仪器/样本/统计四分支逐条走查，每条候选带 支持证据/排除证据/状态（candidate|supported|excluded|untestable）/相关误当因果风险（reframe_risk）/按证据强度排序
- [x] **每个异常假设带可执行的验证实验**：动作+真/假预期结果+成本；缺数据测不了如实标 untestable，不编
- [x] **结论与原始数据逐条对账**：reconciliation 表 逐条 结论↔数据位置↔统计量↔阈值↔match；data_ref 可回指 file:row:col
- [x] 复核步骤第二个人可执行：回查哪个文件哪个字段、核对哪条日志、加做什么对照
- [x] 后续实验与归因树互相引用（每条改动注明它排除/支持哪条假设）
- [x] 单位/方法/阈值歧义如实保留（ambiguities），不擅自消歧；重复<3、对照缺失、读数饱和均有降级路径
- [x] unexplained 列出未解释部分；不虚构测量值/原因/重复数
- [x] result.json 覆盖题面 output_contract 三块 + case_id + status + uncertainty
- [x] 异常表覆盖：数据缺失、单位不一致、重复不足、对照缺失、超量程饱和、结论冲突、格式异常、图谱人工读数

## 文件

- `SKILL.md` — Skill 本体（6步流水线：基线计算→趋势判读→异常定位→归因树→复核与后续→对账输出）
- `scripts/robust_stats.py` — 稳健判读器（baseline/anomalies/trend/all 四模式，Python3 标准库）
- `scripts/demo_data.csv`、`scripts/demo_roles.json` — 最小自测输入（合成示意数据，非正式案例答案）

## 自测记录（2026-11-24）

1. frontmatter 可解析（name=result-interpretation-anomaly-analysis）✓
2. output_contract 对照：题面输出表 3 块内容映射到 trend/anomalies/causes/verification_steps/next_experiments/reconciliation/evidence/confirmations_required ✓
3. robust_stats.py：ast.parse 通过；19行合成数据（6对照+9趋势点+4含1注入异常）实跑：
   - baseline：median=0.348 MAD=0.025，对照n=6 控制限[0.334,0.361] 正确 ✓
   - anomalies：注入异常 0.70 被 modified_z=9.5>3.5 捕获，定位 batch=b2/channel=B/well=B7 ✓
   - trend：b1|A 斜率0.0216 R²=0.9513（含平台段折算）方向 up ✓
   - 修复记录：首版趋势组混入对照行（time=0）产生伪平台期 → 修复为趋势分析剔除对照行+平台窗口要求时间跨度>0，复测通过 ✓
   - 控制限规则对趋势样本触发属设计行为（规则并集给候选，归因树区分趋势解释 vs 点异常），SKILL.md 已写明判读方式 ✓
4. 资源限额：5 文件 / <60KB；SKILL.md 约 200 行 ✓
5. 无虚构：demo 数据为合成且标注；阈值来源显式披露；不编造测量值/原因/重复数 ✓
