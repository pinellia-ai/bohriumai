#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""coverage_audit — 覆盖率与漏检分析（真实可运行，仅标准库）。

用法：
  python3 coverage_audit.py --reference /app/work/reference_set.json \
      --candidates /app/work/candidates.jsonl --records /app/work/records.jsonl \
      --search-log /app/work/search_log.jsonl --workdir /app/work [--supplementary supplementary.json]

reference_set.json：已知相关文献参考集（冻结版本），结构：
  {"version": "...", "frozen_at": "...", "items": [{"title": "...", "doi": "...", "year": ..., "authors": "...", "notes": "..."}]}

supplementary.json（可选）：补充检索查询 [{"query_id":"S1","query":"...","topk":20}]

输出 coverage.json：
  reference_total / hits（逐条命中状态+判定方法）/ missed（逐条漏检+原因码+归因到查询与字段）/
  coverage_rate / supplementary_gain（补检新增命中与边际收益）/ residual
退出码 0；2 参考集缺失。
"""
import argparse, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--records", required=True)
    ap.add_argument("--search-log", required=True)
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--supplementary", default=None)
    args = ap.parse_args()
    if not os.path.exists(args.reference):
        print("reference set missing", file=sys.stderr)
        return 2

    with open(args.reference, encoding="utf-8") as fh:
        ref = json.load(fh)
    cands = SL.load_jsonl(args.candidates)
    records = SL.load_jsonl(args.records)
    slog = SL.load_jsonl(args.search_log)
    all_corpus = records

    cand_ids = {c["record_id"] for c in cands}
    hits, missed = [], []
    for item in ref.get("items", []):
        rid, method = SL.hit_match(item, all_corpus, strict_year=False)
        entry = {"title": item.get("title"), "doi": item.get("doi"),
                 "target_record_id": rid, "hit_method": method}
        if rid:
            entry["matched"] = True
            entry["in_candidates"] = rid in cand_ids
            if rid not in cand_ids:
                entry["miss_reason"] = "corpus_hit_but_not_retrieved"
                entry["attribution"] = "命中语料但未进入候选集：查询式未覆盖其用词或排序截断，见 search_log 对应轮次"
                missed.append(entry)
            else:
                hits.append(entry)
        else:
            entry["matched"] = False
            has_doi = bool(item.get("doi"))
            entry["miss_reason"] = SL.classify_miss("no_doi" if not has_doi else "")
            entry["in_corpus"] = False
            entry["attribution"] = ("参考集条目无有效标识符且标题近似匹配失败：标识异常或语料未收录" if not has_doi
                                    else "语料内无 DOI/标题近似匹配：来源库未收录该条或字段异常")
            missed.append(entry)

    cov_rate = round(len(hits) / max(1, len(ref.get("items", []))), 4)
    supp_gain = []
    if args.supplementary and os.path.exists(args.supplementary):
        with open(args.supplementary, encoding="utf-8") as fh:
            supp = json.load(fh)
        idx = SL.Index(all_corpus)
        pre_ids = set(cand_ids)
        for s in supp.get("queries", []):
            ranked, _m = idx.search(s["query"], topk=int(s.get("topk", 20)))
            new_hits = [all_corpus[i]["record_id"] for sc, i in ranked
                        if all_corpus[i]["record_id"] not in pre_ids]
            supp_gain.append({"query_id": s["query_id"], "query": s["query"],
                              "new_candidate_count": len(new_hits),
                              "new_record_ids": new_hits[:30],
                              "marginal_gain": len(new_hits)})
        supp_gain.append({"verdict": ("边际收益>0，建议继续一轮" if any(s["marginal_gain"] > 0 for s in supp_gain[:-1])
                                      else "边际收益=0，停止补检；残余遗漏按 miss_reason 解释")})

    out = {"reference_version": ref.get("version"), "frozen_at": ref.get("frozen_at"),
           "reference_total": len(ref.get("items", [])),
           "hit_count": len(hits), "coverage_rate": cov_rate,
           "hits": hits, "missed": missed,
           "missed_count": len(missed),
           "miss_reason_summary": {k: sum(1 for m in missed if m["miss_reason"] == k)
                                   for k in {m["miss_reason"] for m in missed}},
           "supplementary": supp_gain if supp_gain else None,
           "audit_note": "分母=冻结参考集条目数（非检索结果自身）；每条漏检含原因码与归因；判定方法逐条记录",
           "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    SL.write_json(os.path.join(args.workdir, "coverage.json"), out)
    print("coverage=%.3f hits=%d missed=%d" % (cov_rate, len(hits), len(missed)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
