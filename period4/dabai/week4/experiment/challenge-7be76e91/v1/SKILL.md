---
name: plan-comparison-selector
description: |
  把 2-N 个候选实验方案摆到同一张可比矩阵上，完成横向比较并给出可辩护的选择：
  统一比较口径 → 硬约束淘汰 → 加权评分（成本/时间/可行性/风险/证据五维）→
  scripts/compare_plans.py 真实算术计分+权重敏感性分析 → 选择结论带证据挂载与舍弃理由。
  全程离线、只依据输入材料；每个判断挂来源；候选全部不可行时如实报告，不硬选。
---

# 实验方案比较与选择 Skill

## 1. 用途与适用范围

- 输入：2-N 个候选实验方案（文档/JSON，可能已版本化）+ 评价标准与硬约束 + 资源材料（报价单、设备清单、排期、预实验记录）。
- 输出：统一可比矩阵 + 加权评分与敏感性分析 + 可辩护选择结论（含每个被舍弃方案的具体理由），落盘 `/app/output/result.json`。
- 适用：同一实验目标下多条路线的横向比较与选型。不适用：单一方案的设计创新、数据统计分析、文献综述。
- 核心原则：**先固定比较口径再逐案填表；数字统一口径（机时/耗材/人力/一次性 vs 按次）；每个判断挂证据来源；结论强度靠证据不靠语气。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id`（原样）、任务、`output_contract` 全字段（提取到 `/app/work/00_contract_fields.json`）、材料清单。
2. 读全部候选方案与资源材料，建立 `/app/work/00_comparability_base.json`：
   ```json
   {"plans": [{"plan_id": "A", "version": "v2", "path": "...", "one_line": "..."}],
    "hard_constraints": [{"id": "HC1", "expr": "总预算≤5000", "source": "<文件>:<位置>"}],
    "evaluation_criteria": {"dimensions": ["质量与证据", "成本", "时间", "可行性", "风险"],
                            "weights": {"质量与证据": 0.35}, "source": "案例给定或标注 assumption"},
    "unit_costs": [{"item": "乙腈", "price": 120, "per": "L", "source": "报价单:L2"}],
    "resource_base": {"equipment": [], "booking_wait_days": {}, "gaps": []}}
   ```
3. 权重无材料依据 → 标 assumption 并做全档敏感性（见 Step 4）；材料缺失记 gaps。

验收断言：每个 plan 有 plan_id 与出处；每条硬约束有 source；权重来源注明。

## 3. 工作流程（5步流水线）

### Step 1 统一比较口径
固定可比字段（每个方案都填同一套，缺的填 `n/a+原因`，不许各用一套结构）：
```json
{"field": "总成本", "unit": "元", "components": ["耗材", "机时费", "人力工日", "样品制备"], "one_time_vs_recurring": "区分"}
```
必填字段组：目标一致性 / 自变量与因变量 / 对照设置 / 关键参数与区间 / 设备需求 / 耗材需求 / 样本需求 / 总机时 / 总成本（含构成）/ 关键路径时长 / 风险清单 / 证据强度（文献/预实验/none）。
- 成本口径：机时、耗材、人力、样品准备、排期等待、返工预留（建议 15%）分别列，区分一次性投入与按次消耗；单价来自材料，缺价标 price_missing 不猜。
- 时间口径：执行时长 + 样品准备 + 设备排期等待 + 表征排队 + 返工，都算进总时长。

### Step 2 硬约束淘汰
逐方案核对硬约束（脚本算术：总成本求和、总时长求和、参数区间比对）：
- 违反硬约束 → 淘汰，写明违反哪条、差距多少（淘汰也要有数字）。
- 全部违反 → 不硬选，输出 conflict_report（见 §6）。

### Step 3 填矩阵与评分
- 每个字段填实际值 + 来源位置；主观分（如证据强度）用锚点：文献直接支持=3 / 预实验支持=2 / 仅理论推断=1 / 无=0。
- 运行 `python3 scripts/compare_plans.py --matrix matrix.json`：
  - 归一化（min-max 或锚点分），硬约束过滤，加权总分，输出排序与分差。
  - **敏感性分析**：每个权重 ±20% 重算排序，输出"排序翻转载荷点"——哪个权重变到多少名次会换；结论若对权重敏感 → 降级为"条件选择"。

### Step 4 可辩护选择
结论必须含三件套：
1. **选择**：得分最高的可行方案 + 分差数字。
2. **舍弃理由**：每个被舍弃方案一句具体理由，指向矩阵中最大失分字段与数字（如"B 总成本 ¥8,420 超硬约束 HC1 上限 68%"）。
3. **敏感性说明**：权重在什么范围内结论稳定、在什么范围翻转让给谁。
- 并列或分差 <5% → 给条件选择（什么条件下选 A，什么条件下选 B），条件可判定。

### Step 5 输出 result.json
先落最小骨架再充实。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "comparability_fields": [{"field": "...", "unit": "...", "components": [], "source": "..."}],
  "matrix": [{"plan_id": "A", "fields": {"总成本": {"value": 0, "source": "...", "missing": false}}, "hard_constraints_passed": true}],
  "eliminated": [{"plan_id": "B", "reason": "违反HC1", "gap_quantified": "超68%"}],
  "scores": {"weights": {}, "weighted_totals": {"A": 0}, "ranking": [], "sensitivity": [{"dimension": "成本", "flip_point": "..."}]},
  "decision": {"selected": "A", "margin": 0, "abandon_reasons": [{"plan_id": "B", "reason": "...", "evidence": "<文件>:<位置>"}],
               "conditional": null, "defense": "敏感性范围内结论稳定"},
  "risk_comparison": [{"plan_id": "A", "risks": [{"mode": "...", "trigger": "...", "severity": "...", "mitigation": "...", "fallback": "..."}]}],
  "evidence": [{"claim": "...", "source": "<文件>:<位置>", "quote": "..."}],
  "uncertainty": [{"item": "...", "type": "price_missing|assumption|gap", "impact": "..."}],
  "confirmations_required": ["设备排期", "报价确认", "专家确认"],
  "limits": "未比较的维度与不适配情形"
}
```
- 七类字段（目标/变量/对照/参数/资源/风险/证据）融入 comparability_fields + matrix；依据与风险=evidence+risk_comparison；确认项=confirmations_required。

