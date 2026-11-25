#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""screen — 候选文献逐条纳排筛选与可解释排序（真实可运行，仅标准库）。

用法：
  python3 screen.py --candidates /app/work/candidates.jsonl --criteria /app/work/criteria.json --workdir /app/work

criteria.json 结构（由 Agent 在筛选前依据题面/研究问题显式化，全部判据必须可判定）：
{
  "include": [{"code": "I1", "criterion": "研究对象为……", "must_terms": ["term1", "term2"]}],
  "exclude": [{"code": "E1", "criterion": "非原始研究（综述/评论/社论）",
               "must_terms": ["review", "editorial", "commentary"]}],
  "pending_rule": "两条以上判据无法判定 → pending，写明缺什么证据",
  "core_must": ["term"]            // 可选：核心证据必须命中的词
}

输出：
  screening.jsonl  每条 {record_id, decision(included|excluded|pending), reason_code,
                       evidence_quote(原文摘录), hit_criteria, confidence}
  ranked.json      仅 included 按 (是否核心证据, 命中判据数, BM25 分) 排序 + 平局说明
退出码 0；2 表示缺输入。
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def _norm_tokens(cands):
    toks = set()
    for t in cands:
        toks |= set(SL.tokenize(t))
    return toks

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--criteria", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    for p in (args.candidates, args.criteria):
        if not os.path.exists(p):
            print("missing input: %s" % p, file=sys.stderr)
            return 2

    cands = SL.load_jsonl(args.candidates)
    with open(args.criteria, encoding="utf-8") as fh:
        cri = json.load(fh)
    rows, tie_notes = [], []
    for c in cands:
        text = " ".join(str(v) for v in c.get("fields", {}).values())
        title = c.get("fields", {}).get("title", "")
        basis = c.get("relevance_basis") or []
        quotes = " | ".join(b.get("quote", "") for b in basis[:2]) or title[:120]
        inc_hits, exc_hits, pend = [], [], []
        for rule in cri.get("include", []):
            toks = _norm_tokens(rule.get("must_terms", []))
            if toks and toks <= set(SL.tokenize(text)):
                inc_hits.append(rule["code"])
        for rule in cri.get("exclude", []):
            toks = _norm_tokens(rule.get("must_terms", []))
            if toks and toks <= set(SL.tokenize(text)):
                exc_hits.append(rule["code"])
        core_ok = True
        core = cri.get("core_must")
        if core:
            ctoks = _norm_tokens(core)
            core_ok = ctoks and (ctoks & set(SL.tokenize(text))) != set()
        n_inc = len(cri.get("include", []))
        if exc_hits:
            decision, rc = "excluded", exc_hits[0]
            conf = "high"
        elif n_inc and len(inc_hits) == n_inc and core_ok:
            decision, rc = "included", "+".join(inc_hits)
            conf = "high"
        elif inc_hits and core_ok:
            decision, rc = "pending", "partial:" + "+".join(inc_hits)
            conf = "medium"
            pend.append("仅命中 %d/%d 条纳入判据；缺：摘要未覆盖 %s 等判据证据" %
                        (len(inc_hits), n_inc, "+".join(c for c in [r["code"] for r in cri.get("include", []) if r["code"] not in inc_hits])))
        elif not inc_hits and not exc_hits:
            decision, rc = "pending", "undetermined"
            conf = "low"
            pend.append("纳入/排除判据均无法从标题摘要判定，需人工读全文")
        else:
            decision, rc = "excluded", "no_include_match"
            conf = "medium"
        rows.append({"record_id": c["record_id"], "title": title,
                     "source": c.get("source"),
                     "decision": decision, "reason_code": rc,
                     "evidence_quote": quotes[:300], "hit_criteria": inc_hits + exc_hits,
                     "pending_notes": pend, "confidence": conf,
                     "bm25_score": c.get("best_score", 0.0)})

    included = [r for r in rows if r["decision"] == "included"]
    pendings = [r for r in rows if r["decision"] == "pending"]
    excluded = [r for r in rows if r["decision"] == "excluded"]
    included.sort(key=lambda r: (-len(r["hit_criteria"]), -r["bm25_score"]))
    # 平局说明：同分同判据数的并列项
    seen = {}
    for i, r in enumerate(included):
        r["rank"] = i + 1
        key = (len(r["hit_criteria"]), r["bm25_score"])
        seen.setdefault(key, []).append(r["record_id"])
    for key, ids in seen.items():
        if len(ids) > 1:
            tie_notes.append("rank %s并列（判据数=%d, bm25=%.2f）：%s；平局按 record_id 升序稳定排序" %
                             (ids[0], key[0], key[1], ",".join(ids)))
            ids.sort()
    for i, r in enumerate(included):
        r["rank"] = i + 1

    SL.write_jsonl(os.path.join(args.workdir, "screening.jsonl"), rows)
    SL.write_json(os.path.join(args.workdir, "ranked.json"),
                  {"included": included, "pending": pendings, "excluded": excluded,
                   "counts": {"included": len(included), "pending": len(pendings),
                              "excluded": len(excluded), "total": len(rows)},
                  "tie_notes": tie_notes})
    print("total=%d included=%d pending=%d excluded=%d ties=%d" %
          (len(rows), len(included), len(pendings), len(excluded), len(tie_notes)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
