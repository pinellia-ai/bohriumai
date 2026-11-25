---
name: editable-relationship-schematic
description: |
  科研示意图生成与编辑（workorder: editable_relationship_schematic）。从来源材料抽取实体—关系—数据—图面约束，生成分层可编辑 SVG 源文件与 PNG/PDF 导出件；每个图元带 id 与 data-source 来源定位，导出前跑合规校验；材料外内容一律标 unverified，不虚构实体、数值或单位。
---

# 可编辑关系示意图 Skill（editable-relationship-schematic）

## 1. 用途与适用范围

- 用途：把实验流程、结构关系、机制链条从文字/表格材料变成"实体画对、关系画对、可编辑、可复核"的示意图。
- 输入：/input/case.json + task.md + 科研材料（PDF/CSV/文本，路径见 case.json）。
- 输出：分层 SVG 源文件（文字未转曲、按层分组）+ PNG/PDF 导出件 + result.json（含来源映射与导出检查）。
- 不做：统计方法选择、海报版式美化、论文正文写作。数值统计图请走 chart_builder 路线（§3 Step 4B）。
- 硬约束：图上不得出现材料中不存在的基因名、浓度、时间点、单位；每个图元可追溯。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：记录 case_id（原样保留）、材料清单、output_contract 全字段。把 output_contract 逐字段抄进 work/order.json 的 `contract_fields`。
2. `mkdir -p /app/work /app/output`；先写最小 result.json 骨架（status=running, case_id）到 /app/output，保证中断也有产物。
3. 盘点材料：逐个打开（PDF 用 pdf-text-tool，表格直接读）。材料缺失 → result.json 写 status=failed + missing_materials，终止（不虚构）。
4. 在 task.md / case.json 中定位 workorder 类型与导出要求（格式、尺寸、分辨率）；缺失时按默认：SVG+PNG(300dpi)+PDF。

验收：order.json 存在，含 case_id、contract_fields、材料路径清单。

## 3. 工作流程

### Step 1 实体—关系抽取（防"画错"的关键）

对每份材料逐段读，产出三个 TSV 到 /app/work：

- `entities.tsv`：`id, name, type(基因/蛋白/复合物/细胞/区室/步骤/部件), attrs, source_location`
- `relations.tsv`：`id, from, to, type(activate/inhibit/bind/modify/transport/contain/parallel), evidence_text, source_location`
- `datamap.tsv`：`item, value, unit, source_location`（图中要标的任何数值）

规则：
- source_location 必须是可复查的位置（文件名+页码/段落/行号/单元格），抄原文短语进 evidence_text。
- 材料里只有"促进/上调"没有方向箭头语义时，direction 按 evidence 判定；判定依据不足 → type 写 `neutral` 并在 result.json 记 uncertainty。
- 抽取完做**清单复核**：relations.tsv 的每个 from/to 必须存在于 entities.tsv；数值必须与材料逐字符一致。

验收：三表行数>0；`python3 scripts/qa_extract.py entities.tsv relations.tsv datamap.tsv` 通过（检查悬空引用与空 source）。

### Step 2 图面规划（布局与语义约束）

写 /app/work/layout_plan.json：
- 区室/分组：包含关系用 compartments 表达，不画成并列。
- 关系语义映射（固定约定，写进图例）：activate=实心三角箭头、inhibit=竖线端点红色箭头、bind=双向菱形或双线、contain=嵌套框、时序=带编号箭头。**箭头方向=因果方向**，上下游颠倒视为错误。
- 布局规则：上下游从左到右/从上到下；节点间距≥40px；文字不溢出框；引导线不交叉（无法避免时用折线绕行）。
- 每个节点/边/区室标注 source_location。

### Step 3 生成 spec 并渲染（源文件优先）

把 layout_plan 转成 diagram spec（JSON，字段见 scripts/svg_builder.py 头注释），然后：

```bash
python3 $SKILL_DIR/scripts/svg_builder.py /app/work/diagram_spec.json --outdir /app/output
```

产出：`<title>.svg`（分层可编辑源文件：layer-background/structure/data/annotation/legend，文字为 <text> 节点可改）、`.png`（300dpi 位图）、`.pdf`。
spec 中每个元素的 `source` 字段填 Step 1 的 source_location；材料外元素（纯版式如底色）填 `figure-own`。

### Step 4B（可选）数据图表部分

若 workorder 还要求依据数据表出图（source_value_chart 情形），用：

```bash
python3 $SKILL_DIR/scripts/chart_builder.py /app/work/chart_spec.json --outdir /app/output
```

要求：y 轴含单位、误差线含义（SD/SEM/95%CI）写明、柱高=值线性映射（SVG 内 data-value/data-row 可回溯 CSV 行）、禁止截断基线（bar 从 0 起）。

### Step 5 导出校验（硬门槛，不过不算完成）

```bash
python3 $SKILL_DIR/scripts/export_check.py --svg /app/output/<title>.svg --png /app/output/<title>.png --pdf /app/output/<title>.pdf --legend-n <图例项数>
```

