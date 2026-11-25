# challenge-32c0210d 学位论文与长文档写作 v1（弱项加重版）

前人均分 53.3，本版按"写重"策略交付：三级章节树+字数预算+跨章一致性检查+依赖表+版本留痕，五套产物。

## 交付标准清单（自题面提取）

- 立得住：章节规划与提纲、论证链条、字数分配对应——三级章节树（章/节/小节），每个叶子小节登记论证任务+证据+字数预算，预算总和受控。
- 连得上：术语表/符号表/定义清单/结论清单四张底账；跨章一致性检查（术语同写、编号连续、图表引用有效、前后结论一致）；dependency-map 改动一处定位受影响段落。
- 改得动：最小改动，保留作者原句与机器改写句差异标记（EDIT 标记），changelog 可回退可比较。
- 查得清：论断-文献绑定、改动追溯版本记录。
- 必备论证要素：研究问题/方法/结果/讨论/局限 5/5；著录项：图表/参考文献/附录。
- 本版题面修订：organizer-edit-workorder 划定编辑目标；W16 提供分节可编辑工作稿而非成品论文——skill 明确按工作稿处理，不冒称完成整篇论文。
- result.json 落实 output_contract 全字段 + case_id。

## 组件

- SKILL.md：七步流水线（章节树→四张底账→成稿/改稿→依赖表→一致性检查→changelog→交付）。
- scripts/check_thesis.py：7 项校验——标题层级不跳级、图表编号连续、C-n/M-n/R-n 悬空、术语禁用变体、字数预算达成。

## 自测记录

1. YAML frontmatter 结构校验：PASS（name=thesis-longdoc-writer）。
2. output_contract 覆盖：thesis/chapter-tree/glossary/consistency-report/changelog 等产物 + fact_source_map（含 conclusion_id）+ version_and_boundaries 全覆盖。PASS。
3. 脚本实跑两轮：
   - 缺陷版稿件正确拦截 5 项（Fig-2 缺号、R-2 悬空、禁用变体"CNN网络"、字数偏差 43.6%）。
   - 修复过程中发现并修正脚本自身 bug（C-n 使用模式捕获缺前缀导致误报），修正后重测。
   - 修复版 7 项全 PASS（exit=0）。拦截能力与预算门槛均验证。
4. 资源限额：3 文件约 13KB ≤2MB。PASS。
