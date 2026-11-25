---
name: mindmap-builder
description: |
  学术思维导图 Skill：从论文/综述/实验方案等材料构建可机读、可编辑、节点
  可溯源的思维导图。双格式交付：markdown 层级大纲（机读主格式，缩进即层
  级）+ OPML/FreeMind 兼容 XML（可导入脑图工具）。每个节点带 evidence
  定位（材料路径+页码/段落），节点分 fact(事实)/summary(概括)/inference
  (推断) 三级并显式标注；关系边（因果/依赖/对比/支持/冲突）必须有原文
  依据，材料没有依据的连接禁止。节点规模受控（默认≤60），不编造内容。
---

# 学术思维导图 Skill

## 1. 用途与适用范围

- 用途：从固定材料构建论文结构/研究方案/项目计划/会议纪要/概念体系类思维导图，交付可读可改可导入的导图文件+溯源台账。
- 适用：单篇论文梳理、综述多文献整理、实验方案组织。
- 边界：节点内容忠于材料；不把装饰性词语当关键节点；无依据的连接不画。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：`case_id` 原样、`output_contract` 全字段、材料路径。
2. 读 `/input/task.md`：导图用途、目标读者、期望根节点视角（论文结构/研究问题/任务计划）、格式与规模要求。
3. 打开材料读实际内容；建 `/app/work/source-index.md`：段落级定位表（`S-n | 材料#页码/段落 | 关键内容`），作为节点 evidence 的取值池。
4. 材料缺失/不可读 → status=failed + missing_inputs。

## 3. 工作流程（5 步流水线）

### Step 1 概念抽取 → /app/work/extract.json
- 从材料抽取六类要素：核心概念 / 研究问题 / 方法 / 证据 / 结论 / 任务（按导图用途取舍），每条：`{id, text, source(S-n), kind(fact/summary/inference)}`。
- 事实=材料原句直取；概括=多句压缩（标注依据句）；推断=材料未明说但由事实支撑（显式标 inference）。
- 验收：每条要素有 source；推断条数占比 ≤20%。

### Step 2 层级组织 → /app/work/hierarchy.md
- 根节点=任务指定的视角；同级节点粒度一致（同级互斥、不交叉、不重复）；
- 层级深度默认 3-4 级；重要信息不埋没（关键结论在≤3级深度内可见）；
- 节点规模上限 60（超出先归并下位节点）；每节点 ≤25 字。
- 验收：每个节点可回溯到 extract.json 条目；无材料外节点。

### Step 3 关系标注 → /app/work/relations.json
- 仅标注有材料依据的关系边：`{from, to, type(因果/依赖/对比/时间/引用/支持/冲突), evidence(S-n)}`。
- 材料没说因果的不得画因果边；对比/冲突边必须引用材料中原文对照处。
- 验收：每条边有 evidence；边数 ≤ 节点数。

### Step 4 导图生成 → /app/work/mindmap.md + mindmap.opml
- markdown 主格式（机读）：缩进层级+节点标记：

```markdown
# 根节点  <!-- purpose: 论文结构 -->
## 研究问题 [S-1|fact]
### 问题A：X对Y的影响 [S-2|fact]
- 关系: 依赖 → 方法B [S-5]
```

- OPML 辅格式（可导入主流脑图工具）：`<outline text="...">` 嵌套，节点备注带 evidence。
- 验收：脚本核对层级缩进合法、节点引用 S-n 有效、规模达标。

### Step 5 校验与交付 → scripts/check_mindmap.py → /app/output/
- 运行 `python3 scripts/check_mindmap.py mindmap.md relations.json extract.json source-index.md`
- 核对：① 节点数 ≤60、深度 ≤4；② evidence S-n 在 source-index 中存在；③ extract 中 fact 条目 100% 进入导图（防关键信息遗漏）；④ relations 的 from/to 节点均存在于导图。
- fail 项回 Step 2/3 修复。交付：`result.json`、`mindmap.md`、`mindmap.opml`、`relations.json`、`extract.json`、`checks.json`。

## 4. 输出契约（result.json 逐字段）

以 `output_contract` 为准，通用骨架：

```json
{
  "case_id": "<原样>",
  "status": "completed | partial | failed",
  "deliverables": {
    "mindmap_markdown": "/app/output/mindmap.md",
    "mindmap_opml": "/app/output/mindmap.opml",
    "relations": "/app/output/relations.json",
    "node_extract": "/app/output/extract.json"
  },
  "fact_source_map": [
    {"node": "方法B：迁移学习", "source": "paper.pdf#p3 para2", "kind": "fact"}
  ],
  "version_and_boundaries": {
    "change_records": ["根节点按任务要求取'研究方案'视角"],
    "manual_review_items": ["两处材料结论冲突(§3.2 vs §5.1)，导图双列并标冲突边"],
    "material_gaps": ["任务要求含'负责人'但材料未提供"],
    "anomalies": []
  },
  "uncertainty": [
    {"item": "节点X归入'方法'还是'结果'存在两可", "level": "low", "handling": "按材料段落主旨归入方法"}
  ],
  "summary": {"n_nodes": 42, "max_depth": 4, "n_relations": 18,
               "kinds": {"fact": 30, "summary": 9, "inference": 3}}
}
```

## 5. 数字门槛

| 门槛 | 值 | 不达标 |
|---|---|---|
| 节点 evidence 覆盖 | 100% 节点带 S-n | 缺失节点标 inference+gap |
| 关系边 evidence | 100% | 无依据边必删 |
| 推断节点占比 | ≤20% | 超出 → 降级回材料句 |
| 节点规模 | ≤60（或任务指定） | 超出先归并 |
| 深度 | ≤4 | 超出提升层级 |
| fact 要素入图率 | 100% | 关键概念遗漏 → 补图 |

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 材料自相矛盾 | 两说并列+冲突边（evidence 指向两处原文），不擅自取舍 |
| 节点规模爆炸 | 先归并同粒度下位节点，保持 fact 覆盖率 |
| 格式不支持（要 xmind/freemind 二进制） | 交付 markdown+OPML 标准格式并说明，anomalies 记录 |
| 任务要求的维度材料没有（如负责人） | material_gaps 记录，不虚构节点 |
| 材料超长 | 按 task.md 用途定向抽取，source-index 记录抽样范围 |
| 装饰性词语 | 不入导图；如属标题结构可作锚但不设节点 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] markdown 层级缩进合法，可脚本解析
- [ ] 每节点有 [S-n|kind]，每边有 evidence
- [ ] fact 100% 入图；无材料外节点/无依据边
- [ ] OPML 可解析（XML well-formed）
- [ ] checks.json 全 pass；status 与实际一致

## 8. 效率约束

- 64 请求/900 秒：Step1-2 合并 1-2 次调用；markdown 由层级 JSON 一次性渲染；先落最小 result.json。
- ≤50 文件、单文件 ≤500KB、总量 ≤2MB。

## 9. 最小示例（示意输出，非正式案例结果）

输入：1 篇论文 PDF（12 页）。
source-index 40 段 → extract 45 条（fact 30/summary 12/inference 3）→ hierarchy 42 节点 4 级 → relations 18 条（含 1 条冲突边：§3.2 vs §5.1 结论对照）→ check_mindmap.py 全 pass → 交付 mindmap.md + mindmap.opml → result.json status=completed。
