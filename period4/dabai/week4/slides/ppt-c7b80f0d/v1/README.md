# README — ppt-c7b80f0d 论文转学术 PPT（v1）

## 交付标准清单（从题面提取）

题面：论文转学术 PPT，3 个固定案例，输出要求三块 + Harbor 运行契约。

| # | 要求 | 来源 | 落实位置 |
|---|---|---|---|
| 1 | 提取研究问题/方法/结果/限制形成主线 | 任务① | SKILL.md Step 2（四要素模板+locator） |
| 2 | 设计页级主张、图表引用、讲解顺序 | 任务② | Step 3（slides_plan schema：claim/figure/role） |
| 3 | 按模板生成可编辑演示文件及讲稿/备注 | 任务③ | Step 4（plan_to_pptx.py，备注含[主张][证据]） |
| 4 | 每页保留论文定位并检查导出渲染 | 任务④ | Step 6（evidence_lint.py + export_check.py） |
| 5 | 输出：可编辑演示文件 | 输出要求表 | result.json deliverables.source_pptx |
| 6 | 输出：页级证据映射（引用准确未改写事实） | 输出要求表 | result.json slides[].evidence + 数字保真校验 |
| 7 | 输出：渲染与版本记录 | 输出要求表 | result.json coverage.export + version_log |
| 8 | result.json 含 output_contract 全字段 + case_id | Harbor 契约 | SKILL.md §4 契约表 |
| 9 | 先落盘最小 result.json，逐步充实 | Harbor 契约 | Step 0 result_scaffold.py |
| 10 | 可编辑产物需有真实渲染 PDF/PNG 预览 | Harbor 契约 | Step 5 导出 PDF + export_check 页数一致 |
| 11 | 材料缺失/无法判断/运行失败分别说明 | 题面 | gaps / uncertainty / status=failed 分离 |
| 12 | ≤50 文件 2MB，无 symlink；64 请求 900 秒 | Harbor 契约 | §8 效率约束 |
| 13 | 六类要素覆盖：主线/页结构/图表引用/讲解逻辑/模板约束/导出渲染 | 题面评分 | result.json coverage 六键 |

## 目录结构

```
v1/
├── SKILL.md            # Agent 操作手册（§3 结构，YAML frontmatter）
├── README.md           # 本文件
└── scripts/
    ├── result_scaffold.py   # 最小 result.json 落盘
    ├── plan_to_pptx.py      # 页级计划 → 可编辑 pptx（模板继承+备注溯源）
    ├── evidence_lint.py     # 证据映射/数字保真/六要素校验
    ├── export_check.py      # pptx 完整性 + PDF 页数一致性
    └── deck_diff.py         # （复用工具）两版计划逐页 diff
```

## 自测记录（2026-11-24，本地 macOS，python 3 + python-pptx 1.0.2）

| 项 | 结果 |
|---|---|
| YAML frontmatter 解析 | PASS（name=paper-to-academic-slides，与目录用途一致） |
| output_contract 覆盖 | PASS（题面"输出要求"3 块 + Harbor case_id/status/sources/uncertainty 全落实） |
| 脚本语法 ast.parse ×5 | PASS |
| plan_to_pptx 实跑（3页计划→deck.pptx） | PASS（slide_count=3，备注齐） |
| plan_to_pptx 坏 schema（缺 claim） | PASS exit 4 拒绝 |
| evidence_lint 正例 | PASS exit 0 |
| evidence_lint 数字篡改（92.3%→93.0%） | PASS exit 1 正确拦截 |
| export_check 无 PDF / 假 1 页 PDF（3 页 deck） | PASS exit 3 正确告警 |
| result_scaffold 新建/保留已存在 | PASS |
| template_audit / fit_check / deck_diff 实跑 | PASS |
| 资源限额 | 7 文件 ≈30KB ≤50/2MB |
| SKILL.md 行数 | 168 行（150-400 达标） |

## 已知限制

- 本地无 LibreOffice，PDF 导出命令在评测环境以 resources.yaml 提供的工具为准；
  导出失败时按 §6 处置（coverage.export=partial，不伪造 PDF）。
- evidence_lint 的数字保真是子串级匹配（防取整/改写），非语义校验。
