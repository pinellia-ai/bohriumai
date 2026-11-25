---
name: experiment-feasibility-review
description: |
  对一份具体实验方案做七类约束（假设与变量、对照组、设备材料、时间成本、参数范围、
  风险与异常、伦理与安全）的逐项可行性审查，产出可勾选、可判定、可复核的审查表与量化评分。
  方法主线：逐检查项带原文定位判定 → 资源四状态核验（已具备/可外协/需采购/不具备）→
  时间与样本算术估算 → scripts/feasibility_score.py 量化打分 → 有条件可行结论写清条件。
  全程离线、只依据输入材料；方案没写 ≠ 方案满足；材料缺失如实标 gap，不虚构。
---

# 实验方案可行性评估 Skill

## 1. 用途与适用范围

- 输入：待审方案（文档/JSON，可能为多个版本化候选方案）+ 资源条件材料（设备清单、采购记录、报价单、SOP、审批表单、人员/排期表）。
- 输出：逐项审查表 + 量化可行性评分 + 可执行结论（可行/有条件可行/不可行，条件逐条可判定），落盘 `/app/output/result.json`。
- 适用：开工前审查（资源、时间、样本、伦理、安全、参数、风险七类约束）。不适用：方案科学创新性评价、实验执行、数据分析、正式伦理审批结论。
- 核心原则：**审查落到方案的具体章节、参数和清单行；"方案没写"记为 not_specified 而不是 satisfied；结论可执行；同一方案换人复跑可得到可比结论。**

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 `case_id`（原样保留）、任务说明、`output_contract` 全字段（提取到 `/app/work/00_contract_fields.json`）、材料清单。
2. 逐个读材料，建立 `/app/work/00_condition_base.json`（条件底账）：
   ```json
   {"equipment": [{"model": "...", "spec": "...", "available": true, "booking_wait_days": 0, "source": "<文件>:<位置>"}],
    "materials_supplies": [{"name": "...", "spec": "...", "lead_time_days": 0, "unit_price": null, "source": "..."}],
    "budget": {"total": null, "currency": "", "source": "..."},
    "personnel": {"count": 0, "skills": [], "source": "..."},
    "samples": {"available_n": null, "storage": "", "ethics_status": "", "source": "..."},
    "ethics_safety": {"animal": false, "human": false, "hazmat": false, "approvals": [], "source": "..."},
    "gaps": ["无报价单", "无排期表"]}
   ```
3. 多版本候选方案时，每个版本独立建档审查，不混合结论。
4. 材料缺失 → 该类条件记 `unknown`，对应检查项判定标 `indeterminate`，不默认满足。

验收断言：case_id 已记录；条件底账每类有 source 或在 gaps 中；未读内容不出现判定。

## 3. 工作流程（6步流水线）

### Step 1 建立检查项体系
用 `/app/work/checkitems.json`（可按案例微调，但七类必须齐）：

```json
{"categories": [
 {"cat": "假设与变量", "items": [
   {"item_id": "HV-1", "check": "假设可检验（有可测量因变量）",
    "how": "在方案中定位假设段，核对是否给出因变量操作定义与单位",
    "basis": "通则：不可测量即不可检验"}]},
 {"cat": "对照组", "items": [{"item_id": "CT-1", "check": "至少两类对照且与研究目标匹配", "how": "定位对照组清单", "basis": "通则"}]},
 {"cat": "设备材料", "items": [{"item_id": "EM-1", "check": "方案每个步骤的设备型号/规格在条件底账中存在且参数匹配", "how": "逐行比对步骤设备表与底账", "basis": "条件底账"}]},
 {"cat": "时间成本", "items": [{"item_id": "TC-1", "check": "步骤时长+等待周期+周转 ≤ 可用时间窗；预算 ≤ 上限", "how": "逐项求和后与约束比对（脚本算术）", "basis": "约束材料"}]},
 {"cat": "参数范围", "items": [{"item_id": "PR-1", "check": "每个关键参数在设备量程/材料耐限/安全阈值内且有依据", "how": "与底账量程逐项比对", "basis": "设备手册/安全阈值"}]},
 {"cat": "风险与异常", "items": [{"item_id": "RA-1", "check": "关键步骤有失败判据与处置路径", "how": "定位风险段核对", "basis": "通则"}]},
 {"cat": "伦理与安全", "items": [{"item_id": "ES-1", "check": "涉动物/人体/危化品时对应审批状态明确且未过期", "how": "比对审批表单", "basis": "伦理规范条目"}]}
]}
```
每项判定输出：`pass / fail / conditional / not_specified(方案没写) / indeterminate(条件不明) / na`。
验收断言：七类各 ≥1 项被实际判定；每条判定附 `plan_location`（方案中的章节/行/字段）与 `condition_source`（底账条目或缺失说明）。

### Step 2 逐项审查（先读方案，再对底账）
- 每条判定必须引用方案原文位置 + 条件底账条目；禁止无定位的意见。
- **方案没写的内容 → `not_specified`**，并在结论中列为需补充信息，绝不默认满足。
- 方案自相矛盾（如两处参数不同）→ 记 `contradiction`，引用两处位置。
- 判定阈值不确定（材料没给标准）→ 标 `indeterminate` + 写明缺什么。

### Step 3 资源四状态核验
对方案所需每项设备/耗材/人力输出状态：`已具备 / 可外协 / 需采购 / 不具备`，附依据：
```json
{"need": "恒温槽H(25-95°C)", "status": "已具备", "evidence": "底账 equipment[2] 量程匹配",
 "blocking": false, "action": "需排期确认", "wait_days": 3}
```
`不具备` 或 `需采购` 且货期超时间窗 → 标记 blocking，直接影响总评。

