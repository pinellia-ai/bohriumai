---
name: sci-kb-grounded-qa
description: |
  科研知识库问答 Skill：在本地多文件知识库（跨目录/跨格式/含重复副本与历史版本）上完成"检索→带来源引用的问答→证据回链→不确定性提示"的完整交付。
  方法主线：建段落级索引（含版本/副本归并）→查询改写与同义扩展→多块检索→逐句证据绑定（每个关键论断配 文件+版本+页/段+原文片段）→
  分级置信（proven/indicative/unresolved）→证据不足时明确答"知识库中没有依据"并说明缺什么。全程离线、引用真实、可被他人按记录复跑。
---

# 科研知识库问答（Grounded QA with Evidence Links）

## 1. 用途与适用范围

- **做**：对库内文件回答科研问题，答案的每个关键论断都能落到具体文件+版本+段落；库内无依据时如实说"没有"并说明缺口。
- **不做**：开放网络检索、无中生有的推断、权限绕过。
- **验收三件事**：论断↔原文片段一一对应；缺证敢说没有；他人可按记录重走同样问答。

## 2. 输入识别（Step 0，必做）

1. 读 `/input/case.json`：case_id 原样保留、知识库目录、问题清单（单个或多个问题）、输出要求。
2. 盘点库：文件数、可读数、重复副本组、版本链（复用哈希分组）。
3. 库为空 → status=failed。

## 3. 工作流程（六步）

### Step 1 建索引（`kb.py build` → kb_index.json）
- 全格式文本抽取（txt/md/csv/pdf/docx/xlsx），段落级切块，保留页码/章节/首句。
- **副本与版本归并**：同 sha256 副本只留主路径索引（其余记 alias）；命名递进异哈希建版本链，检索时**优先最新版**，旧版命中标注版本号。
- 扫描件无文本层记 `coverage_gap`（答案里声明"这部分内容不在可检索范围"）。

### Step 2 查询改写（模型辅助，≤2 次/问题）
把自然语言问题改写为：核心概念词集（中文+英文+缩写）、限定条件（年份/项目/文件类型）、问题类型（事实型/比较型/定位型）。

### Step 3 检索（`kb.py answer`）
同义扩展→多块打分检索→取 top-k（k=8）；同义扩展词、过滤路径、各文件命中数记入检索记录（复跑依据）。

### Step 4 证据绑定与作答（模型，≤3 次/问题）
- 每个关键论断必须绑定至少一条证据：`{claim, evid_id, locator{path,version,page,para,first_sentence,snippet}}`。
- 证据强度分级：**proven**（原文直接陈述）/ **indicative**（原文部分支持，需推断）/ **unresolved**（库内证据不足或互相冲突）。
- 证据互相冲突时不取一方：并列给出双方原文位置，标 `conflict`。
- 不引入证据片段之外的数字/结论；推断必须显式标 indicative 并写推断链。

### Step 5 缺证判定
- 检索 top-k 得分低于阈值或无相关块 → `answer="知识库中没有找到支持该问题的依据"`，`missing_evidence` 写明：检索过的词、覆盖的文件范围、可能需要的文件类型。
- **禁止**把"检索不到"答成"知识库没有该事实"以外的话（如泛泛科普）。

### Step 6 汇总与复跑记录（→ /app/output/result.json + retrieval_log.json）
retrieval_log 记录：每个问题的改写词、扩展词表、检索范围、top-k 块 id、得分——他人可按日志重走。

## 4. 输出契约（result.json 逐字段）

```json
{
  "case_id": "原样保留",
  "status": "ok|partial|failed",
  "kb_overview": {"files": 0, "readable": 0, "duplicate_groups": 0, "version_chains": 0, "coverage_gaps": ["扫描件x.pdf 无文本层"]},
  "answers": [{
    "question": "原始问题",
    "answer": "带引用的回答文本（论断以 [E1] [E2] 标注）",
    "claims": [{"claim": "缓冲液配方为 137 mM NaCl", "confidence": "proven|indicative|unresolved",
                 "evidence": [{"evid_id": "E1", "path": "...", "version_label": "v2", "page": 3, "para_idx": 4,
                                "first_sentence": "...", "snippet": "...", "locator": "path#page=3,para=4"}]}],
    "conflicts": [{"topic": "...", "evidence_a": "E1", "evidence_b": "E3", "note": "..."}],
    "missing_evidence": {"triggered": false, "searched_terms": [...], "scope": "...", "suggestion": "..."}
  }],
  "operation_evidence": {"kb_index": "kb_index.json", "retrieval_log": "retrieval_log.json",
                          "hash_algo": "sha256", "rerun_cmd": "kb.py build→kb.py answer"},
  "uncertainty": ["印刷页码未对齐时 page 为物理页", "双栏PDF段序为抽取顺序"]
}
```

## 5. 数字门槛

- 引用真实率 100%：每条 evidence 的 snippet 必须能在源文件逐字找到（抽查 3 条）。
- 无证不答：任何 claim 无 evidence → 该 claim 降 unresolved 并触发 missing_evidence 检查。
- 覆盖：库内与问题相关的多份文件都被检索记录覆盖（不只命中一份就下结论）。

## 6. 异常处理表

| 情况 | 处置 |
|---|---|
| 文件不可读/无权限/加密 | coverage_gap 声明，不猜内容 |
| 扫描件无文本层 | 同上 |
| 版本冲突命中 | 优先最新版 + 旧版并列标注 |
| 证据互相矛盾 | conflict 并列呈现，不取一方 |
| 检索为空 | missing_evidence 如实报告 |
| 目录为空/路径失效 | status=failed + 原因 |

## 7. 自查清单

- [ ] case_id 原样；每条论断有证据且可回链。
- [ ] 缺证问题答"没有依据"并说明缺什么。
- [ ] retrieval_log 完整，他人可复跑。
- [ ] 副本/旧版未当独立证据。

## 8. 效率约束

索引与检索脚本化；模型请求：每问题改写 1 次 + 作答 1 次，多问题案例总计 ≤16 次。先落最小 result.json（kb_overview + 首问答案），再补全其余问题。

## 9. 最小示例（示意输出，非正式案例结果）

问题："这个体系的缓冲液配方写在哪一版？"
答案："缓冲液配方（137 mM NaCl / 2.7 mM KCl / pH 7.4）记录在 protocol_v2 [E1]，v1 中该节为'待更新'占位 [E2]。"
E1.locator = "实验记录/P-2023-015/protocol_v2.pdf#page=3,para=4"（snippet 含原句）。
