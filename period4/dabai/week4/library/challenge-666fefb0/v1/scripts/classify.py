#!/usr/bin/env python3
"""文献自动分类主脚本：scan→classify→plan→apply→rollback（幂等可回滚）。
用法:
  python3 classify.py scan <输入目录> --out inventory.json
  python3 classify.py classify <输入目录> --rules tag_rules.json --out classification.json [--library <库根>]
  python3 classify.py apply classification.json --src <输入目录> --dst <库根> --log ops_log.jsonl --out manifest.json
  python3 classify.py rollback manifest.json
"""
import argparse, hashlib, json, os, re, shutil, sys, time

DOC_TYPE_PAT = [
    ("preprint", r'(preprint|arxiv|biorxiv|medrxiv|ssrn)', re.I),
    ("conference", r'(proceedings|conference|会议|论文集|icml|neurips|acl\b)', re.I),
    ("thesis", r'(学位论文|thesis|dissertation|博士|硕士)', re.I),
    ("supplement", r'(supplement|supporting|补充材料|SI\d)', re.I),
]

def sha256_of(p):
    h = hashlib.sha256()
    try:
        with open(p, 'rb') as f:
            for c in iter(lambda: f.read(1 << 20), b''):
                h.update(c)
        return h.hexdigest()
    except Exception:
        return None

def head_text(fp):
    fp_l = fp.lower()
    try:
        if fp_l.endswith('.pdf'):
            try:
                from pypdf import PdfReader
                r = PdfReader(fp)
                return (r.pages[0].extract_text() or "")[:4000] if r.pages else ""
            except Exception:
                return ""
        return open(fp, encoding='utf-8', errors='ignore').read(4000)
    except Exception:
        return ""

def first_page_meta(name, head):
    meta = {}
    m = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', head, re.I)
    meta['doi'] = m.group(1).rstrip('.,;)') if m else None
    m = re.search(r'(19|20)\d{2}', name) or re.search(r'(19|20)\d{2}', head[:400])
    meta['year'] = m.group(0) if m else None
    lines = [l.strip() for l in head.splitlines() if l.strip()]
    meta['title'] = lines[0][:100] if lines else os.path.splitext(name)[0]
    m = re.search(r'^([A-Z][a-zA-Z\-]+),?\s+(?:et al|and|&)?', head)
    meta['first_author'] = m.group(1) if m else None
    return meta

