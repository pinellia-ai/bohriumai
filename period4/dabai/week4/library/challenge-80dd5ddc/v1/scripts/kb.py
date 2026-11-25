#!/usr/bin/env python3
"""知识库索引+带引用问答检索：kb_build → kb_answer（证据绑定、版本归并、缺证判定）。
用法:
  python3 kb_build.py <库根目录> --out kb_index.json
  python3 kb_answer.py --index kb_index.json --query "问题" --out answer.json [--case-id ID] [--top 8]
多问题示例：--query-file questions.txt（每行一问）
"""
import argparse, hashlib, json, os, re, sys, time

CHUNK_MAX = 1200
LOW_SCORE_THRESHOLD = 4  # 低于此分视为证据不足

def sha256_of(p):
    try:
        return hashlib.sha256(open(p, 'rb').read()).hexdigest()
    except Exception:
        return None

def extract(fp):
    ext = os.path.splitext(fp)[1].lower()
    try:
        if ext == '.pdf':
            from pypdf import PdfReader
            r = PdfReader(fp)
            return [(i + 1, p.extract_text() or "") for i, p in enumerate(r.pages)]
        return [(None, open(fp, encoding='utf-8', errors='ignore').read())]
    except Exception:
        return None

def tokenize(text):
    toks = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_\-]{1,}', text):
        toks.add(m.group(0).lower())
    for m in re.finditer(r'[\u4e00-\u9fff]{2,}', text):
        s = m.group(0); toks.add(s)
        for i in range(len(s) - 1):
            toks.add(s[i:i + 2])
    return toks

def cmd_build(a):
    chunks, docs, gaps, dupes = [], [], [], {}
    hash_map, base_map = {}, {}
    did = 0
    for dp, _, fns in os.walk(a.root):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, a.root)
            digest = sha256_of(fp)
            base = re.sub(r'(v\d+|final|\(\d+\)|修订)', '', os.path.splitext(rel)[0], flags=re.I).rstrip(' _-')
            if digest:
                if digest in hash_map:
                    dupes.setdefault(hash_map[digest], []).append(rel)
                    continue  # 副本不入索引
                hash_map[digest] = rel
            base_map.setdefault(base, []).append({"rel": rel, "digest": digest, "mtime": os.path.getmtime(fp)})
            pages = extract(fp)
            if pages is None:
                gaps.append({"path": rel, "reason": "unreadable_or_no_text_layer"})
                continue
            docs.append({"doc_id": did, "path": rel, "sha256": digest})
            for page, text in pages:
                buf, pi = "", 0
                for para in re.split(r'\n\s*\n', text):
                    t = para.strip()
                    if not t:
                        continue
                    if len(buf) + len(t) > CHUNK_MAX and buf:
                        chunks.append(mk(did, rel, page, buf, pi, digest)); pi += 1; buf = t
                    else:
                        buf = (buf + "\n" + t).strip()
                if buf:
                    chunks.append(mk(did, rel, page, buf, pi, digest))
            did += 1
    # 版本链：同 base 多条；优先按文件名版本号排序，缺号按 mtime
    def vrank(item):
        m = re.search(r'v(\d+)', os.path.basename(item['rel']))
        return int(m.group(1)) if m else 0
    chains = {}
    for b, v in base_map.items():
        if len(v) > 1:
            chains[b] = sorted(v, key=lambda x: (vrank(x), x['mtime']))
    json.dump({"root": a.root, "docs": docs, "chunks": chunks, "coverage_gaps": gaps,
               "duplicate_groups": dupes, "version_chains": {b: [x['rel'] for x in v] for b, v in chains.items()}},
              open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f"kb: {len(docs)} docs, {len(chunks)} chunks, {len(gaps)} gaps, {len(dupes)} dup groups -> {a.out}")

def mk(did, rel, page, text, pi, digest):
    sents = re.split(r'(?<=[。.!?!?])\s*', text.strip())
    return {"chunk_id": f"{did}_{pi}", "doc_id": did, "path": rel, "page": page, "para_idx": pi,
            "first_sentence": sents[0][:100] if sents else text[:100], "text": text, "sha256_8": (digest or "")[:8]}

