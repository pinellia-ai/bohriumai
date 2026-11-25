---
name: apparatus-route-diagram
description: |
  实验装置与技术路线图（workorder: apparatus_and_technical_route）。从装置清单/工艺描述抽取部件—接口—步骤—流向的结构化中间表示，据此布图自检：部件名称数量与材料一致、管路连接不凭空补齐、流向箭头不反向、步骤编号与正文逐条对照；交付分层可编辑 SVG + PNG/PDF 导出与逐元素来源标注。
---

# 实验装置与技术路线图 Skill（apparatus-route-diagram）

## 1. 用途与适用范围

- 用途：装置结构图、带编号流程图、材料/能量/信息流向图、分阶段技术路线图。
- 不做：数据分析与数值拟合、实验方案合理性判断、论文排版。
- 核心判据：实体可追溯、连接与顺序成立、他人可打开改标注重导出。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 全字段抄 order.json）；最小 result.json 先落盘。
2. 盘点材料：装置清单（部件名/数量/参数）、装配说明（接口/连接）、工艺描述（步骤顺序）、技术路线（阶段/里程碑）。材料缺失→failed。
3. 判定 workorder 子类型：apparatus（装置结构）/ procedure（步骤流程）/ flow（物料流向）/ route（技术路线）——可组合。

## 3. 工作流程

### Step 1 结构化抽取（实体—连接—步骤—流向 四表）

写四个 TSV 到 /app/work：

- parts.tsv：`id,name,qty,params,source_location`（部件名与数量照抄材料；同类部件用编号区分，如"泵P1/P2"）
- connections.tsv：`id,from,to,interface,medium,source_location`（from/to 必须在 parts 中；interface 抄材料接口描述；**材料未写的连接不得补**，推断连接标 source=inferred + uncertainty）
- steps.tsv：`id,seq,text,parallel_group,source_location`（seq=材料中的编号；并行支路标 parallel_group；循环回流标注 loop_back；终止条件单列）
- flows.tsv：`id,from,to,what(物料/能量/信息),source_location`（每个箭头一句来源）

复核：connections/steps/flows 的端点全部存在于 parts/steps；qa_check.py 断言通过。

### Step 2 布局规则

- 装置图：主体单元居中，辅助单元（泵/阀/检测器）沿流向排布；接口对齐（管路从接口边缘出线，不从框中心穿出）。
- 流程图：主序列纵向编号 1→n；并行支路同列分叉后汇合；回流箭头虚线绕行；终止节点画双框。
- 流向：箭头方向=材料流向描述（"A 通入 B"→ A→B）；分流画分叉点、合流画汇合点、废料出口单独标注；**禁止断头箭头**（每个箭头两端必须落在部件/步骤上）。
- 技术路线：阶段横向分栏，栏内列方法与里程碑，栏间依赖箭头；阶段目标写在栏头。

### Step 3 渲染

`svg_builder.py diagram_spec.json --outdir /app/output`：节点=部件/步骤（label 带编号），edges=连接/流向（type=neutral 实线；loop_back 用 dash）；图例含线型含义与介质类型。

### Step 4 双重校验

```bash
python3 $SKILL_DIR/scripts/qa_check.py parts.tsv connections.tsv steps.tsv flows.tsv   # 悬空端点/空来源/断头箭头
python3 $SKILL_DIR/scripts/numbering_check.py steps.tsv diagram_spec.json              # 编号与正文顺序对照
python3 $SKILL_DIR/scripts/export_check.py --svg ... --png ... --pdf ... --legend-n N
```

numbering_check 断言：① spec 中步骤节点标签的编号集合 = steps.tsv seq 集合（防编号错位）② spec 边序列形成的拓扑序与 seq 顺序不冲突（存在 per-seq 递增的拓扑序则 PASS）③ 每步骤节点有 source。

### Step 5 result.json

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "workorder_subtype": "apparatus|procedure|flow|route",
  "editable_source": {"svg": "...", "text_editable": true},
  "exports": [{"format": "png", "dpi": 300}, {"format": "pdf", "path": "..."}],
  "structured_ir": {"parts": 0, "connections": 0, "steps": 0, "flows": 0,
                    "tsvs": ["parts.tsv", "connections.tsv", "steps.tsv", "flows.tsv"]},
  "checks": {"qa_check": "pass", "numbering_check": "pass", "export_check": "pass"},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