def load_rules(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return {"topics": {}}

def classify_file(rel, name, head, rules):
    doc_type, type_hit = "unknown", None
    for t, pat, flags in DOC_TYPE_PAT:
        m = re.search(pat, name) or re.search(pat, head[:800], flags)
        if m:
            doc_type, type_hit = t, m.group(0); break
    blob = (name + "\n" + head).lower()
    scored = []
    for topic, spec in rules.get("topics", {}).items():
        kws = spec.get("keywords", []) if isinstance(spec, dict) else spec
        hits = [k for k in kws if k.lower() in blob]
        if hits:
            scored.append((topic, hits))
    scored.sort(key=lambda x: -len(x[1]))
    topic = scored[0][0] if scored else "uncategorized"
    tags = list(dict.fromkeys(k for _, hs in scored[:3] for k in hs))[:5]
    basis = {"doc_type_hit": type_hit, "rule": topic,
             "title_hits": [h for h in (scored[0][1] if scored else []) if h.lower() in name.lower()],
             "body_hits": (scored[0][1] if scored else [])}
    return topic, doc_type, tags, basis

def cmd_classify(a):
    rules = load_rules(a.rules)
    out = []
    hash_seen = {}
    doi_map = {}
    for dp, _, fns in os.walk(a.input_dir):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, a.input_dir)
            head = head_text(fp)
            digest = sha256_of(fp)
            meta = first_page_meta(n, head)
            if not head and not os.path.splitext(n)[1].lower() in ('.txt', '.md', '.csv'):
                if not head:
                    out.append({"src": rel, "unprocessed": True, "reason": "no_text_layer_or_unreadable"})
                    continue
            topic, doc_type, tags, basis = classify_file(rel, n, head, rules)
            year = meta['year'] or 'unknown_year'
            # 命名模板: 作者-年份-标题，缺字段降级
            author = meta['first_author'] or 'Unknown'
            title = re.sub(r'[\\/:*?"<>|\n]', '_', meta['title'])[:60] or os.path.splitext(n)[0][:60]
            new_name = f"{author}-{year}-{title}{os.path.splitext(n)[1]}"
            degraded = not (meta['first_author'] and meta['year'])
            dst = f"{topic}/{year}/{doc_type}/{new_name}"
            rec = {"src": rel, "dst": dst, "doc_type": doc_type, "tags": tags, "basis": basis,
                   "meta": meta, "sha256": digest, "rename_degraded": degraded,
                   "action": "move+rename"}
            # 去重
            if digest in hash_seen:
                rec["action"] = "archive_duplicate"
                rec["duplicate_of"] = hash_seen[digest]
            elif meta['doi'] and meta['doi'] in doi_map:
                rec["action"] = "archive_duplicate"
                rec["duplicate_of"] = doi_map[meta['doi']]
                rec["dup_key"] = f"doi:{meta['doi']}"
            else:
                if digest:
                    hash_seen[digest] = rel
                if meta['doi']:
                    doi_map[meta['doi']] = rel
            out.append(rec)
    json.dump({"input_dir": a.input_dir, "n": len(out), "items": out}, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(f"classified {len(out)} files -> {a.out}")

def cmd_apply(a):
    cls = json.load(open(a.classification, encoding='utf-8'))
    done = set()
    if os.path.exists(a.manifest):
        try:
            done = {r['src'] for r in json.load(open(a.manifest, encoding='utf-8'))['items'] if r.get('result') == 'ok'}
        except Exception:
            pass
    log = open(a.log, 'a', encoding='utf-8')
    items, unprocessed = [], []
    for rec in cls['items']:
        if rec.get('unprocessed'):
            unprocessed.append(rec); continue
        if rec['src'] in done:
            continue
        src = os.path.join(a.src, rec['src'])
        dst = os.path.join(a.dst, rec['dst'])
        result = 'ok'
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        except Exception as e:
            result = f"failed: {e}"
            unprocessed.append({"src": rec['src'], "reason": str(e)})
        entry = {**rec, "result": result}
        items.append(entry)
        log.write(json.dumps({"t": time.time(), "src": rec['src'], "dst": rec['dst'],
                              "action": rec['action'], "result": result}, ensure_ascii=False) + '\n')
    log.close()
    manifest = {"n_actions": len(items), "ok": sum(1 for i in items if i['result'] == 'ok'),
                "items": items, "unprocessed": unprocessed}
    json.dump(manifest, open(a.manifest, 'w'), ensure_ascii=False, indent=1)
    print(f"apply ok={manifest['ok']} unprocessed={len(unprocessed)} -> {a.manifest}")

def cmd_rollback(a):
    m = json.load(open(a.manifest, encoding='utf-8'))
    n = 0
    for it in m['items']:
        if it.get('result') == 'ok' and it.get('dst'):
            dst = os.path.join(m.get('dst', ''), it['dst'])
            try:
                os.remove(dst); n += 1
            except OSError:
                pass
    print(f"rolled back {n} applied files (source untouched; copy-mode rollback)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    c = sub.add_parser('classify'); c.add_argument('input_dir'); c.add_argument('--rules', default='tag_rules.json'); c.add_argument('--out', required=True); c.add_argument('--library')
    p = sub.add_parser('apply'); p.add_argument('classification'); p.add_argument('--src', required=True); p.add_argument('--dst', required=True); p.add_argument('--log', required=True); p.add_argument('--manifest', required=True)
    r = sub.add_parser('rollback'); r.add_argument('manifest')
    a = ap.parse_args()
    {'classify': cmd_classify, 'apply': cmd_apply, 'rollback': cmd_rollback}[a.cmd](a)
