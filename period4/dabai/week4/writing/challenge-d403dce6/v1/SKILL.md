---
name: grant-proposal-writing
description: |
  基金申请书写作 Skill。基于给定材料产出"可直接进入申请书的章节稿＋要素对照说明"：科学问题—创新点—研究目标—研究内容—技术路线—考核指标—研究基础七要素逐层咬合（目标↔内容↔路线↔指标一一对应，不出现目标三个路线两条），创新点与已有工作差异定位（不用"首次/国际领先/填补空白"类无法核验修饰），已完成与拟开展严格区分，引用与前期成果带来源。离线运行：事实性内容回溯到输入材料位置，申请人证据缺失如实标 gap，不编造文献/数据/成果。
---

# 基金申请书写作（七要素咬合 → 逐条对应 → 证据链）

## 1. 用途与适用范围

- 用途：把散乱材料（论文、前期成果、指南要求）组织成申请书章节稿+要素对照说明。
- 适用：立项依据/科学问题/研究目标/创新点/技术路线/研究基础/可行性任一节或整稿；不适合作预算表。
- 四大考察点：立得住（必要性论证）、说得准（创新差异可核验）、对得上（目标-内容-路线-指标逐条对应）、查得到（引用与前期成果可追溯）。
- 组织方修订v1：三案例补充写作要求与七要素/计划一致性约束；真实申请人证据仍明确缺失，不得虚构。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样保留、任务说明、材料路径、output_contract 全字段。
2. 读 `/input/task.md` 与 `organizer-workorder.json`（如存在）：目标基金类型、章节要求、篇幅、七要素/计划一致性约束。
3. 盘点材料：领域文献（PDF 读全文）、申请人前期成果、平台条件、指南/政策口径。**原论文与既有成果归外部作者；真实申请人证据缺失时标 gap，不补造。**
4. 先落盘最小 `result.json`（status=partial 占位）。

## 3. 工作流程（七步流水线）

### Step 1 材料证据台账（产出 `evidence_ledger.json`）
`ev_id | 类型（文献/数据/前期成果/平台/政策口径） | 内容 | 来源位置（文件/页/段）`。后续每个事实性句子引用 ev_id；台账外事实不得写入。

### Step 2 科学问题收敛（产出 `elements_matrix.md` 首节）
把宽泛兴趣收敛为可回答、可分解、有边界的科学问题：写明"别人做到哪一步（ev_id）、还差什么、为什么必须现在做、为什么是我们"。禁止政策口号堆叠——每句必要性挂台账证据。

### Step 3 目标-内容-路线-指标对应矩阵（elements_matrix.md 主体，本题核心）
表格式逐行咬合：`研究目标 G1..Gn | 对应研究内容 C1..Cn | 技术路线步骤 R1..Rn（输入→方法→输出+关键节点+风险与备选） | 考核指标 M1..Mn（可检验）`。硬规矩：**行数一致、逐行对应**，出现目标三个、路线两条、指标另说一套即 FAIL。技术路线不罗列方法名，每步写输入输出与可行性依据（挂 ev_id）。

### Step 4 创新点定位（elements_matrix.md）
先列代表性已有工作（文献+位置），再写差异：`创新点 I1..In | 与已有工作的具体差别（对比对象+位置） | 为什么难 | 凭什么做得成（前期基础 ev_id）`。禁用"首次/国际领先/填补空白"等无法核验修饰。

### Step 5 研究基础与可行性（elements_matrix.md）
组织成证据链：`能力（平台/经历/团队分工）→ 证据（ev_id，具体成果）→ 与本研究的关系（支撑哪条 G/R）`。申请人证据缺失处如实标 `gap: 申请人材料未提供`。已完成/拟开展逐条标注 completed / planned。

### Step 6 一致性回检（产出 `consistency_check.md`）
跑 `scripts/check_proposal.py`（§6）：① G/C/R/M 行数与对应关系；② 违禁修饰词扫描（首次/国际领先/填补空白/开创性）；③ 引用与前期成果的 ev_id 覆盖率；④ completed/planned 混淆检查。FAIL 项修复后重跑。