全部 PASS 才继续；FAIL 先修 spec 再重跑。校验项：文字未转曲、图元带 id+data-source、分层结构、字体声明、图例项数一致、PNG≥1500px、PDF 可打开。
人工检查（把 PNG 渲染给自己看一遍）：重叠、文字溢出、箭头方向、区室归属、中文乱码（乱码→换 FIG_CJK_FONT 指向可用 CJK 字体重渲染，并在 result.json 记 font_used）。

### Step 6 result.json 与 provenance

/app/output/result.json 字段（对应 output_contract，逐字段落实）：

```json
{
  "case_id": "<原样>",
  "status": "complete | partial | failed",
  "editable_source": {"svg": "path", "layers": ["background","structure","data","annotation","legend"], "text_editable": true},
  "exports": [{"format": "png", "path": "...", "dpi": 300}, {"format": "pdf", "path": "..."}],
  "entity_relation_map": {"entities_tsv": "/app/work/entities.tsv", "relations_tsv": "/app/work/relations.tsv", "n_entities": 0, "n_relations": 0},
  "source_verification": [{"element": "e-1", "claim": "A 激活 B", "source": "材料§3 p2: 'A磷酸化B'", "verified": true}],
  "export_check": {"pass": true, "checks": ["...校验输出..."]},
  "uncertainty": ["方向依据不足的边: e-3"],
  "change_log": [{"ts": "...", "change": "v1 初版", "reason": ""}]
}
```

验收：status 与实际一致；partial 必须列出 limits；所有 listed 文件真实存在。

## 4. 输出契约

- 逐字段对照 /input/case.json 的 output_contract：contract 里每个字段都必须出现在 result.json，没有数据的字段写 null + uncertainty 说明，不得删字段。
- 三大交付（题面要求）：可编辑源文件 / 导出件（带格式、尺寸、分辨率、字体、色彩检查结果）/ 来源与修改记录（元素来源、版本、数据映射、异常说明）。

## 5. 数字门槛

- 实体/关系/数值 100% 有 source_location；无来源图元数 = 0（版式元素除外，标 figure-own）。
- export_check 全 PASS；PNG ≥300dpi；SVG 文字节点 >0。
- 达不到 → status=partial，写明缺什么。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 材料缺失/损坏 | status=failed，missing_materials 列清单，不虚构 |
| 关系方向不明 | 画 neutral 箭头 + uncertainty 记录，不擅自补方向 |
| 实体名称歧义（基因 vs 蛋白） | 按材料原写法，大小写/斜体约定照抄 |
| 数据与图例不符 | 以数据为准改图例；矛盾无法解决 → partial |
| 字体缺失/中文乱码 | FIG_CJK_FONT 指定 CJK 字体重渲染；仍失败 → partial + font_used 记录 |
| 渲染/导出失败 | 降级只交 SVG（可编辑源仍是完整交付），exports 里如实标 null |
| 材料间矛盾 | 不选边站，result.json 记录矛盾双方位置与内容 |

## 7. 自查清单

- [ ] case_id 原样；output_contract 字段全覆盖
- [ ] entities/relations/datamap 三表齐全且 qa_extract 通过
- [ ] SVG 分层、文字可编辑、每图元带 data-source
- [ ] 箭头方向=材料因果方向；区室=包含而非并列
- [ ] 图例与图中语义映射一致；无材料外实体/数值
- [ ] export_check 全 PASS；PNG/PDF 真实存在
- [ ] result.json status 如实；uncertainty 与 change_log 已填

## 8. 效率约束（64 请求 / 900s）

先落最小 result.json（Step 0）；抽取与绘图一次成型，不做风格迭代；PNG/PDF 校验失败最多修复 2 轮；超过预算即交 partial。总文件数 ≤50。

## 9. 最小示例

输入 spec（示意，非正式案例结果）：节点 EGFR→RAF activate，来源"材料§3 p2"。调用 `svg_builder.py spec.json --outdir out` → demo.svg/demo.png/demo.pdf，export_check 全 PASS（见 scripts 头注释与 README 自测记录）。


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

- workorder 类型: `editable_relationship_schematic`；spec 文件命名: `diagram_spec.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。


## 附录 D 关系类型视觉语法（Step 2 固定约定补充）

| 材料表述 | relations.type | 视觉 |
|---|---|---|
| A 促进/驱动/触发 B | activate | 黑实心三角箭头 |
| A 抑制/阻断 B | inhibit | 红 T 形端箭头 |
| A 与 B 结合/互作 | bind | 双端短线 |
| A 在 B 内/包含 | contain | 嵌套框 |
| 步骤 1→2→3 | 时序 | 编号+箭头 |
| 并联/两条途径 | parallel | 分叉双线 |

## 附录 E 编辑保留性自检（"改一个标签不用重画"验证）

1. 打开 SVG：图元按 layer-* 分组；节点/边/图例均有语义 id。
2. 改任意 `<text>` 内容保存 → 重跑 export_check 仍 PASS（文字未转曲的可编辑证据）。
3. 数据更新重绘：改 datamap/spec 中数值 → chart_builder/svg_builder 重跑 → verify_map 一致。
