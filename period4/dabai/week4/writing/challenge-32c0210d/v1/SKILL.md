---
name: thesis-longdoc-writer
description: |
  学位论文与长文档写作 Skill：面向数万字规模长文档的章节规划、成稿与跨章
  一致性维护。核心三件套：①三级章节树（章-节-小节）+每节论证任务+证据
  清单+字数预算，预算总和受控；②术语表/符号表/定义清单/结论清单四张
  底账，成稿时强制对齐；③跨章一致性检查脚本——编号连续性、术语同写、
  图表引用有效、前后结论不冲突，改动一处后用依赖表找出受影响段落。
  论断-文献绑定，改动留版本记录，材料外内容标 unverifiable，不编造文献。
---

# 学位论文与长文档写作 Skill

## 1. 用途与适用范围

- 用途：按提纲与材料写出学位论文/长报告的章节稿，并交付配套术语表、引用绑定表、改动记录与一致性检查报告；支持按导师意见分批改稿。
- 适用：综述/方法/结果/讨论各类型章节；万级字数长文档。
- 边界：W 类案例若提供分节可编辑工作稿，则只在其基础上改写与检查，不当作成品论文；材料不足标 gap 不虚构。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、`output_contract` 全字段、材料清单；若含 `organizer-edit-workorder.json` 类工单，以工单划定的编辑目标与离线范围为准。
2. 读 `/input/task.md`：章节要求、篇幅、格式、引用规范。
3. 若材料为分节工作稿（working chapters）：逐节盘点 → 记录每节现状（已有内容/缺口/与其他节的交叉引用），不把工作稿误读为完成稿。
4. 建 `/app/work/chapter-inventory.md`：每节一行 → 节号 | 类型 | 现状 | 字数现状 | 交叉引用(引用了哪些节/图表/结论)。
5. 材料缺失 → status=failed + missing_inputs。

## 3. 工作流程（7 步流水线）

### Step 1 三级章节树 + 字数预算 → /app/work/chapter-tree.md
- 固定结构：第1级"章"，第2级"节"，第3级"小节"，Markdown 标题层级 `# / ## / ###`。
- 每个叶子小节登记：论证任务（回答什么）、所需证据（材料位置）、字数预算、依赖（依赖哪些前文结论/定义）。
- 总字数预算 = 任务要求字数；逐级汇总校验（章预算=节之和，脚本核对）。
- 必备论证要素齐全：研究问题、方法、结果、讨论、局限；著录项：图表、参考文献、附录。
- 验收：三级齐全、预算总和=目标、每个叶子有论证任务。

### Step 2 四张底账 → /app/work/{glossary,symbols,definitions,conclusions}.json
- 术语表：术语 | 唯一写法 | 同义变体（禁止） | 首次出现位置。
- 符号表：符号 | 含义 | 单位 | 首次定义位置。
- 定义清单：定义 | 章节位置 | 内容（防重复定义）。
- 结论清单：结论 ID(C-n) | 章节 | 陈述 | 依赖的结论。
- 验收：成稿前底账先行；每条可指回原文位置。

### Step 3 逐节成稿/改稿 → /app/work/chapters/
- 按章节树逐节写，规则：
  - 术语/符号只用底账唯一写法；
  - 每个叶子小节字数落在预算 ±20%；
  - 论断带证据：`[M-n]` 材料定位、`[R-n]` 文献、跨章引用带 `[C-n]`；
  - 引用了文献但结论被改写、或引用不存在的文献 → 禁止（脚本核对）。
- 改稿模式（按导师/评审意见）：意见拆成修改项 → 每项映射到小节 → 最小改动，保留作者原句与机器改写句差异标记 `<!--EDIT{n}: before|after-->`。
- 验收：叶子字数达标率 ≥90%；论断来源标注无缺失。

### Step 4 依赖表 → /app/work/dependency-map.json
- 每条记录：`{consumed_in: "3.2.1", uses: ["C-2","Sym-sigma","Fig-3"]}`。
- 改动一处后，反查依赖表定位受影响段落（输出到 consistency 报告 `affected_sections`）。
- 验收：跨章引用（[C-n]/图表/符号）100% 入表。

### Step 5 跨章一致性检查 → scripts/check_thesis.py
- 运行 `python3 scripts/check_thesis.py /app/work/chapters/ /app/work/`
- 核对：① 标题层级合法（#→##→### 不跳级）；② 编号连续（图表/公式/章节）；③ 术语变体违规（用了禁用同义写法）；④ [C-n]/[M-n]/[R-n]/Fig-n 悬空；⑤ 字数预算达成（叶子 ±20%，总预算）；⑥ 结论 C-n 被引用处与底账陈述冲突粗检。
- fail 项回 Step 3 修复，最多 2 轮。输出 `consistency-report.json`。

