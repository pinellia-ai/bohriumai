---
name: graphical-abstract-builder
description: |
  Graphical Abstract（workorder: graphical_abstract）。单页内按"问题→方法→结果→结论"四段视觉压缩：面板—要点映射先于画图，实体/关系/数值逐项溯源，核心结果用颜色/长度编码并与图例一致，分层可编辑 SVG + 300dpi PNG/PDF 导出；同输入可稳定复现同一版式结构。
---

# 图形摘要 Skill（graphical-abstract-builder）

## 1. 用途与适用范围

- 用途：把一篇研究的问题、方法路线、核心结果、结论压缩成单页自洽视觉摘要（论文/基金/汇报用）。
- 不做：论文正文写作、统计分析、实验设计。
- 核心判据：①实体/关系/数值可追到来源 ②同输入复现同结构 ③可编辑源文件交付。

## 2. 输入识别（Step 0，必做）

1. 读 /input/case.json（case_id 原样、output_contract 全字段抄 order.json）；最小 result.json 先落盘。
2. 盘点材料：研究描述/摘要/实验记录/结果表；提取目标规范（画布尺寸如 1200×900 或期刊模板、导出格式）。材料缺失→failed。
3. 若材料缺"核心结果数值"，GA 只画到方法与定性结论，results 面板标 "no quantitative result in source"——**不得编造数字**。

## 3. 工作流程

### Step 1 面板—要点映射（先定内容再定版面）

写 /app/work/storyboard.json，四面板各 1-3 个要点，每要点带 source：

```json
{
  "question":  {"points": ["问题P1"], "source": "摘要§1"},
  "method":    {"points": ["方法M1", "方法M2"], "source": "方法§2"},
  "results":   {"points": ["结果R1 (值, 单位, 来源)"], "source": "结果§3 表1"},
  "conclusion":{"points": ["结论C1"], "source": "讨论§4"},
  "must_not_panel": ["仅进图注不入图的信息"]
}
```

规则：每个要点必须能在材料中指到出处；结论不得超出结果支持的范围（结果只支持"A>b"就不写"显著最优"）。

### Step 2 实体与编码规划

- entities.tsv / relations.tsv / datamap.tsv（同 §来源规范，每行 source_location）。
- 视觉通道分配（写入 legend_spec）：颜色→类别或条件组、长度/高度→数值、箭头→因果或流程、面板位置→阅读顺序。**色觉安全**：默认 Okabe-Ito 色板（#0072B2/#E69F00/#009E73/#CC79A7），灰度打印可辨（亮度差>0.3）。
- 每面板配 panel id（A/B/C/D）与 1 行小标题（≤12 字）。

### Step 3 单页渲染

`ga_builder.py storyboard.json entities.tsv datamap.tsv --outdir /app/output`：
- 版式模板（固定结构保证复现）：顶部标题带（研究题目缩写），下方四面板 grid：问题(左上)→方法(右上)→结果(左下, 最大)→结论(右下)；阅读顺序箭头编号 1→2→3→4。
- 结果面板优先用数据图（chart_builder 柱/线图内嵌：误差线含义、y 轴单位、n= 必标）；机制/流程要点用 svg_builder 元语。
- 图例盒放右下：色板含义+箭头语义+误差线定义。
- 字号层级：标题 20 > 面板小标题 14 > 正文 11 ≥ 最小可读 8。

### Step 4 校验

```bash
python3 $SKILL_DIR/scripts/storyboard_check.py storyboard.json entities.tsv datamap.tsv   # 要点溯源/无编造数值
python3 $SKILL_DIR/scripts/export_check.py --svg ... --png ... --pdf ... --legend-n N
```

storyboard_check 断言：① 每要点有非空 source ② datamap 数值与材料引用一致（值/单位字符串比对）③ 四面板齐备 ④ 结论要点可在结果要点或材料中找到支撑（支撑缺失→FAIL）。
人工看 PNG：文字溢出、面板重叠、色板在灰度下是否可分、图例与编码一致。

### Step 5 result.json

```json
{
  "case_id": "<原样>", "status": "complete|partial|failed",
  "storyboard": "/app/work/storyboard.json",
  "editable_source": {"svg": "...", "panels": ["A-question","B-method","C-results","D-conclusion"], "text_editable": true},
  "exports": [{"format": "png", "dpi": 300}, {"format": "pdf", "path": "..."}],
  "trace": {"entities": 0, "datamap_items": 0, "storyboard_check": "pass"},
  "visual_encoding": {"palette": "Okabe-Ito", "grayscale_safe": true},
  "export_check": {"pass": true},
  "uncertainty": [], "change_log": []
}
```

## 4. 输出契约

output_contract 逐字段落实；三大交付=可编辑源文件（分层、面板命名清楚）/导出件（格式尺寸分辨率字体检查）/来源与修改记录（storyboard+三 TSV+校验报告）。

## 5. 数字门槛

- 要点 100% 有 source；编造数值=0（storyboard_check 强制）；图例-编码一致；四面板齐备；同输入重跑版式结构一致（模板固定）。
- export_check 全 PASS；PNG≥300dpi。

## 6. 异常处理表

| 情形 | 处置 |
|---|---|
| 缺结果数值 | results 面板定性描述+uncertainty，不造数 |
| 实体歧义 | 照材料写法+uncertainty |
| 文字溢出 | 缩要点字数（面板要点≤3），字号≥8pt |
| 画布超限 | 按模板比例缩放内容字号，不裁面板 |
| 字体/导出失败 | FIG_CJK_FONT 重试；降级只交 SVG |
| 材料过泛（像信息图） | 严格按 storyboard 四面板裁剪，多余信息进图注 |

## 7. 自查清单

- [ ] 四面板齐、阅读顺序编号、storyboard_check 过
- [ ] 无编造数值；图例=视觉通道一致；灰度可辨
- [ ] SVG 分层面板命名清楚、文字可编辑
- [ ] export_check 全 PASS；result.json 如实

## 8. 效率约束

先最小 result；storyboard 一次成型；版面最多调 2 轮；≤50 文件。

## 9. 最小示例

四面板 demo（问题/方法/结果/结论各 1 要点+1 数据柱图内嵌）→ storyboard_check/export_check 全过（见 README 自测记录，示例非正式案例结果）。


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

- workorder 类型: `graphical_abstract`；spec 文件命名: `storyboard.json`。
- 越界内容一律移交相邻课题：统计方法选择、实验方案设计、论文写作、版式美化。
- 科学判断由评测 Judge 做：本 skill 只保证"可编辑源文件+导出合规+来源可核验"三件套的工程质量。
