---
name: methods-experiments-writer
description: |
  方法与实验章节写作 Skill：从代码、配置、日志、数据说明等散落材料抽取要素，
  对齐正文，产出"可复现四表"（材料表/步骤表/参数表/质控表）+ 章节成稿。
  每条参数与步骤可追溯到具体材料位置；无来源数值不写入正文；缺口显式标出交作者确认，不编造数据。
---

# 方法与实验章节写作（可复现四表 + 参数溯源）

## 1. 用途与适用范围

- 适用：把实验记录、配置文件、日志、数据说明整理成论文的方法与实验章节。
- 方法主线：**先抽要素、再对齐、后成稿**。核心交付物是可复现四表，章节正文由四表支撑。
- 硬约束：数值只来自材料（配置/日志/代码/数据说明/作者确认），来源逐条登记；材料缺口显式标注；不编造。
- 不适用：结果讨论、结论章节（标 out_of_scope）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、任务说明、材料路径、`output_contract` 全字段。
2. 读 `/input/task.md`（如有）：目标期刊格式、章节模板、篇幅约束。
3. 逐个真实读取材料文件；代码/配置读实际内容，日志读实际数值，不凭文件名猜。
4. 材料缺失 → 落 `status=failed` result.json，不虚构。

## 3. 工作流程

### Step 1 要素抽取（四来源）
- 从材料抽取六类要素：方法步骤、实验设置、参数、数据集、对照条件、复现要件。
- 每条要素登记：`{element, value_or_desc, source(文件路径+行/键/页), status(verified|unverified|gap)}`。

### Step 2 组装可复现四表
| 表 | 内容 | 验收标准 |
|---|---|---|
| 材料表 | 数据集/模型/试剂/软件及版本、来源与获取方式 | 名称+版本+来源三项齐全 |
| 步骤表 | 有序步骤：每步输入→操作→输出→判断条件 | 步骤可执行、顺序无歧义、多步不压缩成一句 |
| 参数表 | 参数名/取值/单位/作用对象/来源 | 每行有 source；无来源标 UNVERIFIED 不得入正文 |
| 质控表 | 对照设置、重复次数、随机种子、评价指标与统计方式、异常处置 | 对照同预算说明、种子/重复数明确 |

### Step 3 数值对齐校验（跑 scripts/param_trace.py）
- 扫描章节正文中的数字，逐一在参数表/材料表中查找匹配来源。
- 找不到来源的数字 = "为段落顺畅补出的数值"，从正文删除或标 `[UNVERIFIED: 待作者确认]`。
- 正文数值与表格数值不一致 → 以材料来源为准修正，冲突记录。

### Step 4 章节成稿
- 结构：方法概述 → 材料与数据集 → 实验设置 → 方法步骤 → 对照与评价 → 复现与限制。
- 条件分台：训练/验证/测试条件分开写，硬件、软件版本、种子、重复次数不串台。
- 限制条件落到具体失效场景（"当 X 超过 Y 时方法失效"），不写套话。

### Step 5 复现清单
- 给出他人可复做的最小清单：代码版本、环境/依赖、随机种子、数据获取方式、运行命令、编译/训练轮次。
- 清单中每一项标注来源或 UNVERIFIED。

### Step 6 缺口与确认项
- 汇总所有 gap/unverified 为 `author_queries`（追问清单），逐条：问什么、为什么需要、建议作者提供什么。
- 明确写入正文与 result.json，不静默跳过。

## 4. 输出契约（/app/output/result.json）

以 case.json 的 `output_contract` 为准，本 skill 保证：

```json
{
  "case_id": "原样保留",
  "status": "complete | partial | failed",
  "chapter_text": "方法与实验章节成稿（可编辑）",
  "material_table": [], "procedure_table": [], "parameter_table": [],
  "qc_table": [],
  "param_trace": {"numbers_in_text": 0, "matched": 0, "unmatched": []},
  "reproduction_checklist": [],
  "author_queries": [{"question":"","why":"","suggest":""}],
  "sources": [{"element":"","origin":"材料路径+位置"}],
  "unverified": [], "uncertainty": ""
}
```

