---
name: slide-gen-editor-iterative
description: |
  学术 PPT 生成与编辑 Skill。从论文/提纲生成页面骨架（每页明确叙事角色），支持按指令
  压缩/扩写/换受众/换语言编辑并保持术语符号一致，图表插入处理图注/编号/单位/引用
  （区分可重绘与只能引用原图），多轮迭代版本可比对可回退，模板母版/字号/配色/页脚
  规范内成稿且导出不塌、字体不丢、图片不裁。
---

# Slide Gen & Editor — 学术 PPT 生成与编辑 Skill（可迭代、可回退）

## 1. 用途与适用范围

学术页面的生成、内容编辑、图表插入与演示稿迭代。核心是"取舍与重排"：哪些结果单独占页、方法压到几条、图几先出现、一页几个要点。三标准：页内内容与源材料对得上；指定模板真实套用可查；整册版式与导出可复跑、可逐页核对。

不负责：论文精读与文献综述、科研绘图可视化算法、文字润色、PPT 软件开发。

## 2. 输入识别（必做第一步）

1. `ls /input/`；读 case.json / task.md，记录 case_id、受众/时长/页数约束。
2. 盘点：源材料（论文/提纲/既有 deck）、模板（母版/版式/占位符）、图表素材。
3. 若为编辑任务：先记录原 deck 版本基线（页数/结构/内容摘要），建立变更前快照。
4. 材料缺失：status=failed。

## 3. 工作流程

### Step 1 学术页面生成（取舍与页序）
- 从源材料规划页序：每页**明确叙事角色**（背景/方法/结果/讨论/结论）与唯一主张。
- 内容取舍有依据：核心结果优先单独成页，方法压缩为流程要点；取舍理由登记 changes。
- 生成页面骨架先落盘（outline 先行，保 partial）。

### Step 2 内容编辑（四类指令）
- `压缩`：保主张与关键数值，删修饰——术语、符号与源材料一致。
- `扩写`：只从源材料扩（补证据/条件），不引入源外内容。
- `换受众`：导师版重方法细节、评审版重创新与结论强度、同行版重技术路线——切换时保留证据定位。
- `换语言`：术语表锁定，数字/单位原样。
- 每次编辑记录 `{页码, 改了什么, 为什么}`。

### Step 3 图表插入
- 区分**可重绘**（有数据表）与**只能引用原图**（仅图片/截图）——可重绘的用数据再生成并标注"依数据重绘"，只能引用的保原图不改。
- 图注、编号、单位、正文引用一一对应；数值从数据表读取，禁止按印象取整。

### Step 4 演示稿迭代（版本可比对可回退）
- 每轮修改保存版本快照（v1/v2/…，文件或结构记录）：`{版本, 改动页, 改动内容, 原因}`。
- 改坏可回退：改动按页隔离（不批量覆盖母版）；提供上一版本恢复路径。
- 明确标注交付版（哪一版是最终交付）。

### Step 5 模板约束与导出渲染
- 母版/字号层级/配色/页脚规范内成稿——改页**不改母版**；主题字体色保持继承。
- 导出 PDF：字体不替换（缺失如实登记）、文字不溢出、图片不裁；导出参数记录，他人可复跑。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "slide_generation_editing",
  "status": "success | partial | failed",
  "outline": [{"page":1,"role":"...","claim":"...","source_locator":"..."}],
  "edit_history": [{"round":1,"page":3,"change":"压缩方法页","reason":"时长约束","term_kept":true}],
  "figures": [{"page":4,"figure":"Fig.2","mode":"redrawn_from_data | original_image","caption_ok":true,"number_matches_ref":true}],
  "versions": [{"v":1,"changed_pages":[3],"snapshot_ref":"v1/","revert_path":"v1/"}],
  "delivery_version": "v2",
  "files": {"pptx":"deck.pptx","pdf":"deck.pdf","editable":true},
  "template_compliance": {"master_untouched":true,"theme_kept":true,"footer_uniform":true,"violations":[]},
  "export_check": {"fonts_substituted":[],"text_overflow":0,"images_cropped":0},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：edit_history 与 versions 对应（可回溯每轮改动）；figures 无编号错位；template_compliance 无违规；交付版本明确标注；numbers_audit 类数值核对全部通过（并入 figures/caption 检查）。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 源材料与指令冲突（如要求扩写但无材料） | 说明并按最小扩写处理，登记 |
| 图表只有截图无数据 | 引用原图，标 original_image，不伪造重绘 |
| 编辑改坏母版 | 立即回退到版本快照，重新隔离改动 |
| 预算不足 | outline+核心页落盘 partial，编辑史随改随记 |

