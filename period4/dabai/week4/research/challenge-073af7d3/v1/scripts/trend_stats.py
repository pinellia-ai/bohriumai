#!/usr/bin/env python3
"""趋势统计流水线：normalize → yearly → topics（全部脚本化，可复算）。
用法:
  python3 trend_stats.py normalize <文献目录或题录.json> --out corpus.json
  python3 trend_stats.py yearly corpus.json --out yearly_stats.csv [--topic-lexicon topic_lexicon.json]
  python3 trend_stats.py topics corpus.json --lexicon topic_lexicon.json --out topic_evolution.json
"""
import argparse, csv, glob, hashlib, json, os, re, sys
from collections import defaultdict

YEAR_RE = re.compile(r'(19|20)\d{2}')
DOI_RE = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.I)

def norm_title(t):
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]', '', (t or '').lower())

def load_bib_entries(src):
    """支持题录 json(list) / 目录内 txt/md/csv/pdf 文件名+首行"""
    entries = []
    if os.path.isfile(src) and src.endswith('.json'):
        raw = json.load(open(src, encoding='utf-8'))
        for i, it in enumerate(raw if isinstance(raw, list) else raw.get('records', [])):
            entries.append({"title": it.get('title', ''), "year": it.get('year'), "doi": it.get('doi'),
                            "authors": it.get('authors', []), "venue": it.get('venue', ''),
                            "keywords": it.get('keywords', []), "cited_by": it.get('cited_by'),
                            "source_file": it.get('source_file', f'record{i}'), "locator": it.get('locator', '')})
        return entries
    for dp, _, fns in os.walk(src):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, src)
            head = ''
            try:
                head = open(fp, encoding='utf-8', errors='ignore').read(2000)
            except Exception:
                pass
            m = YEAR_RE.search(n) or YEAR_RE.search(head[:200])
            dm = DOI_RE.search(head)
            lines = [l.strip() for l in head.splitlines() if l.strip()]
            entries.append({"title": lines[0][:120] if lines else os.path.splitext(n)[0],
                            "year": m.group(0) if m else None, "doi": dm.group(0) if dm else None,
                            "authors": [], "venue": "", "keywords": [], "cited_by": None,
                            "source_file": rel, "locator": f"{rel}#L1"})
    return entries

def cmd_normalize(a):
    raw = load_bib_entries(a.src)
    seen_doi, seen_title, out = {}, {}, []
    n_dup = 0
    for i, e in enumerate(raw):
        y = e.get('year')
        if not y:
            m = YEAR_RE.search(e['title'])
            y = m.group(0) if m else None
        key_d = e.get('doi')
        key_t = norm_title(e['title'])[:80]
        status = 'unique'
        if key_d and key_d in seen_doi:
            status = 'dup_doi'
        elif key_t and key_t in seen_title:
            status = 'dup_title_author_year'
        if status != 'unique':
            n_dup += 1
            out.append({"rec_id": f"R{i:04d}", **e, "year_norm": y, "dedup_status": status,
                        "dup_of": seen_doi.get(key_d) or seen_title.get(key_t)})
            continue
        if key_d:
            seen_doi[key_d] = f"R{i:04d}"
        if key_t:
            seen_title[key_t] = f"R{i:04d}"
        out.append({"rec_id": f"R{i:04d}", **e, "year_norm": y, "dedup_status": "unique"})
    years = [int(o['year_norm']) for o in out if o['year_norm'] and o['dedup_status'] == 'unique']
    corpus = {"src": a.src, "n_total": len(raw), "n_dup": n_dup,
              "n_after_dedup": len([o for o in out if o['dedup_status'] == 'unique']),
              "year_missing_rate": round(1 - len(years) / max(len(out), 1), 3),
              "year_range": [min(years), max(years)] if years else None,
              "provenance": "year_norm=元数据优先，缺失从文件名/标题补录",
              "records": out}
    json.dump(corpus, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"corpus: {corpus['n_total']} total, {corpus['n_dup']} dup, missing_year={corpus['year_missing_rate']} -> {a.out}")

