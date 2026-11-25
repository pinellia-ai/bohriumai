# README — challenge-98e5a474 科研示意图生成与编辑（v1）

## 交付标准清单（从题面 output_contract 提取）

1. **可编辑源文件**：分层 SVG（layer-background/structure/data/annotation/legend），文字为 `<text>` 节点未转曲、可改可替换字体；实体、关系、图例、数据映射正确。
2. **导出件**：PNG（300dpi，≥1500px）+ PDF；含格式/尺寸/分辨率/字体/色彩检查结果（export_check.py 输出）。
3. **来源与修改记录**：entities/relations/datamap 三 TSV（每行带 source_location）、result.json 的 source_verification/change_log/uncertainty。
4. result.json 逐字段落实 output_contract + case_id 原样；status 如实（complete/partial/failed），partial 必须列 limits。
5. workorder 类型：editable_relationship_schematic——真实可编辑 SVG/PNG/PDF + 源保留编辑；科学判断由 LLM Judge 评，不做导出蒙混。
6. GITHUB_URL.txt：如无公开仓库则不放置（题面附加分项，不伪造）。

## 文件清单

- SKILL.md：六步流水线（识别→抽取→布局→渲染→校验→result）
- scripts/core_g.py：SVG 原语库（图元强制 id+data-source）
- scripts/svg_builder.py：spec→分层 SVG+PNG+PDF
- scripts/raster.py：PIL 光栅化（PNG 与 SVG 同源渲染）
- scripts/chart_builder.py：数据表→柱/线/散点图（含误差线与 data-value 映射）
- scripts/export_check.py：导出合规校验（10 项检查，FAIL 即退出码 1）
- scripts/qa_extract.py：抽取质检（悬空引用/空来源/数值格式）

## 自测记录（2026-11-24 本机实跑）

1. YAML frontmatter 解析：OK（name=editable-relationship-schematic）。
2. output_contract 覆盖：可编辑源文件/导出件/来源与修改记录 → result.json §Step6 模板三块齐备。OK。
3. 脚本语法 `ast.parse`：core_g/svg_builder/raster/export_check/chart_builder/qa_extract 全过。
4. 实跑：
   - svg_builder 最小 spec（2 节点 1 边 2 图例+区室）→ svg/png(3750x2500px 300dpi, PingFang.ttc)/pdf 全生成。
   - export_check → pass:true，10/10 PASS。
   - chart_builder CSV 3 行柱图 → svg/png/pdf 全生成，export_check pass:true。
   - qa_extract 悬空引用/空来源负例与正例 → 正例 pass，负例正确报错。
5. 资源限额：7 文件，约 42KB ≤ 50 文件/2MB。OK。
6. 无虚构：SKILL 不含题面外字段；示例标注"示意"。

## 边界与维护

- PNG 光栅化在无 CJK 字体环境可能方框：设 FIG_CJK_FONT 环境变量指向可用字体；result.json font_used 如实记录。
- export_check FAIL 时不允许交付，先修 spec。