### Step 4 时间与样本算术估算
- 用 `scripts/feasibility_score.py --check-arithmetic` 或直接核对方案给出的估算：步骤时长求和、并行折算、样品数×单件时间、耗材量×单价求和。
- 每个估算可解释：数从哪来（方案原文/底账/常识折算，常识折算标 assumption）。
- 样本：方案需求量 vs 底账可得量 vs 伦理批件允许量三者比对，取最小值并指出谁卡脖子。

### Step 5 量化评分
运行 `python3 scripts/feasibility_score.py --review review.json`：
- 七类各 0-100 分：pass=100，conditional=60（附条件），not_specified=40，indeterminate=50，fail=0（blocking fail 直接 0），na 不计。
- 总分 = 加权（默认等权；案例给定权重则用案例权重）。
- 分级锚点：≥80 可行；60-79 有条件可行（条件=全部 conditional 项与 not_specified 关键项清单）；<60 不可行（列出 blocking 项）。
- **评分是排序与分级工具，不替代逐条结论；每条 conditional 的条件必须具体可判定。**

### Step 6 输出 result.json
先落最小骨架（case_id+status+output_contract 空壳）再充实。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "status": "success | partial | failed",
  "reviewed_versions": [{"version": "v1", "overall_score": 72, "verdict": "有条件可行"}],
  "final_verdict": {"verdict": "可行|有条件可行|不可行|无法判定", "conditions": ["条件1：xx≤yy，判定方式…"], "blocking_items": []},
  "checklist": [{"cat": "...", "item_id": "...", "verdict": "pass|fail|conditional|not_specified|indeterminate|na",
                 "plan_location": "<方案文件/章节/字段>", "condition_source": "<底账条目或gap>",
                 "reason": "...", "needed_action": "..."}],
  "resource_matrix": [{"need": "...", "status": "已具备|可外协|需采购|不具备", "evidence": "...", "blocking": false, "wait_days": 0}],
  "time_sample_estimate": {"total_min": 0, "critical_path_min": 0, "budget": 0, "samples": {"required": 0, "available": 0, "allowed": 0, "bottleneck": "..."}, "assumptions": []},
  "score": {"per_category": {"假设与变量": 0}, "weights": {}, "overall": 0, "grade": "..."},
  "evidence": [{"claim": "...", "source": "<文件>:<位置>", "quote": "原文"}],
  "uncertainty": [{"item": "...", "type": "not_specified|indeterminate|gap", "impact": "..."}],
  "confirmations_required": ["需专家/管理员/伦理委员会确认的事项"],
  "limits": "未覆盖事项与复跑说明（换人按 checklist 可复跑）"
}
```
- 完成标准：结论落到具体章节与参数；"有条件可行"的条件可判定；换人复跑得到可比结论。
- 不把未经确认的建议写成可执行事实 → 全部进 confirmations_required。

## 5. 数字门槛

- 七类全部有判定项（na 需说明理由）→ 否则 partial。
- 每条判定有 plan_location + condition_source → 否则该条作废重审。
- blocking fail ≥1 时 verdict 不得为"可行"。
- 评分由脚本算出，非手填。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 方案缺页/无法读取 | 记 gap，涉及项 not_specified，status=partial，limits 写明缺哪页 |
| 参数缺失 | 该项 indeterminate，列入需补充信息，不猜测 |
| 设备信息不明（型号对不上） | 记 contradiction/indeterminate，给匹配候选并列差异，转确认项 |
| 伦理状态未定 | ES 类全部 conditional，条件=取得批件；不得判 pass |
| 方案自相矛盾 | 引两处原文，标记 contradiction，verdict 至多为有条件可行 |
| 超长文档 | 按 output_contract 相关段落优先审；未审段落列 limits |
| 无预算/无报价材料 | TC 类降为 conditional（条件=补报价），price_missing 不猜价 |
| 多版本方案 | 每版独立评分与结论，可给对比排序但不混合条件 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 100% 映射
- [ ] 七类检查项全部判定，无默认满足
- [ ] 每条判定有方案位置 + 条件底账来源
- [ ] 资源四状态矩阵完整，blocking 项进 verdict
- [ ] 时间/样本/预算为算术结果，假设已列
- [ ] 评分来自脚本，分级与锚点一致
- [ ] conditional 条件可判定；confirmations_required 与可执行事实分离
- [ ] not_specified / indeterminate / gap 三类如实写入 uncertainty

## 8. 效率约束（64请求/900秒）

- Step0-1 两次响应内完成；Step2 逐类批量判定（每次一类）；Step5 脚本本地跑；输出组装 ≤2 次。
- 材料优先级：方案正文 > 设备清单 > 排期/审批 > 报价 > 其他。
- 第1次响应后先写 result.json 骨架。

## 9. 最小示例（示意，非正式案例结果）

输入：方案"用恒温槽H在80°C反应2h，样本n=50"；底账：恒温槽H量程25-95°C已具备（排期3天）、样本可得20只、无预算材料。
判定：PR-1 pass（80<95，底账equipment[2]）；TC-1 conditional（预算无报价，需补充）；样本 fail（50>20，blocking）→ verdict=不可行（样本量缺口30只）+ 给两条修复路径（降至20只并修改统计功效说明 / 补采购样本）。示意 status=success。
