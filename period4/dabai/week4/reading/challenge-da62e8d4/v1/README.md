# README — challenge-da62e8d4 论文复现与方法验证 (v1)

## 交付标准清单（从题面提取）

- 本版任务范围（题面开头修订原文）：选定"**参数/代码/指标验算与差异归因**"子场景，实际运行包内**两份候选数值方法**，核对**原始来源、实际环境、事前容差**。组织方合成试验不是原作者代码、物理实验或全量复现；缺失原始数据/仓库明确保留。
- 四关注：找得齐（材料定位到具体版本，缺失显式登记）、跑得对（按论文参数而非默认值）、对得上（偏差落事前容差内）、讲得清（归因到环境/数据/实现/论文描述不足，可独立复核）。
- 输出：`/app/output/result.json`，含 case_id、材料清单、参数表（三级取值依据）、环境、两方法 runs、容差对比、归因、分级结论（reproduced/partially_reproduced/not_reproduced）、缺失项、不确定性、变更记录。

## 文件

- `SKILL.md` — 六步流水线（材料定位→参数复原→环境记录→运行两候选→容差对比归因→分级结论）
- `scripts/tolerance_check.py` — 容差对比计算器：absolute/relative 容差、deviation 可复算、无 declared_at 强制 unverifiable（禁止事后定容差）、reported=0 保护，带 `--selftest`

## 自测记录（2026-11-25）

- [x] YAML frontmatter 可解析
- [x] output_contract 全字段覆盖（material_checklist/parameter_table/environment/runs/comparison/attribution/conclusion/missing_items/uncertainty/change_log）
- [x] tolerance_check.py ast.parse 通过；`--selftest` 实跑四例：容差内 within、超差 out、无容差 unverifiable、reported=0 unverifiable → PASS
- [x] 无虚构：缺失分支/合成数据边界按题面保留
- [x] 资源限额：4 文件 / <30KB
