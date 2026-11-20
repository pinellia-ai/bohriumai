---
name: protocol-compare-selector
description: |
  实验方案比较与选择 Skill。同一目标 3-5 条可行路线的**可辩护比较**：统一维度（设备机时/
  耗材成本/参数窗口/风险等级/证据强度）逐路线打分，权重与决策标准先声明；给出选择+具体
  舍弃理由（每条被弃路线输在哪）；不偏好不敷衍。方案依据/假设/需专家确认项标注。
---

# Protocol Compare & Select — 实验方案比较与选择 Skill

## 1. 用途与适用范围

"最后需要一个可辩护的选择，以及一个具体的舍弃理由"：维度统一 → 打分透明 → 选择可辩护 → 舍弃有据。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、实验目标、候选路线（3-5 条）、约束与偏好。
2. **决策标准前置**：`{维度, 权重, 判定规则}` 版本化——先定标准后比较（避免为偏好选路线而调权重）。

## 3. 工作流程

### Step 1 统一维度打分
- 五维：设备机时 / 耗材成本 / 参数窗口（可行范围宽窄）/ 风险等级 / 证据强度（预期结论的可信度）。
- 每路线每维：`{score, 依据(材料内证据/文献/估算)}`——依据引用具体文档。

### Step 2 加权比较
- 加权总分 + 维度短板提示（某路线某维极差即使总分高也要警示）。
- 敏感性：换权重（如成本敏感 vs 证据敏感）排序是否翻转——翻转时明示两种结论。

### Step 3 选择与舍弃
- 选择：`{选定路线, 决定性优势}`；**每条被弃路线给具体舍弃理由**（输在哪个维度、差多少），不敷衍（"综合考虑不选"不合格）。
- 可辩护性自检：他人按同一标准能否复现同一选择？

### Step 4 标注
- 方案依据（文献/SOP）、假设（估算前提）、需专家确认项（如成本估算、风险评级）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "protocol_comparison",
  "status": "success | partial | failed",
  "criteria": [{"dim":"cost","weight":0.3,"rule":"耗材+机时折算","version":"v1"}],
  "routes": [
    {"route":"R1 化学法","scores":{"machine_hours":2,"cost":4,"param_window":3,"risk":3,"evidence":4},
     "basis":{"cost":"报价单p1","risk":"文献[2]报告成功率70%"},"total":3.2},
    {"route":"R2 酶法","scores":{...},"total":3.8}
  ],
  "sensitivity": {"cost_weight_doubled":"R1 反超——两种结论均列出","flips":true},
  "selection": {"chosen":"R2 酶法","deciding_advantage":"参数窗口宽+证据强度高",
                "discarded_reasons":[{"route":"R1","lost_on":"成本(4→高)与风险(70%成功率)","diff":"加权差0.6"},
                                      {"route":"R3","lost_on":"机时翻倍","diff":"时间约束不满足"}]},
  "annotations": {"basis":["文献[2]"],"assumptions":["成本按报价单估算"],"expert_confirm":["R3 安全等级评估"]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：criteria 版本化前置；每维有依据；sensitivity 翻转明示；discarded_reasons 逐条具体；专家确认项标注。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 路线信息缺失 | 该维 unknown + 总分降级处理 |
| 两路线并列 | 敏感性分析给条件化建议 |
| 预算不足 | 打分表先行（partial） |

## 6. 自查清单

1. [ ] 标准前置版本化？五维统一？
2. [ ] 每维打分有依据？
3. [ ] 敏感性翻转明示？
4. [ ] 舍弃理由逐条具体？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。标准与打分表先行；敏感性脚本化；选择论证最后组装。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
