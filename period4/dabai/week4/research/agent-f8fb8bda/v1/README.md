# agent-f8fb8bda 深度研究 Agent v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：研究产物（synthesis 结论与证据范围一致）、证据矩阵（evidence_table：来源/定位/比较字段）、不确定性（conflicts/gaps/unverifiable 不越界）
- [x] result.json 含 case_id + status + material_fact/inference/unverifiable 三分
- [x] 突破方向覆盖：问题拆解（sq 可独立检索+依赖标注+成环检测）、检索规划（顺序/停止条件/去重）、多步工具调用（tool_calls.jsonl 参数与返回留痕）、证据综合（结论句↔证据行、冲突并列、强度三档）
- [x] 研究空白基于检索缺口（queries_tried 必填）
- [x] 脚本实跑通过（含坏数据抓错验证）

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=deep-research-agent。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：pipeline_check.py PASS。
4. 构造最小工件实跑（3 sq 依赖链 + 3 证据含冲突 + 1 gap）：
   - verdict=pass：依赖无环、计划无重复、回链率 2/2、gaps 有据：PASS
   - 注入假引用 E99 → verdict=fail 并定位"结论句无证据回链"：PASS
5. 无虚构：不发明 benchmark 分数；结论必须 material_fact/inference 标注：PASS

## 调用方式

```bash
# Agent 按 SKILL.md §3 五步执行，产物落 /app/work：
# decomposition.json / search_plan.json / tool_calls.jsonl / evidence_table.json / synthesis.json / gaps.json
python3 scripts/pipeline_check.py --work /app/work --out /app/work/check.json
# check.json verdict=pass 后汇总写 /app/output/result.json（schema 见 SKILL.md §4）
```

## 边界与限制

- 每 sq 检索 ≤3 次降级链（换词→换源→unresolved）；冲突只并列不裁决。
- 工具调用与 trace 由平台记录，本 skill 不伪造分数。
