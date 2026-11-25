#!/usr/bin/env python3
"""证据表校验器 + 草稿全检：quote 可定位、[EVxx] 绑定率、强度一致性、主题覆盖。
用法:
  python3 draft_check.py quotes evidence_table.csv --corpus corpus.json --out /tmp/ev_check.json
  python3 draft_check.py draft draft.md --evidence evidence_table.csv --out /tmp/draft_check.json
"""
import argparse, csv, json, os, re, sys

def norm(s):
    return re.sub(r'\s+', '', s or '')

def load_text_map(corpus_path):
    """rec_id -> 可定位文本（首2000字符）；题录模式用 title/abstract/head。"""
    corpus = json.load(open(corpus_path, encoding='utf-8'))
    recs = corpus.get('records', corpus) if isinstance(corpus, dict) else corpus
    m = {}
    for r in recs:
        rid = r.get('rec_id')
        m[rid] = norm(' '.join([r.get('title', ''), r.get('abstract', '') or r.get('head', ''), r.get('fulltext', '') or '']))
    return m

def cmd_quotes(a):
    rows = list(csv.DictReader(open(a.evidence_table, encoding='utf-8')))
    tm = load_text_map(a.corpus)
    bad = []
    for r in rows:
        q = norm(r.get('quote', ''))
        rid = r.get('rec_id')
        if not q or not rid:
            bad.append((r.get('ev_id'), 'missing_fields')); continue
        hay = tm.get(rid, '')
        if q[:60] not in hay:
            bad.append((r.get('ev_id'), 'quote_unverified'))
    out = {"n_rows": len(rows), "unverified": bad, "verified": len(rows) - len(bad),
            "verdict": "pass" if not bad else "fail"}
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": out['verdict'], "verified": out['verified'], "bad": bad[:10]}, ensure_ascii=False))

def cmd_draft(a):
    draft = open(a.draft, encoding='utf-8').read()
    ev_ids = set()
    try:
        for r in csv.DictReader(open(a.evidence, encoding='utf-8')):
            ev_ids.add(r.get('ev_id'))
    except Exception:
        pass
    used = set(re.findall(r'\[(EV[0-9]+)\]', draft))
    dangling = used - ev_ids
    # 强度一致性：声称"已被证明"的句子需 ≥2 个 EV
    hard_violations = []
    for line in draft.splitlines():
        if '已被证明' in line:
            n_ev = len(re.findall(r'\[EV[0-9]+\]', line))
            if n_ev < 2:
                hard_violations.append(line.strip()[:60])
    # 实质论断句无引用（句号结尾且含数字/比较词的长句）
    unbound = []
    for sent in re.split(r'(?<=[。.!?])\s*', draft):
        s = sent.strip()
        if len(s) > 40 and ('高于' in s or '低于' in s or '显著' in s or re.search(r'\d', s)) and '[EV' not in s and not s.startswith('#'):
            unbound.append(s[:60])
    out = {"ev_used": sorted(used), "dangling_refs": sorted(dangling),
            "hard_violations": hard_violations, "unbound_claims": unbound[:10],
            "verdict": "pass" if not (dangling or hard_violations or unbound) else "fail"}
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({"verdict": out['verdict'], "dangling": out['dangling_refs'],
                       "hard": len(hard_violations), "unbound": len(unbound)}, ensure_ascii=False))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('quotes'); q.add_argument('evidence_table'); q.add_argument('--corpus', required=True); q.add_argument('--out', required=True)
    d = sub.add_parser('draft'); d.add_argument('draft'); d.add_argument('--evidence', required=True); d.add_argument('--out', required=True)
    a = ap.parse_args()
    {'quotes': cmd_quotes, 'draft': cmd_draft}[a.cmd](a)
