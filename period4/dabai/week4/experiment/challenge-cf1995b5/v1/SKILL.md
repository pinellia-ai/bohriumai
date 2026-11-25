---
name: experiment-plan-generator
description: |
  把研究目标转成可排期、可执行、可复核的实验方案，并产出三个带变更记录的版本
  （v1初稿→v2修订→v3优化）。方法主线：假设-变量-对照-设备材料-时间成本-参数范围-风险异常
  七要素逐项落地，每条决策带依据与来源定位，参数与成本用 scripts/plan_check.py 做真实算术校验。
  全程离线、只依据输入材料；材料缺失如实标 gap，不虚构设备、报价与文献。
---

# 实验方案生成与优化 Skill

## 1. 用途与适用范围

- 输入：一个研究目标 + 约束条件 + 科研材料（设备清单、SOP、文献、历史记录、报价单等）。
- 输出：结构化实验方案（3个版本）+ 依据与风险 + 确认项，落盘为 `/app/output/result.json`。
- 适用：湿实验/计算实验的方案设计与迭代优化。不适用：数据分析建模、论文写作、文献综述、安全与伦理审批的正式结论（只列确认项）。
- 核心原则：**每条决策带依据；每个参数带单位、量程、来源；每个风险带判据与止损点。** 方案必须让实验人员能排期、能报价、能知道哪一步失败该改什么。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留，不改写）、任务说明、`output_contract` 全部字段、材料文件清单。
2. 逐个打开材料文件（实际读内容，不按文件名猜）：
   - 设备/参数材料 → 抽出设备型号、量程、精度、附件；
   - 报价/预算材料 → 抽出单价、币种、计价单位、货期；
   - SOP/历史记录 → 抽出参数依据、已知失败模式；
   - 文献 → 只抽与本目标直接相关的参数区间与判据，记录出处。
3. 盘点结果写入 `/app/work/00_material_inventory.json`：
   ```json
   {"case_id": "...", "materials": [{"path": "...", "type": "equipment|budget|sop|literature|history", "key_facts": ["型号X量程Y", "试剂Z单价N/瓶"]}], "missing": ["无预算材料", "无设备清单"]}
   ```
4. **材料缺失 → 对应要素标 `gap`，result.json 的 status 如实降级为 partial；不虚构。**

验收断言：case_id 已记录；output_contract 字段名列表已提取到 `/app/work/00_contract_fields.json`；每个材料有至少1条 key_fact 或出现在 missing 里。

## 3. 工作流程（7步流水线）

### Step 1 目标 → 可检验假设与变量
产出 `/app/work/10_hypotheses.json`，每个假设：
```json
{"h_id": "H1", "hypothesis": "在X条件下，Y随Z增加而单调上升",
 "iv": {"name": "Z", "operational_def": "用M方法测的Z浓度", "unit": "mM", "levels": [1, 2, 4, 8]},
 "dv": {"name": "Y", "operational_def": "用N方法测的产率", "unit": "%", "measurement": "HPLC外标法", "expected_direction": "increase"},
 "confounders": ["温度漂移", "批次差异"], "source": "材料<文件>:<位置> 或 gap"}
```
硬性要求：变量必须有操作定义、单位、取值水平；自变量、因变量、混杂因素三者齐全；没有材料支撑的操作定义标 `assumption` 并进确认项。
验收断言：每个假设 iv/dv/confounders 字段非空，levels 是具体数值或明确分类。

### Step 2 对照组设计
每个假设至少配齐两类对照（材料允许范围内）：
- 空白/基线对照（排除本底）；
- 阳性对照（证明体系能响应）或阴性对照（排除非特异效应）；
- 如自变量是多水平，用剂量梯度对照。
每条对照写明：`{group, purpose: "排除什么混杂", n: 样本数, cost_per_sample, basis}`。**只有一组对照 → 主动补设计并说明依据；体系材料不足以设阳性对照 → 标 gap 进确认项。**
验收断言：每条对照的 purpose 指向一个具体混杂因素，与 Step 1 的 confounders 对得上。

