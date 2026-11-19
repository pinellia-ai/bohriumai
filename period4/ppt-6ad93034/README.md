# slide-gen-editor-iterative — 学术 PPT 生成与编辑

> 波尔产品周赛第4期 · Skill 交付包使用与方法说明（文档与 Skill 同版本）

## 1. 这是什么

围绕「学术 PPT 生成与编辑」构建的可被 Agent 调用的 Skill（slide-gen-editor-iterative）：按 SKILL.md 定义的工作流，在平台固定案例上完成实际任务，交付可独立复核的结果，全程保留来源定位与不确定性说明。核心方法：page skeleton with narrative roles…

平台评测方式：本 Skill 被安装到评测环境的 skill 目录，官方 DeepSeek Harness 在 3 个固定案例上运行（64 次模型请求 / 900 秒 / 单响应 16384 token 预算），与不加载 Skill 的基础 Agent 对照评分。本包不含、也不需要预制答案。

## 2. 快速调用

- 触发语句示例："请按本 Skill 从材料生成页面骨架，或按指令编辑指定页并保留版本记录"
- 输入：`/input/case.json`（含 case_id、任务说明、材料位置、output_contract）+ 题目材料文件。
- 输出：/app/output/（deck.pptx + deck.pdf + result.json）（字段以 case.json 的 `output_contract` 为最高优先，缺省时按 SKILL.md §4 结构）。
- 过程产物：`/app/work/`。

## 3. 方法概述（与 SKILL.md 一致）

- page skeleton with narrative roles
- four edit modes (compress/expand/retarget/translate) with terminology lock
- figure insertion separating redraw-from-data vs original-image
- per-round version snapshots with revert paths and declared delivery version
- master/theme untouched, export never breaks.

## 4. 输入输出契约速览

- `case_id` 原样保留；`status ∈ success | partial | failed`；证据定位到论文章节/图表号/材料位置。
- `gaps`：材料缺失项——只登记，不构造。
- `uncertainty_notes`：无法判定项；`changes`：取舍与修改记录。
- 部分完成时 status=partial：已完成部分完整可交，未完成项列明剩余工作量。

## 5. 异常处理速查

| 情况 | 处置 |
|---|---|
| 输入缺失/损坏 | status=failed 写明缺失项；不编造 |
| 材料与任务约束冲突 | 以实际材料为准，冲突登记 uncertainty_notes |
| 预算不足 | 落盘 partial，gaps 列剩余项 |
| 输出 contract 与本文件冲突 | 以 case.json 的 output_contract 为准 |

（完整异常表见 SKILL.md §5）

## 6. 复用与再跑

- 依赖：仅评测环境预装工具；本包全部为 UTF-8 文本资源。
- 再跑：按 SKILL.md §3 工作流以相同输入重跑即得一致结构结果。
- 自查：输出前按 SKILL.md 自查清单逐条核对；`python3 -m json.tool result.json` 验证。

## 7. 版本与维护

- 版本：v1（p4 首发，含运行时硬性契约段）。
- 维护：契约变更、材料 schema 变化时同步修订 SKILL.md 与本文件。