def load_lexicon(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return {"topics": {}}

def topic_of(rec, lexicon):
    blob = ' '.join([rec.get('title', ''), ' '.join(rec.get('keywords', []))]).lower()
    hits = []
    for t, kws in lexicon.get('topics', {}).items():
        for kw in kws if isinstance(kws, list) else kws.get('keywords', []):
            if kw.lower() in blob:
                hits.append(t)
                break
    return hits

def cmd_yearly(a):
    corpus = json.load(open(a.corpus, encoding='utf-8'))
    lex = load_lexicon(a.topic_lexicon)
    rows = []
    by_year = defaultdict(list)
    for r in corpus['records']:
        if r['dedup_status'] == 'unique' and r.get('year_norm'):
            by_year[int(r['year_norm'])].append(r)
    years = sorted(by_year)
    prev = None
    for y in years:
        recs = by_year[y]
        counts = defaultdict(int)
        for r in recs:
            for t in topic_of(r, lex) or ['(unclassified)']:
                counts[t] += 1
        total = len(recs)
        yoy = (total - prev) / prev if prev else None
        rows.append({"year": y, "count": total, "yoy": round(yoy, 3) if yoy is not None else None,
                     "topic_share": {t: round(c / total, 2) for t, c in sorted(counts.items())}})
        prev = total
    with open(a.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'count', 'yoy', 'topic_share'])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    # 拐点判据：|yoy|>=0.5 且随后一年同向
    infl = []
    for i, r in enumerate(rows[:-1]):
        yoy = r.get('yoy')
        if yoy is not None and abs(yoy) >= 0.5:
            nxt = rows[i + 1].get('yoy')
            sustained = nxt is not None and (nxt > 0) == (yoy > 0)
            infl.append({"year": r['year'], "yoy": yoy, "sustained": sustained,
                          "note": "候选拐点" if sustained else "单年波动，非拐点"})
    n = len(years)
    cagr = {"window": [years[0], years[-1]] if n >= 2 else None,
            "value": round((rows[-1]['count'] / rows[0]['count']) ** (1 / max(n - 1, 1)) - 1, 3) if n >= 4 and rows[0]['count'] else None,
            "insufficient": n < 4}
    json.dump({"yearly": rows, "inflections": infl, "cagr": cagr}, open(a.out.replace('.csv', '_summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"yearly {len(rows)} rows, {len(infl)} inflection candidates -> {a.out}")

def cmd_topics(a):
    corpus = json.load(open(a.corpus, encoding='utf-8'))
    lex = load_lexicon(a.lexicon)
    by_year = defaultdict(list)
    for r in corpus['records']:
        if r['dedup_status'] == 'unique' and r.get('year_norm'):
            by_year[int(r['year_norm'])].append(r)
    years = sorted(by_year)
    share = {}
    for y in years:
        c = defaultdict(int)
        for r in by_year[y]:
            for t in topic_of(r, lex) or ['(unclassified)']:
                c[t] += 1
        tot = sum(c.values()) or 1
        share[y] = {t: v / tot for t, v in c.items()}
    events = []
    all_topics = sorted({t for y in share for t in share[y] if t != '(unclassified)'})
    for t in all_topics:
        series = [(y, share[y].get(t, 0)) for y in years]
        first_y = next((y for y, v in series if v >= 0.05), None)
        if first_y:
            evs = [r for y in years if y == first_y for r in by_year[y] if t in topic_of(r, lex)]
            refs = [f"{r['title'][:40]}@{r['locator']}" for r in evs[:2]]
            events.append({"event": "emergence", "topic": t, "year": first_y,
                            "evidence": {"stat_row": f"year={first_y},share>=5%", "exemplar_refs": refs}})
        # 衰退：连续3年下降且低于峰值1/3
        peak = max(v for _, v in series) if series else 0
        for i in range(len(series) - 3):
            y0, y1, y2, y3 = series[i][1], series[i + 1][1], series[i + 2][1], series[i + 3][1]
            if y0 > y1 > y2 > y3 and y3 < peak / 3:
                events.append({"event": "decline", "topic": t, "year": series[i + 3][0],
                                "evidence": {"stat_row": f"连续下降 {series[i][0]}-{series[i+3][0]},峰值{round(peak,2)}", "exemplar_refs": []}})
                break
    json.dump({"years": years, "share_matrix": {str(y): share[y] for y in years}, "events": events,
                "lexicon": a.lexicon}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"topics: {len(all_topics)} topics, {len(events)} events -> {a.out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    n = sub.add_parser('normalize'); n.add_argument('src'); n.add_argument('--out', required=True)
    y = sub.add_parser('yearly'); y.add_argument('corpus'); y.add_argument('--out', required=True); y.add_argument('--topic-lexicon')
    t = sub.add_parser('topics'); t.add_argument('corpus'); t.add_argument('--lexicon', required=True); t.add_argument('--out', required=True)
    a = ap.parse_args()
    {'normalize': cmd_normalize, 'yearly': cmd_yearly, 'topics': cmd_topics}[a.cmd](a)
