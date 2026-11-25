---
name: bounded-parameter-optimizer
description: |
  在设备量程、材料耐限、安全阈值与成本预算的硬约束内，产出可拿去开机的实验参数方案：
  关键参数表（建议值/可行区间/单位/依据）、响应指标口径、搜索策略与停止判据、成本时间预算。
  方法主线：从材料抽取有限参数域 → 约束感知可行域计算 → scripts/param_optimizer.py 在
  可行域内做真实算术搜索（网格/坐标/序贯）并核算成本 → 每条建议带来源与不确定度。
  全程离线；无可行解、约束冲突、数据缺失如实降级，不虚构预测值。
---

# 实验参数优化建议 Skill

## 1. 用途与适用范围

- 输入：研究问题 + 设备/材料/安全约束材料（手册、规格表、历史实验数据、预算）。
- 输出：可执行参数方案（关键参数+建议值+可行区间+响应指标+搜索策略+成本预算），落盘 `/app/output/result.json`。
- 适用：有界参数域内的参数寻优与权衡。不适用：无约束理论建模、设备采购决策本身、统计分析方法论研究。
- 核心原则：**建议参数必须落在真实可行域内；每条权衡有响应指标与成本口径支撑；候选点产生过程、每轮评估、停止判据可复跑复算。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id`（原样）、任务、`output_contract` 全字段（提取到 `/app/work/00_contract_fields.json`）、材料清单。
2. 抽取有限参数域 → `/app/work/00_domain.json`：
   ```json
   {"parameters": [{"name": "温度", "unit": "°C", "min": 25, "max": 95, "step": 5,
     "source": {"type": "equipment_manual|material_spec|safety|literature|history|assumption", "location": "<文件>:<位置>"}}],
    "constraints": [{"type": "device|material|safety|budget|time|throughput", "expr": "温度≤材料耐温80", "source": "..."}],
    "budget": {"total": null, "unit_price_refs": [], "source": "..."},
    "historical_data": [{"path": "...", "columns": [...], "n_rows": 0}],
    "gaps": ["无历史数据"]}
   ```
3. 历史数据实际读文件与列名，不按文件名猜内容；数据缺失标 gap。

验收断言：每个参数有 min/max/unit/source；约束有 source；无数据 → gaps 记录且后续预测全部标 assumption。

## 3. 工作流程（6步流水线）

### Step 1 关键参数识别
- 从研究问题出发列候选参数，按"对响应的影响×可控性×约束强度"筛出关键参数（通常 2-6 个），淘汰理由一句话。
- 每个参数：单位、下限、上限、步进、互斥关系（如 A 升则 B 上限降），依据类型+位置。
- 无依据的取值 → 标 assumption，全部进确认项。

### Step 2 可行域计算（脚本）
运行 `python3 scripts/param_optimizer.py --domain 00_domain.json --mode feasible`：
- 交集计算：各参数自身区间 ∩ 设备量程 ∩ 材料耐限 ∩ 安全阈值，处理互斥约束。
- 输出每个参数的可行区间与不可行区间来源（哪条约束卡掉的）。
- **可行域为空 → 直接走 Step 5 异常路径（约束冲突报告），不给越界建议。**

### Step 3 响应指标与预测
- 每个响应指标：口径（怎么测）、单位、可接受波动、测量方式。
- 有历史数据 → 用简单可复算的模型（线性回归/均值基线）拟合，脚本算出预测与残差，披露 R² 与不确定度；模型简单优先，禁止虚构预测精度。
- 无历史数据 → 预测标 assumption，建议值只给文献/手册区间中点+保守候选，不确定度标 high。

### Step 4 搜索策略与候选点（脚本）
运行 `python3 scripts/param_optimizer.py --domain 00_domain.json --objective objective.json --mode search`：
- objective.json：`{"response": "产率", "direction": "max", "model": {"type": "linear", "coefs": {"温度": 0.8}, "intercept": 10}}`（系数来自 Step 3 拟合或材料，来源注明）。
- 策略选择：≤3 参数且每轮成本高 → 分阶段筛选（粗网格→局部加密）；预算充足 → 全网格；有历史数据 → 以历史最优点为起点的序贯局部搜索。
- 停止判据（写死在脚本）：网格遍历完毕 或 连续 2 轮最优改进 < 1% 或 触达成本上限。
- 输出 Top-N 候选点：参数组合、预测响应（含区间）、每轮评估记录 `search_log`。

### Step 5 成本-响应权衡
- 每个候选点：机时=Σ步骤时长，耗材=Σ单价×用量（单价来自材料，缺价标 price_missing），样本数×通量→轮次与总时长。
- 成本受限时：给"响应损失-成本节省"曲线（脚本算），写明牺牲多少响应换多少成本可接受，取舍理由显式。
- 约束冲突/无可行解/指标矛盾：不硬给方案，输出冲突报告（哪两条约束、差距多大）+ 最接近可行点 + 降级选项（放宽哪条约束、需谁批准）→ 进确认项。

### Step 6 输出 result.json
先落最小骨架再充实。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "key_parameters": [{"name": "...", "unit": "...", "feasible_range": [lo, hi], "suggested_value": x,
                      "step": s, "basis": {"type": "...", "location": "..."}, "exclusion_reason_for_others": "..."}],
  "response_metrics": [{"metric": "...", "unit": "...", "measurement": "...", "tolerance": "...", "model": {"type": "...", "r2": 0, "uncertainty": "..."}}],
  "search_strategy": {"type": "grid|sequential|staged", "initial_points": [], "per_round_rule": "...", "stop_criteria": ["..."], "search_log": []},
  "recommendation": {"primary": {"params": {}, "predicted_response": {"value": 0, "interval": [0, 0], "confidence": "high|med|low"}, "machine_hours": 0, "cost": 0, "currency": "", "repeats": 0},
                     "alternatives": [{"params": {}, "tradeoff_note": "..."}]},
  "tradeoff_analysis": {"cost_response_curve": [{"cost": 0, "response": 0}], "acceptable_sacrifice": "..."},
  "conflict_report": {"conflicts": [], "nearest_feasible": {}, "relax_options": []},
  "evidence": [{"claim": "...", "source": "<文件>:<位置>", "quote": "..."}],
  "uncertainty": [{"item": "...", "type": "assumption|gap|price_missing|high_variance", "impact": "..."}],
  "confirmations_required": ["安全阈值确认", "设备排期", "专家确认"],
  "limits": "适用边界、模型假设、未覆盖事项"
}
```
- 实验方案块（假设/变量/对照/步骤/参数/资源/判读）融入 key_parameters + search_strategy + recommendation；依据与风险块=evidence+conflict_report；确认项块=confirmations_required。
- 无可行解/冲突时 status 如实降级，recommendation 为空并用 conflict_report 说明。

