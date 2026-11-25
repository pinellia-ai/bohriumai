# README — ppt-710fbc72 学术 PPT 模板与格式适配（v1）

## 交付标准清单（从题面提取）

| # | 要求 | 来源 | 落实位置 |
|---|---|---|---|
| 1 | 模板套用：母版/版式/占位符识别，内容写入正确版式，保留主题字体色，占位符缺失替代 | 方向① | Step 1 template_audit.py + slot_map；Step 3 必传模板 |
| 2 | 版式约束：版心内定位对齐、溢出、长标题、多图并排、字号间距阶梯 | 方向② | Step 4 fit_check.py（溢出/字号下限/长标题） |
| 3 | 字体颜色：中英搭配、字号层级、主题色、字体缺失回退 | 方向③ | template_audit 主题字体(latin/ea)+§6 字体缺失处置 |
| 4 | 图表适配：等比缩放或裁切、坐标轴图例可读、编号与引用一致 | 方向④ | plan_to_pptx 等比缩放 + figure.ref 规则 |
| 5 | 批量一致性：页脚/页码/标题位置/留白/字号层级统一+文件完整性校验 | 方向⑤ | Step 5 consistency_checklist |
| 6 | 导出渲染横切：pptx 与 PDF/PNG 一致，字体替换/图片丢失/备注错位记录 | 题面明示 | Step 6 export_check + rendering_notes |
| 7 | 输出：可编辑演示文件（真实套用模板） | 输出要求表 | deliverables + template 字段 |
| 8 | 输出：页级证据映射 | 输出要求表 | slides[].evidence + evidence_lint |
| 9 | 输出：渲染与版本记录（逐页偏差记录） | 输出要求表 | version_log + rendering_notes |
| 10 | 母版/版式继承关系可查；可复跑逐页核对 | 题面判断标准 | template_audit.json + slot_map 落盘 |
| 11 | result.json 全字段+case_id；先落盘最小 result.json | Harbor 契约 | §4+Step 0 |
| 12 | 材料缺失/无法判断/运行失败分别说明 | 题面 | gaps/uncertainty/status |
| 13 | ≤50 文件 2MB；64 请求 900 秒 | Harbor 契约 | §8 |

## 目录结构

```
v1/
├── SKILL.md            # 7 步适配流水线（审计→映射→填充→约束→一致性→导出→记录）
├── README.md
└── scripts/
    ├── result_scaffold.py    # 最小 result.json
    ├── template_audit.py     # 模板审计：母版/版式/占位符/主题字体色（本题核心）
    ├── fit_check.py          # 版式约束：溢出/字号下限/长标题（本题核心）
    ├── plan_to_pptx.py       # 槽位填充构建（模板继承+图表等比缩放）
    ├── evidence_lint.py      # 证据映射+数字保真
    ├── export_check.py       # pptx+PDF 页数一致
    └── deck_diff.py          # （复用工具）适配前后逐页 diff
```

## 自测记录（2026-11-24，python 3 + python-pptx 1.0.2）

| 项 | 结果 |
|---|---|
| YAML frontmatter 解析 | PASS（name=template-fit-adaptor） |
| output_contract 覆盖 | PASS（含 template/consistency_checklist/rendering_notes 题面专属字段） |
| 脚本语法 ast.parse ×7 | PASS |
| template_audit 实跑（3页 deck 当模板） | PASS（母版/版式/占位符/尺寸报告正确） |
| template_audit 缺文件反例 | PASS exit 2 |
| fit_check 实跑（无风险 deck） | PASS exit 0 |
| fit_check 构造 8pt 字号溢出文本 | PASS exit 1 拦截（small-font/overflow 机制经反例验证） |
| plan_to_pptx 实跑（有/无模板） | PASS（template_used 报告正确） |
| evidence_lint 正例/篡改反例 | PASS exit 0 / exit 1 |
| export_check 反例（无PDF/页数不一致） | PASS exit 3 |
| 资源限额 | 9 文件 ≈37KB |
| SKILL.md 行数 | 168 行 |

## 已知限制

- fit_check 的溢出判断是字符量启发式（docstring 已声明），非渲染级精判；配合"禁止带 FAIL 交付"门槛使用。
- 页脚/页码一致性依赖模板母版继承（脚本层面由 template_audit 佐证），细粒度像素级校验需环境渲染工具。
- 本地无 LibreOffice；PDF 导出命令在评测环境以 resources.yaml 为准，失败标 partial 不伪造。
