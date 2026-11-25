#!/usr/bin/env python3
"""纳排筛选脚本：按条款表对题录集逐条判定（题录级/全文级），留痕可复算。
用法:
  python3 screen.py screen criteria.json corpus.json --round title --out screening_log.jsonl [--fulltext-dir DIR]
  python3 screen.py prisma screening_log.jsonl --out prisma_counts.json
"""
import argparse, json, os, re, sys
from collections import Counter

def term_hit(rec, clause):
    terms = clause.get('terms', [])
    blob = ' '.join([rec.get('title', ''), ' '.join(rec.get('keywords', [])),
                     rec.get('abstract', '') or rec.get('head', '')]).lower()
    hits = [t for t in terms if t.lower() in blob]
    return hits

def judge(rec, criteria, round_name):
    # 排除性条款（如综述/语言限制）先行判定；其次按优先级查 include；均未命中→exclude(no_include)
    for ec in criteria['exclude']:
        hits = term_hit(rec, ec)
        if hits:
            return {"verdict": "exclude", "clause_id": ec['crit_id'], "reason_terms": hits}
    for ic in sorted([c for c in criteria['include']], key=lambda x: x.get('priority', 9)):
        hits = term_hit(rec, ic)
        if hits:
            return {"verdict": "include", "clause_id": ic['crit_id'], "reason_terms": hits}
    return {"verdict": "exclude", "clause_id": "no_include_criteria_met", "reason_terms": []}

def cmd_screen(a):
    criteria = json.load(open(a.criteria, encoding='utf-8'))
    corpus = json.load(open(a.corpus, encoding='utf-8'))
    recs = corpus.get('records', corpus) if isinstance(corpus, dict) else corpus
    log = open(a.out, 'w', encoding='utf-8')
    n = 0
    for r in recs:
        if r.get('dedup_status') and r['dedup_status'] != 'unique':
            continue  # 去重记录不参与筛选
        v = judge(r, criteria, a.round)
        rec = {"rec_id": r.get('rec_id'), "round": a.round, "judged_by": "script", **v}
        if a.round == 'fulltext':
            fp = os.path.join(a.fulltext_dir or '', os.path.basename(r.get('source_file', '')))
            if not os.path.exists(fp):
                rec['verdict'] = 'exclude'
                rec['clause_id'] = 'fulltext_unavailable'
                rec['reason_terms'] = []
        log.write(json.dumps(rec, ensure_ascii=False) + '\n')
        n += 1
    log.close()
    print(f"screened {n} records ({a.round}) -> {a.out}")

def cmd_prisma(a):
    recs = [json.loads(l) for l in open(a.log, encoding='utf-8') if l.strip()]
    title = [r for r in recs if r['round'] == 'title']
    full = [r for r in recs if r['round'] == 'fulltext']
    included_title = [r for r in title if r['verdict'] == 'include']
    included_full = [r for r in full if r['verdict'] == 'include']
    counts = {
        "identified": len(title),
        "duplicates_removed": sum(1 for r in recs if r.get('clause_id') == 'DUP'),
        "title_screened": len(title),
        "title_excluded": sum(1 for r in title if r['verdict'] == 'exclude'),
        "fulltext_assessed": len(full) or len(included_title),
        "fulltext_excluded": sum(1 for r in full if r['verdict'] == 'exclude'),
        "included": len(included_full) or len(included_title),
        "exclusion_reasons": dict(Counter(r['clause_id'] for r in title if r['verdict'] == 'exclude')),
    }
    json.dump(counts, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(counts, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('screen'); s.add_argument('criteria'); s.add_argument('corpus')
    s.add_argument('--round', choices=['title', 'fulltext'], required=True); s.add_argument('--out', required=True)
    s.add_argument('--fulltext-dir')
    p = sub.add_parser('prisma'); p.add_argument('log'); p.add_argument('--out', required=True)
    a = ap.parse_args()
    {'screen': cmd_screen, 'prisma': cmd_prisma}[a.cmd](a)