## 5. 数字门槛

- 每个建议值 ∈ 可行域（脚本校验 `--mode verify`）→ 否则该条作废。
- 每个参数/约束/单价有 source；预测带不确定度与模型类型。
- search_log 保留每轮评估，停止判据满足其一才停。
- 成本与单位口径自洽（脚本求和，不手估）。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 无可飞行解（参数域∩约束=∅） | conflict_report + 最接近可行点 + 放宽选项，status=partial |
| 约束冲突（目标温度>材料耐温） | 同上，引用两条约束原文，不给越界方案 |
| 数据缺失（无历史数据） | 预测标 assumption/high uncertainty，建议给区间而非单点 |
| 设备报错/参数越界提示 | 触发 out_of_range_action，回退到最近安全点，记录变更 |
| 指标互相矛盾（产率升纯度降） | 出 Pareto 前沿两个端点方案，选择进确认项 |
| 预算/单价缺失 | price_missing，成本列"待补价"项清单，不猜价 |
| 历史数据单位不一致 | 统一换算并记录换算式，换算不可靠则剔除该列并说明 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 100% 映射
- [ ] 参数域来自材料且带位置；可行域由脚本算
- [ ] 建议值全部落在可行域内（--mode verify 通过）
- [ ] 预测有模型类型+不确定度；无数据则标 assumption
- [ ] search_log 完整；停止判据明确且被执行
- [ ] 成本为脚本求和；price_missing 全部列出
- [ ] 冲突/无解/矛盾情形走 conflict_report，不硬给方案
- [ ] assumption/gap/price_missing 进 uncertainty + confirmations_required

## 8. 效率约束（64请求/900秒）

- Step0-1 两次响应；Step3 拟合、Step4-5 搜索与权衡全部本地脚本；模型响应主要用于抽参数域、定策略、写结论（≤10次）。
- 网格规模上限：脚本内置 max 20000 点，超出自动降为分阶段筛选。
- 第1次响应后先写 result.json 骨架。

## 9. 最小示例（示意，非正式案例结果）

输入：目标"最大化酶反应产率"；材料：恒温槽量程 25-95°C、底物耐温 ≤80°C、历史数据 20 行（温度-产率）、乙腈报价。
输出（节选）：可行域温度 [25,80]（80 上限来自材料耐限）；线性拟合 R²=0.87（脚本算得）；分阶段搜索：粗网格步长10→局部步长2；建议 72°C，预测产率 68±3%，机时 6h，成本 ¥412（脚本求和）；备选 65°C（产率-4%，成本-30%）；search_log 含 2 轮共 14 点，停止原因=改进<1%。示意输出标 status=success。
