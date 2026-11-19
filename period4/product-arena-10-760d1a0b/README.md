# literature-kg-builder — 阅读15｜文献知识图谱构建

> 波尔产品周赛第4期 · reading 赛道 · Skill 交付包使用与方法说明

## 1. 这是什么

围绕「阅读15｜文献知识图谱构建」的可调用 Skill（literature-kg-builder）：组织方为本题准备 3 个固定案例。每个案例包含任务说明、科研材料、必要的输入约束和评分所需的证据范围；案例会以相同内容分别交给基础 Agent 和加载参赛 Skill 的 Agent。你不需要自带正式测试案例，也不需要提交预先写好的答案。…

评测方式：安装至评测环境后，官方 DeepSeek Harness 在 3 个固定案例运行（64 请求/900秒/16384token），与基础 Agent 对照评分。本包不含预制答案。

## 2. 快速调用

- 触发："请按本 Skill 从文献抽取实体关系构建可查询知识图谱"
- 输入：`/input/case.json`（含 case_id、任务、材料位置、output_contract）+ 材料文件。
- 输出：`/app/output/result.json`（字段以 case.json output_contract 为最高优先）。

## 3. 方法概述

-  每个实体：`{entity_id, name(原文原词), type, locator(论文位置), mention_count}`。
-  只收论文真实出现的对象；泛化改写（"该材料"→ 具体名）需引用可定位处。
-  关系类型固定枚举：`uses | measures | improves | causes | compared_with | part_of | reports`（可按题目扩展）。
-  每条边：`{from, to, type, direction, condition(适用条件), evidence(原文短句), locator, certainty(direct | transcribed | inferred)}`。
-  **共现不当因果**：同段出现≠有关系；综述转述标 transcribed；推断标 inferred+依据。
-  同一对象多写法（缩写/大小写/全称）→ 归一主名，别名表登记；同名不同对象（如两个 "Adam"）→ 加限定后缀区分。

## 4. 契约速览

- case_id 原样；status ∈ success|partial|failed；关键结论带页码/段落/图表定位。
- gaps/uncertainty 诚实登记；partial 时已完成部分完整可交；不编造。

## 5. 异常速查

| 情况 | 处置 |
|---|---|
| 材料缺失/损坏 | status=failed 写明 |
| 定位失败 | 用章节+段落描述，标注不确定 |
| 预算不足 | 落盘 partial，gaps 列剩余 |
| contract 与本文件冲突 | 以 case.json output_contract 为准 |

## 6. 复用与版本

- v1（p4 首发）；自查清单见 SKILL.md §6。
