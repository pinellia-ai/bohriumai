# challenge-ec02b694 实验参数优化建议 — v1 交付说明

## 交付标准清单（从题面提取）

- [x] 交付物是"可拿去开机的方案"：关键参数+建议值+可行区间+响应指标口径+搜索策略+成本时间预算
- [x] 建议参数落在真实可行域内：scripts/param_optimizer.py 计算 设备量程∩材料耐限∩安全阈值，verify 模式逐条校验
- [x] 关键参数、响应指标、搜索策略、实验成本四项全覆盖（+假设变量/对照/设备材料/时间成本/风险异常交代）
- [x] 每条权衡有响应指标与成本口径支撑：脚本求和成本，缺价标 price_missing
- [x] 搜索策略有收敛依据：停止判据写死（网格遍历完毕/改进<1%/触达上限），search_log 保留每轮评估
- [x] 候选产生过程可复跑：domain/objective 输入 JSON + 脚本确定性计算
- [x] 预测披露不确定度：有历史数据→脚本拟合（简单可复算模型）；无数据→标 assumption/high
- [x] 无可行解/约束冲突/指标矛盾 → conflict_report + 最接近可行点 + 放宽选项，不给越界方案
- [x] result.json 覆盖题面 output_contract 三块（实验方案/依据与风险/确认项）+ case_id + status + uncertainty
- [x] 异常表覆盖：无可行解、约束冲突、数据缺失、设备报错、指标矛盾、预算缺失、单位不一致

## 文件

- `SKILL.md` — Skill 本体（6步流水线：关键参数识别→可行域计算→响应指标与预测→搜索策略→成本权衡→输出）
- `scripts/param_optimizer.py` — 约束感知搜索器（feasible/search/verify 三模式，分阶段降级，Python3 标准库）
- `scripts/demo_domain.json`、`scripts/demo_objective.json` — 最小自测输入（示意数据，非正式案例答案）

## 自测记录（2026-11-24）

1. frontmatter 可解析（name=bounded-parameter-optimizer）✓
2. output_contract 对照：题面输出表 3 块内容映射到 key_parameters/search_strategy/recommendation/conflict_report/evidence/uncertainty/confirmations_required ✓
3. param_optimizer.py：ast.parse 通过。三模式实跑：
   - feasible：温度区间被 材料约束"温度<=80" 正确截断为 [25,80]，cut_by 记录约束来源 ✓
   - search：网格遍历得 best={温度:80, pH:4}, 预测66.0，stop_reason=grid_exhausted，search_log 完整 ✓
   - verify：温度=85 正确拒绝（exit=1）；可行点通过 ✓
   - 冲突路径：追加"温度<=20"约束后 feasible 模式正确报冲突 exit=1 ✓
4. 资源限额：5 文件 / <60KB；SKILL.md 约 180 行 ✓
5. 无虚构：示例标注示意；模型系数需注明来源，禁止编造精度 ✓