def cmd_answer(a):
    idx = json.load(open(a.index, encoding='utf-8'))
    qs = open(a.query_file, encoding='utf-8').read().splitlines() if a.query_file else [a.query]
    results, log = [], []
    for q in [x.strip() for x in qs if x.strip()]:
        qt = tokenize(q)
        hits = []
        for ch in idx['chunks']:
            toks = tokenize(ch['text'])
            score = len(qt & toks) * 2
            if score == 0:
                continue
            pos = min((ch['text'].lower().find(t) for t in qt if ch['text'].lower().find(t) >= 0), default=0)
            snippet = ch['text'][max(0, pos - 120):pos + 260].replace('\n', ' ')
            # 版本标注：chain 按版本号升序，chain[-1] 为最新
            vlabel, is_latest = "latest", 1
            for base, chain in idx.get('version_chains', {}).items():
                if ch['path'] in chain and ch['path'] != chain[-1]:
                    vlabel = f"v{chain.index(ch['path']) + 1}(旧版,最新为 {os.path.basename(chain[-1])})"
                    is_latest = 0
            hits.append({"score": score + is_latest, "path": ch['path'], "version_label": vlabel, "page": ch['page'],
                         "para_idx": ch['para_idx'], "first_sentence": ch['first_sentence'], "snippet": snippet,
                         "evid_id": f"E{len(hits) + 1}",
                         "locator": f"{ch['path']}#page={ch['page']},para={ch['para_idx']}"})
        hits.sort(key=lambda x: -x['score'])
        top = hits[:a.top]
        enough = top and top[0]['score'] >= LOW_SCORE_THRESHOLD
        results.append({
            "question": q,
            "retrieval": {"top_k": a.top, "hit_count": len(hits), "top_paths": [h['path'] for h in top[:5]]},
            "candidate_evidence": top,
            "sufficient_evidence": enough,
            "answer_note": "检索到候选证据，待绑定论断" if enough else "证据不足：应回答知识库中没有找到支持该问题的依据，并说明缺什么",
            "missing_evidence": {"triggered": not enough, "searched_terms": sorted(qt),
                                  "scope": f"{len(idx['docs'])} docs", "suggestion": "确认相关文件是否已入库/是否有扫描件未入索引" if not enough else None},
        })
        log.append({"q": q, "terms": sorted(qt), "hit_count": len(hits),
                    "top": [{"evid_id": h['evid_id'], "path": h['path'], "page": h['page'], "para": h['para_idx'], "score": h['score']} for h in top]})
    out = {"case_id": a.case_id, "status": "ok", "kb_overview": {"files": len(idx['docs']),
            "duplicate_groups": len(idx.get('duplicate_groups', {})), "version_chains": len(idx.get('version_chains', {})),
            "coverage_gaps": idx.get('coverage_gaps', [])},
           "answers": results,
           "operation_evidence": {"kb_index": a.index, "retrieval_log": a.log, "hash_algo": "sha256",
                                   "rerun_cmd": "kb_build.py → kb_answer.py"},
           "uncertainty": ["page 为物理页", "双栏 PDF 段序为抽取顺序"]}
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(log, open(a.log, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{len(results)} questions answered -> {a.out}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    b = ap.add_subparsers(dest='cmd', required=True)
    bb = b.add_parser('build'); bb.add_argument('root'); bb.add_argument('--out', required=True)
    ba = b.add_parser('answer'); ba.add_argument('--index', required=True); ba.add_argument('--query')
    ba.add_argument('--query-file'); ba.add_argument('--out', required=True); ba.add_argument('--log', required=True)
    ba.add_argument('--case-id', default=''); ba.add_argument('--top', type=int, default=8)
    a = ap.parse_args()
    {'build': cmd_build, 'answer': cmd_answer}[a.cmd](a)
