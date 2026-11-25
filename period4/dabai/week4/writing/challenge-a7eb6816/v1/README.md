# challenge-a7eb6816 写作17｜科研成果转化写作 v1

## 交付标准清单（从题面提取）

- 四重点：读得懂（受众适配）、留得住（删冗余不删证据）、说得准（论断强度匹配源文证据）、接得住（逐段可复核）。
- 评分五维：实际效果 40（改写稿直接可用、事实/数据/图表编号/论断强度与源文一致、逐段对照+删改理由）、使用增益 25、创新增益 15（受众画像→取舍策略→边界标注→多文体映射链条）、可靠体验 10、生态贡献 10。
- 输出契约三件：目标产物（满足指定体裁/受众/格式）、事实与来源映射（逐条回溯）、版本与边界（改动差异/人工确认项/缺口）。
- result.json 含 case_id、honest status、sources、uncertainty、change records；partial 写明边界。
- GitHub 附加分 5 分：GITHUB_URL.txt 第一行写链接（本工作区未建仓，以主仓说明代替；如平台要求单独仓库再补）。
- 资源限额 ≤50 文件 / 2MB。

## 本版方案

SKILL.md 十一节：输入识别（读者/体裁/篇幅/语言四要素，缺项保守默认+uncertainty）→ 受众画像 → 源文拆解三级取舍 → 术语锁定表 → 论断强度四档标注（established/supported/preliminary/speculation）→ 逐段改写 → 逐段对照+改动清单 → 保真校验。
scripts/check_transfer.py：数字保真（支持 missing_reasons 豁免）、图表引用完整、术语唯一三查。

## 自测记录

- YAML 解析通过（name=research-transfer-writing）。
- output_contract 覆盖：case_id/status/deliverable/facts_sources/claim_strength/changes/uncertainty/gaps/limits 全落实 §4。
- 脚本 ast.parse 通过；最小实跑：2 数字过+1 豁免+1 图表丢失+1 术语冲突，报告与退出码符合预期。
- 资源 3 文件约 15KB；SKILL.md 约 145 行。全过。