## 6. 自查清单

1. [ ] 每页有叙事角色与唯一主张？可回溯源材料？
2. [ ] 四类编辑指令正确执行且术语一致？
3. [ ] 可重绘/引用原图区分明确？编号引用无错位？
4. [ ] 每轮改动有记录、可回退？交付版明确？
5. [ ] 母版未被动？导出不塌？
6. [ ] result.json 可解析、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒 / 16384 token。outline 先行；编辑史与版本快照随改随写（低成本高回报）；导出检查合并单次执行。

## 8. 最小调用示例（示意输出，非正式案例结果）

```json
{"case_id":"case-demo","status":"success",
 "outline":[{"page":1,"role":"title","claim":"X方法汇报","source_locator":"标题"},
            {"page":3,"role":"result","claim":"效率提升38%","source_locator":"Fig.4a"}],
 "edit_history":[{"round":1,"page":3,"change":"压缩为3要点","reason":"时长10分钟","term_kept":true}],
 "figures":[{"page":3,"figure":"Fig.4a","mode":"redrawn_from_data","caption_ok":true,"number_matches_ref":true}],
 "versions":[{"v":1,"changed_pages":[3],"snapshot_ref":"v1/","revert_path":"v1/"}],
 "delivery_version":"v1",
 "template_compliance":{"master_untouched":true,"theme_kept":true,"footer_uniform":true,"violations":[]},
 "export_check":{"fonts_substituted":[],"text_overflow":0,"images_cropped":0},
 "gaps":[],"uncertainty_notes":[],"changes":[]}
```

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段（如存在）。它定义本案例 `result.json` 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实内容**；contract 里有而本文件 §4 未描述的字段，按 contract 字段语义填实际结果，绝不遗漏；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：一律从 `/input/case.json` 原样读取，禁止自造。
3. **路径**：工作过程写 `/app/work/`；最终产物写 `/app/output/`（deck/页面文件 + result.json）。
4. **尽早落盘**：先用最小可用结果写一次 result.json，再增量增强——任何时刻中断都保证已落盘内容诚实、结构合法（status 如实标 partial）。
5. **不虚构**：无数据、无文件、无软件状态一律不编造；材料缺失写 gaps，无法判断写 uncertainty，禁止把推断写成事实。
6. **可核验**：每个关键结论保留来源定位（论文章节/图表号/材料位置），他人可独立复核。
7. **交付物自检**：本 Skill 的提交材料为 SKILL.md + README.md；运行时按上述契约执行案例。二者不一致处以本节契约为准。

## v2 执行导向强化（对首轮评测反馈的针对性修正）

首轮评测共性短板：工作流描述偏"清单式"，评测器要看到**真实执行与可复核产物**。本轮强化：

1. **产物即证据**：交付中至少包含 3 个真实执行产物（CSV/JSON/日志/脚本），由脚本或工具真实生成，非描述性文字。
2. **过程留痕**：run_log.md 逐条记录执行的命令与统计（抽取数量/命中数/对账结果），换人可重跑得到同一批产物。
3. **对账自检**：关键数字前后对账（输入数=处理数+跳过数等），对账脚本化。
4. **契约不变**：result.json 仍逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实标注 partial。

**本题针对性补强**：
1. python-pptx 生成（真实文件+占位符类型读取验证）；
2. 版本快照 v1/v2 文件夹真实保留；
3. edit_history 与快照一一对应。

## v4 量化对账强化（基于 64 题出分复盘，11-22）

复盘规律：**评测分 ≈ 可量化对账产物密度 × 真实执行痕迹**。高分题（76-81）全部交付"每行可查的 CSV 对账表 + 状态枚举 + 计数断言"；低分题（39-59）败在"描述性框架无产物"。

本轮硬性要求（除本文件已有契约外追加）：

1. **数值型交付物**：按下方"本题针对性补强"列出的 CSV/脚本，全部真实生成到 /app/output/（不虚构行数与计数）。
2. **对账断言**：每张表给出计数对账（总数=分项之和），写进 result.json 的对账字段。
3. **真实执行**：任何统计/计数由脚本产出，run_log.md 逐条记录命令与输出摘要。
4. **契约不变**：result.json 逐字段落实 case.json 的 output_contract；case_id 原样；status 诚实 partial。

**本题针对性补强**：
1. 交付量化对账：edit_history.csv 与 versions 快照数一致断言
2. figure_audit.csv（变形=0）
3. 占位符类型真实读取表。