### Step 3 步骤 + 设备材料 + 时间成本绑定
每个步骤：
```json
{"step_id": "S1", "action": "...", "equipment": [{"model": "...", "qty": 1, "source": "材料<文件>:<位置>", "substitutable": true, "alt": "..."}],
 "reagents": [{"name": "...", "spec": "...", "qty_per_sample": "...", "source": "..."}],
 "duration_min": 30, "parallelizable": false, "depends_on": [], "operator_hours": 0.5}
```
然后运行算术核算（Step 6 脚本）：串行总时长 = Σ非并行步骤时长 + 关键路径；预算 = Σ(耗材单价×用量) + 机时费×时长 + 人力工日。**时间与预算必须由脚本算出，不手估。** 材料无单价 → 该项标 `price_missing` 进确认项，不猜价。
验收断言：每个步骤有 equipment/reagents/duration；总时长与总预算来自 plan_check.py 输出，数值可复算。

### Step 4 参数范围与依据
关键参数表 `/app/work/40_params.json`：
```json
{"param": "退火温度", "unit": "°C", "value": 55, "range": [52, 58], "out_of_range_action": "弃用本轮，回到55±1重跑",
 "basis": {"type": "sop|equipment_manual|literature|pretest|assumption", "location": "材料<文件>:<位置>", "text": "..."}}
```
硬性要求：参数值必须落在材料给出的设备量程/材料耐限/安全阈值内（脚本校验）；依据四选一注明；`assumption` 类参数不得超过1/3且全部进确认项。
验收断言：每个参数 basis.type != null；越界参数在脚本输出中为 FAIL，必须改值或降级为 partial。

### Step 5 风险与异常处置
对每步预判失败模式（污染、无信号、重复性差、样本不足、设备故障），每条：
```json
{"risk_id": "R1", "step": "S3", "failure_mode": "无信号", "trigger_criterion": "阳性对照读数<本底2倍",
 "stop_loss": "连续2轮触发→停线", "fallback": "改用B方案（依据：材料<文件>:<位置>）", "severity": "high|med|low"}
```
验收断言：trigger_criterion 是可判定的数值/规则，不是"注意观察"；每条有 fallback 或 stop_loss。

### Step 6 组装三版本 + 脚本校验
1. 组装 v1 初稿（七要素齐备）→ 运行 `python3 scripts/plan_check.py --plan v1.json --params 40_params.json --materials 00_material_inventory.json`。
2. 按校验报告修复（FAIL 项、算术错误、缺依据项）→ v2 修订，写变更记录 `changes: [{field, from, to, reason}]`。
3. 按约束做一轮优化（预算/时间超标→裁剪水平数或换并行；参数敏感→加密水平）→ v3 优化版，附优化依据与代价说明。
4. 三个版本都保留；result.json 主推最终版，前两版作为版本记录进 `plan_versions`。
验收断言：plan_check.py 对最终版全部 PASS（或如实 partial）；每个版本的 changes 链完整。

### Step 7 输出 result.json
按 §4 写 `/app/output/result.json`（先写最小骨架：case_id + status + output_contract 全字段空壳，再逐步充实；任何中断都有可评分产物）。

## 4. 输出契约

