# challenge-041f89c5 科研选题与创新性评估 v1

## 交付标准清单（自题面提取）

- [x] output_contract 三块：研究产物（问题定义/比较/创新/可行性四项一致）、证据矩阵（comparison_matrix：五维+locator+纳 closeness）、不确定性（conflicts/assumption/unverifiable 不越界）
- [x] result.json 含 case_id + status
- [x] 突破方向覆盖：问题定义（PICO+可证伪条件，不可证伪显式标注）、已有工作比较（五维矩阵+相近/迁移/不可比判定）、创新点识别（四类型+逐条 verdict+checked_dims）、可行性判断（前提 verified/assumption/unverifiable 三分+条件+风险）、证据回链与冲突（登记表+取信理由）
- [x] 禁语机制：novel 只允许"给定材料范围内未见"，校验器硬卡"尚无人研究"
- [x] 脚本实跑通过（含坏数据抓错）

## 自测记录（2026-11-24）

1. YAML frontmatter PASS；name=research-topic-novelty-assessor。
2. output_contract 字段 100% 覆盖：PASS。
3. ast.parse：novelty_check.py PASS。
4. 构造工件实跑（PICO 定义 + 2 行矩阵 + 1 创新点 + 2 前提）：
   - verdict=pass；注入"尚无人研究"伪条目 → fail 抓出禁语+novel 缺 checked_dims 两处：PASS
5. 无虚构：novel 语义限定材料范围；assumption 不允许带 source：PASS

## 调用方式

```bash
# Agent 五步执行，产物落 /app/work：problem_definition.json / comparison_matrix.csv / novelty_check.json / feasibility.json
python3 scripts/novelty_check.py --work /app/work --out /app/work/ncheck.json
# verdict=pass 后汇总写 /app/output/result.json（schema 见 SKILL.md §4）
```

## 边界与限制

- novelty 判定范围 = case 给定文献集/材料；开放检索仅在 case 提供检索工具时进行，否则 uncertainty 声明。
- 可行性不评估实验科学性本身，只核查前提链。