### Step 7 章节稿组装与汇总（产出 `proposal_sections.md`）
按 task.md 章节要求组装，段落标注 [G1][C2][R1][M3][I2] 等要素标签便于评审核对；result.json 汇总。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "<原样保留>",
  "status": "success | partial | failed",
  "deliverable": {
    "proposal_sections": "/app/output/proposal_sections.md",
    "elements_matrix": "elements_matrix.md",
    "consistency_check": "consistency_check.md",
    "evidence_ledger": "evidence_ledger.json"
  },
  "facts_sources": [
    {"item": "申请人已发表 SCI 论文 3 篇", "source_location": "material/cv.pdf p.1", "manuscript_location": "研究基础 §1", "status": "completed"}
  ],
  "elements_mapping": [
    {"goal": "G1", "content": "C1", "route": "R1", "metric": "M1"}
  ],
  "innovation_positions": [
    {"innovation": "I1", "diff_from": "文献 zhang2021.pdf p.5 的方法 A", "why_hard": "…", "basis": "ev-04"}
  ],
  "changes": [
    {"location": "创新点 §2", "before": "国际领先", "after": "与已有方法 A 的差异为…（对比位置 p.5）", "reason": "去除不可核验修饰"}
  ],
  "uncertainty": [{"item": "政策口径", "issue": "指南未明确考核形式", "resolution": "指标按可检验形式起草", "needs_human_confirm": true}],
  "gaps": ["申请人真实前期证据材料未提供，研究基础节仅按材料外标 gap 的占位框架起草"],
  "limits": ["预算表不在本任务范围"],
  "reproduce": "按 README 步骤可复现"
}
```

硬性要求：`elements_mapping` G/C/R/M 逐行对应；`facts_sources` 覆盖全部事实性内容并标 completed/planned；台账外事实=0；`gaps` 如实列申请人证据缺失。

## 5. 数字门槛（达不到如实标 partial）

- 要素齐全：七个要素（立项依据/科学问题/目标/创新点/技术路线/指标/研究基础）按 task.md 要求逐节产出，缺节=partial。
- 咬合率：G/C/R/M 对应行 100% 配对（脚本比对），错配=FAIL。
- 修饰词：违禁修饰词 0 处（脚本扫描）。
- 证据覆盖：事实性句子 ev_id 覆盖率 100%（抽查+台账对账）；申请人证据缺口全部在 gaps。

## 6. 校验脚本

捆绑 `scripts/check_proposal.py`（纯标准库）：输入 `mapping.json`（G/C/R/M 对应表）+ `banned.json`（违禁词表+全文文本路径）+ `claims.json`（事实句→ev_id），输出 MAPPING/BANNED/EVID 报告。先最小样例实跑再正式使用。

## 7. 异常处理表

| 异常 | 处置 |
|---|---|
| 材料缺失（指南不明/申请人证据缺） | gaps 记录，对应节按占位框架+needs_human_confirm，不虚构 |
| 超长输入 | 按要素分块处理，矩阵全局编号 |
| 引用无法核实 | 不写入正文；如必须提及标 unverifiable |
| 学科跨度过大 | 按 task.md 主学科口径取术语，uncertainty 记录 |
| 格式冲突（指南 vs 模板） | 优先指南条款，uncertainty 记录冲突 |
| 内容涉密/未发表成果 | 按材料指示处理，不扩散细节 |

## 8. 效率约束

预算 64 请求 / 900 秒：Step 0-1 前 10 请求；七要素分节产出后组装；先落最小 result.json。≤50 文件 / 2MB。

## 9. 最小示例（示意，非正式案例结果）

输入：3 篇领域文献 + 指南要求 + 申请人简历（部分）。
示意输出：evidence_ledger 22 条；elements_matrix G3/C3/R3/M3 逐行对应；创新点 2 条均带对比位置；consistency_check 全过；章节稿 4 节带要素标签；result.json status=success（申请人平台证据缺口在 gaps）。

## 10. 命令序列

```
1. cat /input/case.json → 最小 result.json
2. evidence_ledger.json（证据台账，completed/planned 区分）
3. elements_matrix.md（科学问题收敛 → G/C/R/M 对应矩阵 → 创新点 → 研究基础）
4. proposal_sections.md（带要素标签组装）
5. python3 scripts/check_proposal.py mapping.json banned.json claims.json
6. 修 FAIL → result.json 定稿
```

## 11. 自查清单（交前全过）

- [ ] YAML frontmatter 可解析
- [ ] 七要素齐全且 G/C/R/M 逐行咬合（目标三个路线两条=FAIL）
- [ ] 创新点与已有工作差异带对比位置；违禁修饰词 0 处
- [ ] 已完成/拟开展逐条区分；申请人证据缺口在 gaps
- [ ] result.json 全字段落实（facts_sources/elements_mapping/innovation_positions/changes/uncertainty/gaps/limits）
- [ ] 脚本 ast.parse + 最小实跑通过
- [ ] ≤50 文件 / 2MB
