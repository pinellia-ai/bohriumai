---
name: research-transfer-writing
description: |
  科研成果转化写作 Skill。把论文/技术报告按指定受众与体裁改写为可直接使用的转化稿（科普文/申报材料等），方法主线为"受众画像 → 取舍策略 → 逐段改写 → 术语锁定 → 论断强度校准 → 逐段对照复核"。离线运行：所有事实、数字、限定条件必须回溯到源文具体位置（文件/节/段），源文外内容标 gap，不把相关写成因果、不把初步结果写成定论、不新增源文没有支持的结论。
---

# 科研成果转化写作（受众画像 → 取舍 → 术语锁定 → 逐段对照）

## 1. 用途与适用范围

- 用途：在"提供源文、说明读者与体裁"时完成一次完整改写，交付可继续编辑的改稿+逐段对照+改动清单。
- 适用：论文→科普、技术报告→申报材料、论文→项目材料等文体转换；不适用无源文的自由创作。
- 四大考察点对应：读得懂（受众适配）、留得住（取舍不丢证据）、说得准（论断强度匹配）、接得住（逐段可复核）。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、源文路径、output_contract 全字段。
2. 读 `/input/task.md`：提取**目标读者、体裁、篇幅上限、目标语言**四要素；缺任一项 → uncertainty 记录 needs_human_confirm，并采用保守默认（如读者=受过本科教育的非本领域读者）。
3. 读源文真实内容（PDF 用 pdf-text 工具），不依赖领域标签猜测内容。
4. 先落盘最小可用 `result.json`（status=partial 占位）。

## 3. 工作流程（七步流水线）

### Step 1 受众画像（产出 `audience_profile.md`）
逐项写：知识背景、阅读目的、已知概念/未知概念清单、解释深度、术语密度上限、类比方式、篇幅分配。依据 task.md，不足处标 inferred。

### Step 2 源文拆解与取舍策略（产出 `take_strategy.md`）
- 拆段编号（S1, S2, ...），每段给来源位置。
- 三级取舍：**必须保留**（关键结论、数据+单位、样本信息、限定条件、指标口径、图表引用）、**可以压缩**（方法细节、重复论证）、**可以删除**（冗余、与读者无关内容）。每条删除项必须写理由——"删掉的是冗余而不是证据"。

### Step 3 术语锁定表（产出 `term_lock.md`）
从源文抽取领域术语/缩写：`源文术语 | 译/改法 | 首次出现位置 | 处理规则（首次展开/全文统一）`。同一概念全文只有一个说法；缩写首次出现展开并给出处。

### Step 4 论断强度标注（写入 take_strategy.md 附表）
对每条关键论断标注源文证据强度：`established（领域共识）/ supported（本研究数据支撑）/ preliminary（初步结果）/ speculation（推测）`。改写时表述强度不得高于源文强度：初步结果必须带"初步/在…条件下"限定；相关不得写成因果。

### Step 5 逐段改写（产出 `transferred_draft.md`，可编辑）
按目标体裁组织；每个数字、单位、比较基准、样本量、图表编号与源文逐字一致；需要换表达时在 change_log 记录理由。面向公众时：未展开缩写必须展开、公式尽量文字化、行话加一句解释。

### Step 6 逐段对照与改动清单（产出 `para_mapping.md` + `change_log.md`）
- para_mapping：`源文段号 | 改稿段号 | 取舍级别 | 保留要点 | 改动摘要`。
- change_log：每处删改 `位置 | before | after | 理由 | 证据强度是否变化`。