### 触发与调用方式
- 触发条件：任务要求整理/补写方法或实验章节、从配置日志生成章节、参数对齐。
- 调用：读 case.json → Step1 要素抽取 → Step2 四表 → Step3 数值对齐（脚本实跑）→ Step4 成稿 → Step5 复现清单 → Step6 追问清单 → result.json 落 /app/output。
- 脚本调用：`python3 scripts/param_trace.py <result.json>`，正文数字溯源校验，存在无来源数值退出码 1。

### 四表字段定义
- 材料表：`{item, name, version, source, access}`（数据集/软件/模型/试剂）。
- 步骤表：`{step_id, input, operation, output, criterion}`（判断条件写明通过/失败标准）。
- 参数表：`{name, value, unit, scope, source, status}`（source 为 文件:行/键 或 作者确认）。
- 质控表：`{aspect, setting, evidence}`（对照、重复次数、随机种子、指标、统计方式）。
- 正文中的条件描述与四表逐项对齐：正文每句含参数的句子都应有对应表行。

## 5. 数字门槛

- 六类要素（步骤/设置/参数/数据集/对照/复现）全部覆盖，缺类标 partial。
- 参数表每行有来源；正文 100% 数字可溯源（param_trace.unmatched 必须为空或已在正文标注 UNVERIFIED）。
- 四表齐全且字段完整；复现清单五要件（代码/环境/种子/数据/命令）逐项落实或标注缺口。
- 达不到门槛诚实标 partial，列出缺口。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 配置冲突（两文件参数不同） | 以可判定来源（日志/代码）为准，冲突记 author_queries |
| 参数无来源 | 标 UNVERIFIED，不入正文数值 |
| 数据集版本不明 | 写"[版本待确认]"，标 gap |
| 材料为代码但不可运行 | 静态读取提取参数，注明"未经实际运行验证" |
| 权限不足/文件损坏 | 记录具体文件与原因，status=partial |
| 多组实验条件混杂 | 分组拆开登记，正文分台描述 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] 四表齐全，字段完整
- [ ] 正文数字 100% 溯源或标 UNVERIFIED
- [ ] 训练/验证/测试条件分台
- [ ] 复现清单五要件落实
- [ ] author_queries 覆盖全部缺口
- [ ] 未编造任何数值与版本号

## 8. 效率约束

预算 64 请求 / 900 秒。先落 chapter_text 最小版+四表骨架，再逐表充实。
≤50 文件、≤2MB、脚本仅标准库。

## 9. 最小示例（示意输出，非正式案例结果）

参数表行示例：
```json
{"name": "learning_rate", "value": "3e-4", "unit": "", "scope": "训练",
 "source": "configs/train.yaml:L12", "status": "verified"}
```
param_trace 示意：正文出现 "batch size 为 256"，若四表无此条目 →
`{"numbers_in_text": 5, "matched": 4, "unmatched": ["batch_size=256 @ §3.2"]}`，
处理：删除该句或改为 "[UNVERIFIED: batch size 待作者确认]"。
### 最小 result.json 完整示意（示意，非正式案例结果）
```json
{"case_id": "示例占位", "status": "partial",
 "chapter_text": "3 方法 …… 4 实验设置 ……",
 "material_table": [{"item": "dataset", "name": "ImageNet", "version": "2012",
   "source": "data/README.md:L3", "access": "官网下载"}],
 "procedure_table": [{"step_id": "S1", "input": "原始图像", "operation": "中心裁剪224",
   "output": "训练输入", "criterion": "尺寸校验通过"}],
 "parameter_table": [{"name": "learning_rate", "value": "3e-4", "unit": "", "scope": "训练",
   "source": "configs/train.yaml:L12", "status": "verified"}],
 "qc_table": [{"aspect": "重复次数", "setting": "3 次独立运行取均值", "evidence": "log/run1.log"}],
 "param_trace": {"numbers_in_text": 12, "matched": 11, "unmatched": ["256 @ §4.2"]},
 "reproduction_checklist": ["代码 commit a1b2c3", "PyTorch 1.12", "seed 42", "数据官网下载", "bash train.sh"],
 "author_queries": [{"question": "batch size 256 的来源?", "why": "配置与日志不一致",
   "suggest": "提供 run 日志或确认配置值"}],
 "sources": [{"element": "lr=3e-4", "origin": "configs/train.yaml:L12"}],
 "unverified": [{"item": "batch size", "reason": "配置与日志冲突"}],
 "uncertainty": "batch size 冲突已挂起待作者确认"}
```
