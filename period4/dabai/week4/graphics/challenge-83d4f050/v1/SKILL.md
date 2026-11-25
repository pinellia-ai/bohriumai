---
name: biological-mechanism-pathway
description: |
  生物机制图与通路图（workorder: biological_mechanism_pathway）。把机制材料变成可逐条质疑的机制陈述图：生物实体命名规范（基因/蛋白/复合物不混用）、相互作用语义映射（激活/抑制/结合/修饰/转运可区分）、通路方向与区室拓扑正确、图例-颜色-数据三者自洽、分层可编辑 SVG + PNG/PDF 导出；每个实体与每条边回溯到材料位置。
---

# 生物机制通路图 Skill（biological-mechanism-pathway）

## 1. 用途与适用范围

- 用途：机制文字→图元/边结构化映射→约束布局→可编辑导出。图是"机制陈述"，每个箭头带语义。
- 不做：统计结论、实验设计、论文写作。
- 核心判据：实体与边可回溯到输入材料或权威命名；图例/颜色映射自洽；他人可打开源文件改标签重导出。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 全字段抄 order.json）；若提供 wenyon dataset 引用，按 retrieval_ref 说明取材方式，取不到则只依据本地材料并记 uncertainty。
2. 最小 result.json 先落盘（status=running）。
3. 盘点材料：PDF 用 pdf-text-tool 提文本；逐段找：实体句（"X 表达/定位于…")、相互作用句（"X 促进/抑制/磷酸化/结合 Y"）、区室词（膜、胞质、核、线粒体）。
4. 材料缺失→status=failed + missing_materials。

## 3. 工作流程

### Step 1 生物实体清单（命名规范优先）

写 entities.tsv（`id,name,type,compartment,attrs,source_location`）：
- type ∈ gene_protein_complex/cell_type/compartment/molecule；基因与蛋白按材料原写法区分（人基因大写斜体约定照抄，不擅自改）。
- 同义名/旧名：以材料最新用法为准，其余写进 attrs.aka；同名歧义（基因 vs 蛋白）→ 按上下文判定并在 uncertainty 记判定依据。
- 复合物画单节点，成员列 attrs.members；不得把家族成员画成独立节点（材料没说时）。
- 复核：**图中不得出现 entities.tsv 之外的任何生物名词**（防幻觉实体——这是本赛道最常见硬伤）。

### Step 2 相互作用清单（语义→箭头固定映射）

relations.tsv（`id,from,to,type,evidence_text,source_location`）：
- type ∈ activate/inhibit/bind/modify/transport/contain/neutral；evidence_text 抄原文动词短语。
- 固定视觉约定（写进图例）：activate=黑色实心三角箭头；inhibit=红色 T 形端箭头；bind=双端菱形/短线；modify=箭头+修饰标签（如 P=磷酸化、U=泛素化，标签文字来自材料）；transport=跨区室箭头；contain=嵌套区室。
- 方向判定："A 促进 B"→ A→B；"B 被 A 抑制"→ A→B（被动句翻转为因果方向）。依据不足→neutral+uncertainty。
- 反馈环与分支：显式画出（环=回到上游节点的边，注明"feedback"）；材料未提反馈环不得自行补。

### Step 3 拓扑布局约束

layout_plan.json：
- 区室：膜（双层画法：两条平行横线）、胞质、核从上到下；跨膜受体**跨在膜线上**（一半膜外一半膜内），不得整体画进胞内。
- 上下游：受体→胞内信号→效应（核内转录/分泌）自左向右或自上而下；分支并列展开；反馈环用虚线。
- 节点避让：间距≥40px；边标签不压节点；引导线交叉>2 处必须重排。

### Step 4 渲染

`svg_builder.py diagram_spec.json --outdir /app/output`（spec 格式见脚本头注释；compartments 表达区室，edges 带 type）→ SVG/PNG/PDF。图例必含：本图用到的全部边类型 + 颜色含义（若有数据映射：颜色编码表达量/显著性时，datamap.tsv 逐项给值与来源）。

### Step 5 校验（双重）

