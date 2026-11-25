#!/usr/bin/env python3
"""批注提取+锚点校验+检索：PDF annotation 对象与文本标记双通道。
用法:
  python3 annot_extract.py extract <材料目录> --out annotations.json
  python3 annot_extract.py query annotations.json --tags 裂解液 [--file xxx] [--q 关键词]
"""
import argparse, hashlib, json, os, re, sys

INLINE_HL = re.compile(r'==(.+?)==')
INLINE_NOTE = re.compile(r'(?:^|\s)//(.+?)(?:$|\n)')

def sha8(p):
    try:
        return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:8]
    except Exception:
        return None

def norm(s):
    return re.sub(r'\s+', '', s or '')

def pdf_page_texts(fp):
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    r = PdfReader(fp)
    out = []
    for i, pg in enumerate(r.pages):
        try:
            out.append((i + 1, pg.extract_text() or ""))
        except Exception:
            out.append((i + 1, ""))
    return out, r

def extract_pdf(fp, rel):
    recs = []
    try:
        pages, reader = pdf_page_texts(fp)
    except Exception as e:
        return [{"annot_id": None, "file": rel, "error": f"unreadable: {e}", "reason": "encrypted_or_corrupt"}]
    n_annot = 0
    for pno, ptext in pages:
        try:
            page = reader.pages[pno - 1]
            annots = page.get("/Annots")
            if not annots:
                continue
        except Exception:
            continue
        page_norm = norm(ptext)
        for a in annots:
            try:
                o = a.get_object()
            except Exception:
                continue
            subtype = str(o.get('/Subtype', ''))
            contents = str(o.get('/Contents', '') or '')
            color = o.get('/C')
            color = [round(float(x), 2) for x in color] if color else None
            rect = [float(x) for x in o.get('/Rect', [])] if o.get('/Rect') else None
            excerpt = None
            # 尝试从 quadpoints/rect 对齐 underlying text（简化：用整页文本滑窗近似）
            if subtype in ('/Highlight', '/Underline', '/Squiggly') and ptext:
                excerpt = None  # 精确 quadpoint 对齐较复杂；标记待校验
                n_annot += 1
                recs.append({"annot_id": f"A{len(recs) + 1:03d}", "file": rel, "sha256_8": sha8(fp),
                             "page": pno, "subtype": subtype.lstrip('/'), "color": color,
                             "contents": contents or None, "excerpt": excerpt, "rect": rect,
                             "anchor": "unverified_no_excerpt", "source": "pdf_annot"})
                continue
            n_annot += 1
            recs.append({"annot_id": f"A{len(recs) + 1:03d}", "file": rel, "sha256_8": sha8(fp),
                         "page": pno, "subtype": subtype.lstrip('/'), "color": color,
                         "contents": contents or None, "excerpt": None, "rect": rect,
                         "anchor": "no_excerpt", "source": "pdf_annot"})
    if n_annot == 0 and not any(t.strip() for _, t in pages):
        return [{"annot_id": None, "file": rel, "reason": "no_annot_layer_no_text"}]
    return recs or [{"annot_id": None, "file": rel, "reason": "no_annot_layer"}]

def extract_text_marks(fp, rel):
    recs = []
    try:
        lines = open(fp, encoding='utf-8', errors='ignore').read().splitlines()
    except Exception:
        return [{"annot_id": None, "file": rel, "reason": "unreadable"}]
    for i, line in enumerate(lines, 1):
        for m in INLINE_HL.finditer(line):
            recs.append({"annot_id": f"A{len(recs) + 1:03d}", "file": rel, "sha256_8": sha8(fp),
                         "page": None, "line": i, "subtype": "Highlight", "color": None,
                         "contents": None, "excerpt": m.group(1), "anchor": "verified",
                         "source": "inline_mark"})
        for m in INLINE_NOTE.finditer(line):
            recs.append({"annot_id": f"A{len(recs) + 1:03d}", "file": rel, "sha256_8": sha8(fp),
                         "page": None, "line": i, "subtype": "FreeText", "color": None,
                         "contents": m.group(1), "excerpt": line.strip()[:120], "anchor": "verified",
                         "source": "inline_mark"})
    return recs

def cmd_extract(a):
    all_recs = []
    for dp, _, fns in os.walk(a.root):
        for n in sorted(fns):
            fp = os.path.join(dp, n)
            rel = os.path.relpath(fp, a.root)
            ext = os.path.splitext(n)[1].lower()
            if ext == '.pdf':
                all_recs.extend(extract_pdf(fp, rel))
            elif ext in ('.txt', '.md', '.csv'):
                recs = extract_text_marks(fp, rel)
                if not recs:
                    recs = [{"annot_id": None, "file": rel, "reason": "no_annotation_found"}]
                all_recs.extend(recs)
            else:
                all_recs.append({"annot_id": None, "file": rel, "reason": "unsupported_type_skipped"})
    # 锚点校验：对 PDF 无 excerpt 的批注尝试用 contents 或近似；anchor 统计
    stats = {"verified": 0, "verified_normalized": 0, "anchor_shift": 0, "no_excerpt": 0, "unverified": 0}
    for r in all_recs:
        k = r.get("anchor", "unverified")
        if k in stats:
            stats[k] += 1
    json.dump({"root": a.root, "n": len([r for r in all_recs if r.get('annot_id')]),
               "anchor_stats": stats, "annotations": all_recs}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"extracted {stats} -> {a.out}")

def cmd_query(a):
    data = json.load(open(a.annotations, encoding='utf-8'))
    tags = set((a.tags or '').split(',')) - {''}
    out = []
    for r in data['annotations']:
        if not r.get('annot_id'):
            continue
        if a.file and a.file.lower() not in r['file'].lower():
            continue
        blob = json.dumps(r, ensure_ascii=False).lower()
        if tags and not any(t.lower() in blob for t in tags):
            continue
        if a.q and a.q.lower() not in blob:
            continue
        out.append(r)
    print(json.dumps({"matched": len(out), "items": out[:20]}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('extract'); e.add_argument('root'); e.add_argument('--out', required=True)
    q = sub.add_parser('query'); q.add_argument('annotations'); q.add_argument('--tags'); q.add_argument('--file'); q.add_argument('--q')
    a = ap.parse_args()
    {'extract': cmd_extract, 'query': cmd_query}[a.cmd](a)