result.json 逐字段落实 case.json 的 output_contract；以下为必备骨架（字段名以 case.json 为准，一一映射，不得遗漏）：

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "plan_versions": [
    {"version": "v1", "plan": {...}}, {"version": "v2", "plan": {...}, "changes": [...]},
    {"version": "v3", "plan": {...}, "changes": [...]}
  ],
  "final_plan": {
    "hypotheses_variables": [],
    "controls": [],
    "steps": [],
    "parameters": [],
    "equipment_materials": [],
    "time_budget": {"serial_total_min": 0, "critical_path_min": 0, "budget_total": 0, "currency": "", "arithmetic": "由plan_check.py核算"},
    "readout_criteria": [],
    "risks": []
  },
  "evidence": [{"claim": "...", "source": "<文件>:<位置>", "quote": "原文关键句"}],
  "uncertainty": [{"item": "...", "type": "assumption|gap|price_missing", "impact": "...", "needs": "专家/采购/设备管理员确认"}],
  "confirmations_required": ["安全审批", "伦理", "设备排期", "专家确认项"],
  "change_log": "版本与参数变更记录",
  "limits": "本方案未覆盖/不能保证的事项"
}
```
- 依据与风险块：每个方案决策可指到材料位置；假设和边界可复核。
- 确认项块：未经确认的建议一律写进 confirmations_required，不写成可执行事实。
- 材料缺失、无法判断、运行失败分别写入 status/uncertainty/limits，三者分开说明。

## 5. 数字门槛

- 七要素覆盖：假设变量/对照/设备材料/时间成本/参数范围/风险异常/判读标准，每类 ≥1 条且非空壳 → 否则 status=partial。
- 对照 ≥2 类/假设；每参数有依据；时间与预算为脚本核算值；v1→v2→v3 变更链完整。
- plan_check.py 对最终版 FAIL=0（材料性 gap 除外）。
- 达不到门槛：status 如实降级 partial，limits 写明差在哪。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| case.json 或材料缺失 | status=failed，limits 写明缺什么，不编造 |
| 无设备参数/无报价 | 参数标 assumption、成本标 price_missing，进确认项；方案仍交付，注明需人工补价 |
| 时间窗与样本量冲突 | 出两版：裁样本量版 + 延时间窗版，都给算术依据，选择进确认项 |
| 依赖不可用（试剂缺货/设备排期满） | 启用 fallback 路径；无 fallback → 该步骤标 blocked，给替代采购/外协选项 |
| 约束互相矛盾（目标超出设备量程） | 不给越界方案；在 limits 说明矛盾，给最接近可行点 + 差距量化 |
| 材料过长读不完 | 优先读设备/预算/SOP三类；截断处标 gap，不猜内容 |
| 脚本报错 | 修复后重跑；连续失败则手算并标 manual_calculation，结果可信度降级说明 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段 100% 映射
- [ ] 每个变量有操作定义+单位+水平
- [ ] 每个假设 ≥2 类对照，purpose 指向具体混杂
- [ ] 每个步骤绑定设备型号/耗材规格/时长
- [ ] 时间与预算来自脚本核算，单位自洽
- [ ] 每个参数有值/单位/区间/越界处置/依据来源
- [ ] 每条风险有可判定触发判据+止损+fallback
- [ ] plan_check.py 最终版 FAIL=0；三版本变更链完整
- [ ] assumption/price_missing/gap 全部进 uncertainty 或 confirmations_required
- [ ] result.json 最小骨架已先落盘

## 8. 效率约束（64请求/900秒内完成）

- 请求预算分配：Step0-1 用1-2次；Step2-5 各1次批量生成；校验与修复共 ≤6次；输出组装2次。
- 材料优先级：output_contract > 设备/参数 > 预算 > SOP/历史 > 文献；超长材料只抽与关键参数相关的段落。
- 第1次模型响应后先写 result.json 骨架，之后每完成一步就更新。
- 不做：全文翻译文献、重复校验、生成多余版本（恰好3版）。

## 9. 最小示例（示意，非正式案例结果）

输入：目标"评估催化剂X在60-80°C对反应A的转化率影响"；材料：设备清单（恒温槽型号H，量程25-95°C±0.5）、试剂报价单。
输出（节选）：H1 假设 iv=温度(60/65/70/75/80°C, 恒温槽控温) dv=转化率(%); 对照：25°C基线 + 文献最优温度70°C阳性对照; S1步骤绑定恒温槽H; 预算=脚本算得 试剂¥1,240 + 机时8h; 参数80°C距量程上限15°C安全; R1风险=阳性对照无响应→触发判据→停线重配体系。示意输出标 status=success，confirmations_required 含"设备H排期需确认"。