```bash
python3 $SKILL_DIR/scripts/qa_extract.py entities.tsv relations.tsv datamap.tsv   # 悬空引用/空来源
python3 $SKILL_DIR/scripts/pathway_check.py diagram_spec.json entities.tsv relations.tsv  # 语义/拓扑断言
python3 $SKILL_DIR/scripts/export_check.py --svg ... --png ... --pdf ... --legend-n N
```

pathway_check 断言：① spec 节点⊆实体清单、边⊆关系清单（防幻觉）② 边类型∈语义枚举 ③ 每边有 source ④ 图例类型数=实际使用类型数 ⑤ 区室归属与实体 compartment 一致。任一 FAIL 修 spec 重跑。

### Step 6 result.json

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "editable_source": {"svg": "...", "layers": 5, "text_editable": true},
  "exports": [{"format": "png", "dpi": 300}, {"format": "pdf", "path": "..."}],
  "entity_edge_trace": {"entities": 0, "edges": 0, "entities_tsv": "...", "relations_tsv": "...", "pathway_check": "pass"},
  "legend_semantics": {"activate": "实心三角箭头", "inhibit": "红色T形端箭头"},
  "compartments": ["膜", "胞质", "核"],
  "export_check": {"pass": true},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

output_contract 逐字段落实；三大交付=可编辑源文件/导出件（含尺寸分辨率字体色彩检查）/来源与修改记录（实体边清单+语义映射+异常说明）。

## 5. 数字门槛

- 幻觉实体数=0（pathway_check 强制）；每边有 source_location；边类型与证据动词一致率 100%。
- export_check 全 PASS；SVG 文字可编辑。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 输入缺方向信息 | neutral 箭头 + uncertainty，不补方向 |
| 基因/蛋白同名歧义 | 照抄材料写法，uncertainty 记判定 |
| 输入数据与图示矛盾 | 以材料为准；矛盾无法消解→partial 并列明双方位置 |
| 区室信息缺失 | 只画实体与边，区室标 unverified |
| 元素过多不可读 | 按材料主通路优先，次要分支折叠为"+n more"并在图注展开 |
| 字体/导出失败 | FIG_CJK_FONT 重试；仍失败只交 SVG |

## 7. 自查清单

- [ ] 实体 100% 来自材料（pathway_check 过）
- [ ] 箭头类型=证据动词；方向=因果方向
- [ ] 区室/跨膜位置正确；反馈环与分支照材料画
- [ ] 图例覆盖全部使用的语义类型
- [ ] export_check 全 PASS；result.json 如实

## 8. 效率约束

先最小 result；抽取一次成型；布局失败最多重排 2 次；≤50 文件。

## 9. 最小示例

EGFR(膜)→RAF activate→核内转录因子 inhibit，三区室布局；pathway_check 5 项断言全过（见 README 自测记录，示例非正式案例结果）。


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

- workorder 类型: `biological_mechanism_pathway`；spec 文件命名: `diagram_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。


## 附录 D 相互作用动词→语义映射表（Step 2 执行细则）

| 材料动词短语 | type | 视觉 |
|---|---|---|
| 促进/激活/上调/增强 | activate | 黑色实心三角箭头 |
| 抑制/下调/阻断/阻滞 | inhibit | 红色 T 形端箭头 |
| 结合/相互作用/复合 | bind | 双端短线/菱形 |
| 磷酸化/泛素化/乙酰化 | modify | 箭头+标签(P/U/Ac) |
| 转运/易位/入核/分泌 | transport | 跨区室箭头 |
| 组成/包含/位于 | contain | 嵌套区室 |
| 促进(方向不明) | neutral | 灰色开口箭头+uncertainty |

- 被动句翻转："B 被 A 抑制" → A→B inhibit；"A 的表达受 B 调控" → B→A，方向按调控词定。
- 图例必须列出图面出现的每种 type；未出现的语义不进图例（防图例-图面不一致）。

## 附录 E 数据编码（若材料含表达量/显著性）

- 颜色编码表达量：datamap.tsv 逐项值+来源；图例加连续色条说明范围；数值标签照抄 datamap。
- 显著性标记：材料给出 p 值才可标 */**/***（阈值注明）；材料没给 → 不标显著性星号。
