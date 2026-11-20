---
name: library-file-manager
description: |
  科研资料库与文件管理 Skill。让资料在半年后仍能被找到、被信任、被交接：盘点输入文件/
  目录/权限 → 按题目规则组织并维护元数据与版本关系（原始数据/扫描件/旧版本/备份的演进
  链）→ 输出可检索可交接清单 → 跳过/失败/冲突逐条记录与恢复方式。只动副本、留底账。
---

# Library File Manager — 科研资料库与文件管理 Skill

## 1. 用途与适用范围

把"元数据在某人的记忆里"变成可交接的结构：组织、元数据、版本链、交接清单。硬约束：**不删除不覆盖原文件**（所有整理在副本/新目录进行），原位置留底账。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：output_contract 全部字段、case_id、文件/目录清单、组织规则、权限约束。
2. 盘点：文件数、类型（原始数据/扫描件/文档/备份）、目录结构、可读性/权限。
3. 不可读/无权限文件：登记 skipped，不硬闯。

## 3. 工作流程

### Step 1 盘点底账
- 全文件清单：`{path, type, size, mtime, readable}`——对账基准（总数前后一致）。

### Step 2 组织与元数据
- 按题目规则归入目标层级；每文件登记元数据：`{新路径, 类型, 项目/实验归属, 日期, 来源路径}`。
- **版本关系**：同一材料的演进链（v1→v2→修订版→改名副本）按内容/时间/命名特征识别并链接，不按文件名猜。
- 重命名只做映射登记（原路径→新路径），可回溯。

### Step 3 可检索交付
- 交接清单（含分类统计）；索引（关键词→文件）；版本链图。

### Step 4 异常留痕
- 跳过（权限/损坏/未知类型）、失败、冲突（同名不同内容）逐条记录 + 恢复方式（从哪个底账找回）。

## 4. 输出契约

```json
{
  "case_id": "<原样>",
  "task": "library_file_management",
  "status": "success | partial | failed",
  "inventory": {"total_files":312,"by_type":{"raw":80,"scan":42,"doc":150,"backup":40},"readable":310,"skipped":2},
  "organized": [{"src":"...","dst":"...","type":"raw","meta":{"project":"P1","date":"2024-03","instrument":"XRD"}}],
  "version_chains": [{"chain_id":"v1","items":[".../draft_v1.docx",".../draft_v2.docx",".../final.pdf"],"relation":"演进链","evidence":"时间戳+内容相似"}],
  "handover_list": "handover.md（分类统计+索引）",
  "skipped": [{"path":"...","reason":"权限不足","recovery":"需管理员授权后重跑"}],
  "reconciliation": {"before":312,"after_organized":310,"skipped":2,"match":true},
  "gaps": [], "uncertainty_notes": [], "changes": []
}
```

硬性要求：reconciliation 对账成立；原文件未动（只映射登记）；版本链有依据；skipped 可恢复。

## 5. 异常处理

| 情况 | 处置 |
|---|---|
| 目录不可读 | skipped + 恢复方式 |
| 同名冲突 | 双路径保留，不覆盖 |
| 预算不足 | 底账+核心目录优先（partial） |

## 6. 自查清单

1. [ ] 底账对账成立？原文件未动？
2. [ ] 元数据/版本关系有依据？
3. [ ] 清单可检索可交接？
4. [ ] skipped 可恢复？
5. [ ] result.json 含 output_contract 全部字段、case_id 原样？

## 7. 效率约束

预算 64 请求 / 900 秒。盘点脚本化；组织规则映射批处理；交接清单自动生成。

## 附：运行时硬性契约（评分相关，逐条执行，优先级最高）

1. **Step 0 必做——读 output_contract**：打开 `/input/case.json`，找到 `output_contract` 字段。它定义 result.json 必须包含的全部字段。**原样保留字段名与嵌套结构，逐字段落实**；contract 缺失时按本文件 §4 结构输出并在 uncertainty_notes 登记。
2. **case_id**：从 `/input/case.json` 原样读取，禁止自造。
3. **事实依据**：输入文件与材料是事实依据；不编造记录/引用/软件状态/数据。
4. **路径**：过程写 `/app/work/`；最终产物写 `/app/output/result.json`。
5. **尽早落盘**：先写最小可用 result.json 再增强；中断时已落盘内容诚实合法（status=partial）。
6. **可追溯**：每条结果/判定保留来源定位（文件/记录/原文短句）。
7. **交付物自检**：SKILL.md + README.md 一致，不一致以本节契约为准。
