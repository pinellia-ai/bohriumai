# README — challenge-83d4f050 生物机制图与通路图（v1）

## 交付标准清单（题面 output_contract 提取）

1. **可编辑源文件**：分层 SVG（5 层，文字未转曲）；实体/关系/图例/数据映射正确。
2. **导出件**：PNG 300dpi + PDF；格式/尺寸/分辨率/字体/色彩检查（export_check 10 项）。
3. **来源与修改记录**：entities.tsv + relations.tsv（每行 source_location + evidence_text）、pathway_check 报告、uncertainty、change_log。
4. workorder：biological_mechanism_pathway——真实可编辑 SVG/PNG/PDF + 源保留编辑。
5. 追溯链：实体清单→边清单→图例依据→源文件→版本→导出参数，独立可复核。

## 关键断言（pathway_check.py，防本赛道常见硬伤）

1. 幻觉实体=0（spec 节点 ⊆ 实体清单）
2. 幻觉边=0 且端点/语义与清单一致
3. 边语义 ∈ 固定枚举（activate/inhibit/bind/modify/transport/contain/neutral）
4. 每图元有非空 data-source
5. 图例类型集合 = 实际使用边类型集合

## 自测记录（2026-11-24 本机实跑）

1. YAML 解析 OK（name=biological-mechanism-pathway）。
2. 脚本 ast.parse 全过（7 个脚本）。
3. 实跑（三区室 demo：膜外/胞质/核，EGFR→RAF activate，RAF⊣TF inhibit）：
   - pathway_check 负例：构造不在清单的 e3/r2 → 正确报"幻觉节点/幻觉边"并 exit 1。
   - pathway_check 正例 → pass:true；qa_extract pass；svg_builder → svg+png(3750x2500,300dpi,PingFang)+pdf；export_check pass:true（--legend-n 2）。
4. 资源限额：8 文件 ≈ 51KB。OK。
5. 无虚构：dataset 引用仅按 retrieval_ref 说明，不编造取材结果。

## 前人 63.7 弱项针对

① 幻觉实体/边用脚本强制清零 ② 语义→箭头映射固定并写进图例 ③ 区室/跨膜位置约束写进布局规则 ④ 被动句方向翻转规则明确。