output_contract 逐字段落实；三大交付=可编辑源文件/导出件/来源与修改记录。

## 5. 数字门槛

- 部件名/数量与材料逐字一致率 100%；凭空补连接数=0（inferred 必须显式标注）；箭头两端无悬空；步骤编号与正文集合相等。
- export_check 全 PASS。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 部件参数缺失 | 节点只标名称，params 标 unverified |
| 工艺描述歧义（顺序不明） | 按 seq 原编号画；无编号按叙述顺序并在 uncertainty 说明 |
| 接口信息冲突 | 采信装配说明，矛盾记 uncertainty |
| 字体/导出失败 | FIG_CJK_FONT 重试；降级只交 SVG |
| 画布溢出 | 分幅或缩节点字号≥8pt；仍溢出→partial 说明 |

## 7. 自查清单

- [ ] 四表齐全、qa_check 过；无凭空连接
- [ ] 箭头方向=流向描述；无断头箭头；回流虚线
- [ ] 编号与正文逐条对照（numbering_check 过）
- [ ] 图例含线型/介质含义；export_check 全 PASS
- [ ] result.json 如实

## 8. 效率约束

先最小 result；一次成型；布局最多返工 2 次；≤50 文件。

## 9. 最小示例

三部件装置（储液罐→泵P1→反应器）+ 四步流程编号对照；qa_check/numbering_check/export_check 全过（见 README 自测记录，示例非正式案例结果）。


## 附录 A 全流程命令序列（评测时按序执行）

```bash
# Step 0 识别（手动：读 /input/case.json 抄 output_contract 到 order.json）
mkdir -p /app/work /app/output
# Step 1-N 主链路（$SKILL_DIR 为本 skill 安装目录）
ls $SKILL_DIR/scripts/        # 确认脚本齐备
# 各 Step 的具体命令见 §3；校验脚本 FAIL 时按 §6 异常表处置后重跑（≤2 轮）
python3 $SKILL_DIR/scripts/export_check.py --help   # 查看参数
```

## 附录 B 常见失败 ↔ 处置对照

| 失败现象 | 根因 | 处置 |
|---|---|---|
| 校验脚本 exit 1 有 FAIL 项 | 见其输出 detail 字段 | 按 detail 修 spec/数据后重跑 |
| PNG 打开是白图/方框 | 无 CJK 字体 | FIG_CJK_FONT=/path/to/font.ttf 后重跑渲染 |
| result.json 字段缺失 | 跳过 Step 6 模板 | 按 §3 末模板逐字段补齐 |
| 预算接近上限 | 前面步骤耗时过多 | 立即交 partial（status 如实），已产文件照常评分 |
| 材料与预期类型不符 | 题面材料变化 | 按 Step 0 盘点结果走 §6 对应行 |

## 附录 C 与本赛道的边界对照（不做的事，避免越界扣分）

- workorder 类型: `apparatus_and_technical_route`；spec 文件命名: `diagram_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。


## 附录 D 四表→spec 的映射规则（布局是数据的确定性投影）

- parts.tsv → nodes（label=`名称+编号`，qty>1 时节点数=qty 或合并节点标 ×qty）
- connections.tsv → edges（type=neutral 实线；interface 写进边标签）
- steps.tsv → 编号节点列（parallel_group 相同→同一列分叉；loop→dash 边）
- flows.tsv → edges 的介质标签（介质类型进图例：液体/气体/能量/信息用不同线型）
- 装置区（如恒温区/无菌区）→ compartments

## 附录 E 渲染后目检清单（export_check 之外的语义检查）

1. 每条管路两端都在部件接口上（无空中悬线）
2. 回流箭头与其他边不重叠（必要时 +20px 偏移）
3. 步骤编号从 1 连续且方向单调（numbering_check 已断言）
4. 图例线型与图面一致；介质标签单位与材料一致


## 附录 F 维护与版本

- 本版本 v1（2026-11-24）：脚本已在构建机实跑（README 自测记录）；迭代时新开 v2 目录并更新 README 差异说明。
- 依赖：仅 Python 3.8+ 标准库 + Pillow（PNG 渲染）；评测环境 scientific-python 兼容。
- 已知限制：p 值/F 分布为近似（stats 题）；PNG 在无 CJK 字体环境需 FIG_CJK_FONT。
