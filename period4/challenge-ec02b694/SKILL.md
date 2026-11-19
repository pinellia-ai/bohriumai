---
name: parameter-optimizer
description: |
  实验参数优化建议 Skill。交付"能拿去开机"的方案：关键参数识别（牵制关系显式）、每个
  参数建议值+浮动区间+响应指标测量方法、搜索策略（单变量/正交/响应面，按预算选）、
  时间与成本估算。约束联合可行（设备量程/材料耐温/安全阈值不越界）；依据标注（文献/SOP/
  预实验）。
---

# Parameter Optimizer — 实验参数优化建议 Skill

## 1. 用途与适用范围

在相互牵制的量之间给出可执行取舍：温度↑转化率好看但副产物/能耗↑；采样密结论稳但成本翻倍；单参数最优联合不可行。交付不是解释，是**开机方案**。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、实验目标、已有数据/文献参数、约束（设备量程/材料耐温/安全阈值/预算机时）。
2. 建立参数清单：`{param, 当前值, 可调范围, 约束边界, 牵制关系}`。

## 3. 工作流程

### Step 1 关键参数识别
- 对目标指标影响大 + 存在牵制 → 关键参数；依据（文献/预实验/机理）标注。
- 牵制关系显式：`{参数A↑ → 指标↑ 但 参数B代价↑}`——联合可行域概念建立。

### Step 2 建议值与区间
- 每个关键参数：`{建议值, 浮动区间, 响应指标, 测量方法, 依据(文献[2]/SOP/预实验)}`。
- **联合可行**：建议值组合逐条过约束边界（量程/耐温/安全阈值），越界组合不出。

### Step 3 搜索策略
- 按预算选：单变量扫描（预算小）→ 正交设计（多参数）→ 响应面（需精细曲面）；给出试验点数、机时/成本估算、判优标准（响应指标+阈值）。

### Step 4 取舍说明
- 每个建议的代价明说：转化率 vs 副产物/能耗、采样密度 vs 成本——决策留给用户但利弊算清。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "parameter_optimization",
  "status": "success | partial | failed",
  "key_params": [{"param":"温度","current":30,"range":[25,45],"constraint":"材料耐温≤40°C","tradeoff":"↑转化率↑ / 副产物↑"}],
  "recommendations": [
    {"param":"温度","suggested":35,"float":"±2","response_metric":"转化率(%)","measure":"HPLC 定量",
     "basis":"文献[2] 在 35°C 报告最优；35<40°C 耐温边界","joint_feasible":true}
  ],
  "search_strategy": {"type":"orthogonal (L9)","trials":9,"cost":{"machine_hours":18,"reagents":"约X元"},"criterion":"转化率≥目标且副产物<阈值"},
  "tradeoffs": [{"choice":"温度35而非40","gain":"转化率+8%","cost":"副产物+3%、能耗+10%"}],
  "annotations": {"basis":["文献[2]","SOP-S12"],"assumptions":["线性响应区间"],"expert_confirm":["40°C 以上材料形变风险"]},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：recommendations 联合可行（过约束边界）；每条有 basis 与响应测量方法；search_strategy 含成本与判优；tradeoffs 利弊算清；专家确认项标注。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 约束边界材料缺失 | 范围按文献保守值 + needs_human_review |
| 无响应数据可依据 | 建议降级为搜索设计（先测基线） |
| 预算不足 | 关键参数+建议值优先（partial） |

## 6. 自查清单

1. [ ] 关键参数+牵制关系识别？
2. [ ] 建议值联合可行（越界组合未给出）？
3. [ ] 搜索策略含成本与判优标准？
4. [ ] 取舍利弊算清？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。参数清单与牵制图先行；建议值逐条过约束脚本化；策略按预算裁剪。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：数据/配置/日志/文献是事实依据；不编造数据、运行结果、软件状态。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/`（数据/图/代码文件 + result.json）。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：保留原始值、规则、结果、图表/代码和质量检查；每条结论带来源定位。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
