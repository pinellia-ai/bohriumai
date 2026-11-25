#!/usr/bin/env python3
"""查询检索：同义扩展→打分→硬过滤→证据回链→result.json。
用法: python3 search.py --index index.json --query "缓冲液 配方" \
      [--filter k=v ...] [--top 10] --out /app/output/result.json [--case-id <id>]
"""
import argparse, json, os, re, sys, time

def tokenize(text):
    toks = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_\-]{1,}', text):
        toks.add(m.group(0).lower())
    for m in re.finditer(r'[\u4e00-\u9fff]{2,}', text):
        s = m.group(0)
        toks.add(s)
        for i in range(len(s) - 1):
            toks.add(s[i:i + 2])
    return toks

def expand_query(qt, syn):
    out = set(qt)
    for t in list(qt):
        for g in syn.values():
            if t in g:
                out.update(x.lower() for x in g)
    return out

def parse_filters(pairs):
    filters = {}
    for kv in pairs or []:
        k, v = kv.split('=', 1)
        filters[k] = v
    return filters

def year_of(path, chunk):
    m = re.search(r'(20\d{2}|19\d{2})', path) or re.search(r'(20\d{2}|19\d{2})', chunk.get("first_sentence", ""))
    return m.group(1) if m else None

def chunk_passes_filters(chunk, index, filters, report):
    ok = True
    path = chunk["path"]
    for k, v in filters.items():
        k = k.lower()
        if k in ("type", "file_type", "ext"):
            passed = path.lower().endswith('.' + v.lstrip('.').lower())
        elif k == "year":
            passed = year_of(path, chunk) == str(v)
        elif k in ("project", "project_id", "batch"):
            passed = v.lower() in path.lower() or v.lower() in chunk["text"].lower()
        elif k == "path_prefix":
            passed = path.startswith(v)
        else:
            passed = v.lower() in path.lower() or v.lower() in chunk["text"].lower()
        report.setdefault(k, 0)
        if passed:
            report[k] += 1
        else:
            ok = False
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", required=True)
    ap.add_argument("--query", required=True)
    ap.add_argument("--filter", action="append", help="k=v 可多次")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", required=True)
    ap.add_argument("--case-id", default="")
    a = ap.parse_args()

    idx = json.load(open(a.index, encoding="utf-8"))
    syn = idx.get("synonyms", {})
    qt = tokenize(a.query)
    qe = expand_query(qt, syn)
    filters = parse_filters(a.filter)

    scored = []
    filters_report = {}
    for ch in idx["chunks"]:
        toks = tokenize(ch["text"])
        direct = qt & toks
        expanded = qe - qt
        ext_hit = expanded & toks
        if not direct and not ext_hit:
            continue
        score = len(direct) * 2 + len(ext_hit)
        if all(t in ch["text"].lower() for t in a.query.lower().split() if len(t) > 1):
            score += 3  # 短语完整命中加成
        if not chunk_passes_filters(ch, idx, filters, filters_report):
            continue
        snippet = ch["text"]
        pos = min((snippet.lower().find(t) for t in qt if snippet.lower().find(t) >= 0), default=0)
        s0 = max(0, pos - 120); s1 = min(len(snippet), pos + 240)
        snippet = snippet[s0:s1].replace("\n", " ")
        scored.append({
            "rank": 0, "score": score, "path": ch["path"], "sha256_8": ch.get("sha256_8", ""),
            "page": ch.get("page"), "section_title": ch["section_title"], "para_idx": ch["para_idx"],
            "first_sentence": ch["first_sentence"], "snippet": snippet,
            "filter_passed": {k: True for k in filters},
            "locator": f'{ch["path"]}#page={ch.get("page")},para={ch["para_idx"]}',
            "direct_terms": sorted(direct), "expanded_terms": sorted(ext_hit),
        })
    scored.sort(key=lambda x: -x["score"])
    for i, h in enumerate(scored[:a.top], 1):
        h["rank"] = i
    result = {
        "case_id": a.case_id,
        "status": "ok" if scored else ("empty_result" if not filters else "empty_result"),
        "query": {"topic": a.query, "granularity": "paragraph",
                  "filters": {k: v for k, v in filters.items()},
                  "expanded_terms": sorted(qe - qt)},
        "inventory": {"total_docs": len(idx["docs"]), "chunks": idx["n_chunks"], "unreadable": len(idx["unreadable"])},
        "hits": scored[:a.top],
        "empty_result": {"triggered": not scored, "filters_report": filters_report,
                         "note": "过滤后为0：上表为逐条过滤后剩余块数；content_match=0 表示内容确实无命中" if not scored else ""},
        "operation_evidence": {"index_file": a.index, "hash_algo": "sha256",
                               "rerun_cmd": f"python3 scripts/build_index.py <root> --out {a.index} && python3 scripts/search.py --index {a.index} --query '{a.query}' --out {a.out}"},
        "skipped_or_failed": idx.get("unreadable", []),
        "uncertainty": ["段序为文本抽取顺序，双栏PDF可能非阅读序", "印刷页码未自动识别，page为物理页"],
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(result, open(a.out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(scored)} hits -> {a.out}")

if __name__ == "__main__":
    main()
