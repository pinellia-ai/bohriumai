# challenge-7be76e91 实验方案比较与选择 — v1 交付说明

## 交付标准清单（从题面提取）

- [x] 多个候选方案摆到同一张可比矩阵：Step 1 先固定统一口径字段（目标/变量/对照/参数/设备/耗材/样本/机时/成本/时长/风险/证据强度），缺项显式 n/a+原因，禁止各用一套结构
- [x] 成本口径统一：机时+耗材+人力+样品准备+排期等待+返工预留分别列，区分一次性 vs 按次；缺价标 price_missing 不猜
- [x] 时间口径完整：执行+准备+设备排期+表征排队+返工全算进总时长（前人失败点针对性覆盖）
- [x] 硬约束淘汰：淘汰也带量化差距（违反哪条、超多少）
- [x] 加权评分+敏感性分析：scripts/compare_plans.py 归一化计分；每维权重±20%重算，输出翻转点；分差<5%强制条件选择
- [x] 可辩护选择三件套：选择+分差数字、逐方案具体舍弃理由（指向最大失分字段）、敏感性稳定范围说明
- [x] 证据挂载：锚点分级（文献=3/预实验=2/理论=1/无=0），每个判断带来源位置
- [x] 风险逐方案：触发条件/后果量级/缓解/回退，区分可接受风险与不可行
- [x] 全部候选不可行 → conflict_report 不硬选
- [x] result.json 覆盖题面 output_contract 三块 + case_id + status + uncertainty
- [x] 异常表覆盖：设备不可得、耗材超预算、参数窗口冲突、全部不可行、结构不一致、价格缺失、权重无依据

## 文件

- `SKILL.md` — Skill 本体（5步流水线：统一口径→硬约束淘汰→矩阵评分→可辩护选择→输出）
- `scripts/compare_plans.py` — 归一化加权评分+硬约束过滤+权重敏感性（Python3 标准库）
- `scripts/demo_matrix.json` — 最小自测输入（示意数据，非正式案例答案）

## 自测记录（2026-11-24）

1. frontmatter 可解析（name=plan-comparison-selector）✓
2. output_contract 对照：题面输出表 3 块内容映射到 matrix/scores/decision/risk_comparison/evidence/confirmations_required ✓
3. compare_plans.py：ast.parse 通过。三组实跑：
   - 3方案demo：A=91.67 > B=31.67，C 因 hard_fail 正确淘汰并记录原因；margin=60 无需条件选择 ✓
   - 接近场景：flip 检测在并列时正确输出（成本-20%→B、时长+20%→B）✓
   - 归一化方向（min/max）与锚点分（0-3）换算正确 ✓
4. 资源限额：4 文件 / <50KB；SKILL.md 约 170 行 ✓
5. 无虚构：示例标注示意 ✓