## 5. 数字门槛

- 矩阵字段覆盖率：每方案 ≥90% 字段有值或显式 n/a+原因。
- 数字字段（成本/时长）为脚本求和，口径一致；缺价项单独列出。
- 评分与敏感性由脚本输出；结论分差 <5% 必须给条件选择。
- 每条舍弃理由有量化差距或最大失分字段。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 全部候选违反硬约束 | status=partial，输出 conflict_report：各方案差距量化 + 最接近可行者 + 放宽选项（需谁批准） |
| 候选方案结构各不相同 | Step 1 口径先行，缺字段填 n/a+原因，不许跳过 |
| 设备不可得 | 该方案可行性维扣分 + 排期等待计入总时长；blocking 则按硬约束淘汰 |
| 耗材超预算 | 同上；超支比例量化写进淘汰/降级理由 |
| 参数窗口冲突 | 记 contradiction（引两处位置），该方案最多条件选择 |
| 单价/机时费缺失 | price_missing，成本比按已知项做 + 说明口径缺口，不猜价 |
| 权重无依据 | 全档敏感性（±20% 及等权），结论按敏感性表述 |
| 证据全为理论推断 | 证据强度=0，结论加"需预实验确认"条件 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 100% 映射
- [ ] 所有方案同一套可比字段，缺项显式 n/a+原因
- [ ] 成本/时长口径统一且脚本求和；一次性 vs 按次区分
- [ ] 硬约束淘汰带量化差距；评分来自脚本
- [ ] 敏感性分析完成；<5% 分差给条件选择
- [ ] 舍弃理由逐方案具体化，带最大失分字段与数字
- [ ] 每个判断挂来源位置；price_missing/assumption 进 uncertainty
- [ ] 风险逐方案列触发条件/后果量级/缓解/回退

## 8. 效率约束（64请求/900秒）

- Step0-1 两次响应；矩阵填写每方案一次响应；评分与敏感性本地脚本；输出组装 ≤2 次。
- 候选 >4 个时先按硬约束粗筛再细评；材料超长只读与评价字段相关段落。
- 第1次响应后先写 result.json 骨架。

## 9. 最小示例（示意，非正式案例结果）

输入：目标"测聚合物弯曲模量"；候选 A（三点弯曲法，自有万能机）与 B（DMA 法，需外协排队）。
输出（节选）：统一字段后 A 总成本 ¥320/批（自有设备+耗材），B ¥1,150/批（外协机时费）；A 总时长 2 天，B 9 天（含 7 天排队）；评分 A=4.12 B=3.65（脚本），敏感性：证据权重升至 0.5 时翻转为 B（文献支持更强）；选择 A，舍弃理由=B 总时长超时间窗 3 天（引排期表）；并列风险清单。示意输出标 status=success。