### Step 7 校验与汇总（result.json）
跑 `scripts/check_transfer.py`（§6）：数字保真、图表引用完整性、术语一致性、限定语存在性检查。全过 status=success，否则 partial 并在 limits 列明。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "draft_file": "/app/output/transferred_draft.md",
    "audience_profile": "audience_profile.md",
    "para_mapping": "para_mapping.md",
    "change_log": "change_log.md",
    "term_lock": "term_lock.md"
  },
  "facts_sources": [
    {"item": "样本量 n=120", "source_location": "source.pdf p.4 §3.1", "action": "kept", "draft_location": "transferred_draft.md §2"}
  ],
  "claim_strength": [
    {"claim_id": "C-02", "source_strength": "preliminary", "draft_expression": "初步结果显示…", "location": "source.pdf p.7"}
  ],
  "changes": [
    {"location": "S3→T2", "before": "方法细节3段", "after": "压缩为2句", "reason": "受众不需要实验参数", "evidence_loss": false}
  ],
  "uncertainty": [{"item": "篇幅上限", "issue": "task.md 未指定", "resolution": "默认800字", "needs_human_confirm": true}],
  "gaps": ["源文未提供图2数据表，图表引用仅保留编号"],
  "limits": ["科普版未覆盖源文§5机理讨论（受众取舍）"],
  "reproduce": "按 README 步骤可复现"
}
```

硬性要求：`facts_sources` 覆盖全部保留的数字/图表引用/关键结论；`changes` 逐条可复核且标 evidence_loss；源文外新事实数=0。

## 5. 数字门槛（达不到如实标 partial）

- 保留率：必须保留清单中每项在改稿中可指认位置，缺 1 项即 partial。
- 数字保真：改稿中全部数字可在源文找到原文（check_transfer.py 抽取比对），不一致=FAIL。
- 术语一致：term_lock 中每个术语在改稿出现形式唯一，否则 FAIL。
- 强度校准：源文 preliminary/speculation 论断在改稿中无对应限定语 → FAIL。

## 6. 校验脚本

捆绑 `scripts/check_transfer.py`（纯标准库）：输入 `source.json`（源文数字/图表引用/术语清单）+ `draft.json`（改稿对应清单），输出逐项报告：数字保真 diff、图表引用缺失、术语多形式冲突。先最小样例实跑再用于正式案例。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 源文缺引用/数据自相矛盾 | uncertainty 记录，改稿保留矛盾处原样并标注 needs_human_confirm，不擅自仲裁 |
| 体裁与篇幅冲突 | 保守满足体裁结构，limits 说明牺牲项 |
| 材料涉密/未发表 | 改稿只用于交付，不扩散，uncertainty 标注 |
| 术语表冲突（同一词两种惯用） | 采用源文首次出现译法锁定，term_lock 记录决定理由 |
| 源文段落与图表编号断裂 | gaps 记录，引用保留原编号不加new编号 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-2 合并前 10 请求；长文分段处理每批 ≤8 段；先落最小 result.json。产物 ≤50 文件 / 2MB。

## 9. 最小示例（示意，非正式案例结果）

输入：源文 paper.pdf（含 "n=120, p<0.05, 见 Fig.3"）+ 要求"面向公众科普文，800字"。
示意输出：audience_profile 5 项；term_lock 6 条；改稿 780 字全部数字与源文一致；para_mapping 9 行；result.json status=success，claim_strength 含 1 条 preliminary→"初步结果显示"。

## 10. 命令序列

```
1. cat /input/case.json → 最小 result.json
2. 读源文 → 拆段编号 → take_strategy.md（三级取舍+强度标注）
3. term_lock.md → 逐段改写 transferred_draft.md
4. para_mapping.md + change_log.md
5. python3 scripts/check_transfer.py source.json draft.json
6. 修 FAIL → result.json 定稿
```

## 11. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] 受众画像四要素有出处（缺项标 inferred/uncertainty）
- [ ] 必须保留项 100% 可指认改稿位置
- [ ] 全部数字回溯源文位置；源文外新事实=0
- [ ] result.json 含 case_id/status/deliverable/facts_sources/claim_strength/changes/uncertainty/gaps/limits
- [ ] 脚本 ast.parse + 最小实跑通过
- [ ] ≤50 文件 / 2MB