### Step 6 版本与改动记录 → /app/work/changelog.md
- 每次改动：`{节号, 改动类型(新增/改写/删除), before摘要, after摘要, 触发(意见/自查), 可回退标记}`。
- 一次修改可回退、可比较、可说明。

### Step 7 交付 → /app/output/
- `result.json`、合并稿 `thesis.md`（或分节 chapters 副本）、四张底账、`chapter-tree.md`、`consistency-report.json`、`changelog.md`、`todo-review.md`。

## 4. 输出契约（result.json 逐字段）

以 `output_contract` 为准，通用骨架：

```json
{
  "case_id": "<原样>",
  "status": "completed | partial | failed",
  "deliverables": {
    "thesis_markdown": "/app/output/thesis.md",
    "chapter_tree": "/app/output/chapter-tree.md",
    "glossary": "/app/output/glossary.json",
    "consistency_report": "/app/output/consistency-report.json",
    "changelog": "/app/output/changelog.md"
  },
  "fact_source_map": [
    {"claim": "方法沿用X范式", "source": "M-2#方法节", "ref_id": "R-1", "conclusion_id": "C-1"}
  ],
  "version_and_boundaries": {
    "change_records": ["3.2.1 改写：回应导师意见#2，before/after 已留痕"],
    "manual_review_items": ["第4章结论与前文C-2存在张力，需作者裁决"],
    "material_gaps": ["讨论所需同领域对比文献未提供"],
    "anomalies": []
  },
  "uncertainty": [
    {"item": "5.3节字数超预算8%", "level": "low", "handling": "保留并记录"}
  ],
  "summary": {"chapters": 5, "leaf_sections": 18, "budget_total": 30000,
               "budget_actual": 28400, "n_terms": 22, "n_conclusions": 7}
}
```

## 5. 数字门槛

| 门槛 | 值 | 不达标 |
|---|---|---|
| 三级章节树 | 3 级齐全、叶子有论证任务 | 缺级 → partial |
| 叶子字数预算达成率 | ±20% 内 ≥90% | <90% → partial |
| 总字数 vs 目标 | ±10% | 偏差大 → partial 说明 |
| 术语变体违规 / 悬空引用 / 编号断裂 | 0 | 必须修复 |
| 论断-文献绑定率 | 100% 关键论断 | <90% → partial |
| 必备论证要素（问题/方法/结果/讨论/局限） | 5/5 | 缺 → partial |
| 改动留痕 | 100%（有 changelog） | 无痕 → 补记 |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 提纲缺失 | 按学科默认三级树生成，标 manual_review 待确认 |
| 材料为分节工作稿而非成稿 | 如实按工作稿处理，不冒称完成整篇论文 |
| 章节间结论冲突 | consistency 报告列冲突对，两说并存标 manual_review |
| 引用找不到原文 | 引用标 unverifiable，不补编 DOI/年份 |
| 编号不连续/格式不支持 | 脚本检出即修；格式不支持 → 转 markdown 并记 anomalies |
| 超长截断（文档>10万字） | 分节处理+依赖表维持可见性，索引记录截断点 |
| 意见与其引用的章节不匹配 | anomalies + 修改项标 pending，不臆造章节 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 三级树齐全、预算总和=目标、叶子达成率≥90%
- [ ] 四张底账齐且与正文一致（术语唯一写法、无重复定义）
- [ ] 悬空 [C-n]/[M-n]/[R-n]/Fig-n = 0；编号连续
- [ ] dependency-map 覆盖全部跨章引用
- [ ] changelog 每条改动可回退可比较
- [ ] consistency-report 全 pass 或已修复
- [ ] status 与实际一致，partial/failed 有原因

## 8. 效率约束

- 64 请求/900 秒：长文档分节批量产出（每批 2-4 个叶子）；四张底账一次生成；先落最小 result.json 再逐节充实。
- ≤50 文件：分节文件按章合并存放；单文件 ≤500KB、总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入：提纲（4章）+ 分节工作稿 3 节 + 文献条目 8 条。
chapter-tree：4章/12节/18叶，预算 30000 字 → 四张底账（术语 22 条，"卷积神经网络"禁变体"CNN网络"）→ 成稿（论断带 [M-1]/[R-2]/[C-1]）→ dependency-map 41 条 → check_thesis.py 检出"4.2 引用 Fig-7 不存在"→ 修复后全 pass → changelog 6 条 → result.json status=completed。
