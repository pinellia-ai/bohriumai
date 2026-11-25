#!/usr/bin/env python3
"""建段落级索引：文本抽取(多格式)→切块(带页码/章节)→同义归一→倒排索引。
用法: python3 build_index.py <材料根目录> --out /app/work/index.json [--inventory inventory.json]
"""
import argparse, json, os, re, sys

SENT_SPLIT = re.compile(r'(?<=[。.!?!?；;])\s*')
CHUNK_MAX = 1200
EXTRACTABLE = {'.txt', '.md', '.csv', '.tsv', '.json', '.py', '.log'}

def load_synonyms(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return {}

def expand(tokens, syn):
    out = set(tokens)
    for t in tokens:
        for group in syn.values():
            if t in group:
                out.update(group)
    return out

def extract_text(fp, ext):
    """返回 [{page:int|None, text:str}]；不可抽取返回 None 并给原因。"""
    if ext in EXTRACTABLE:
        try:
            txt = open(fp, encoding='utf-8', errors='replace').read()
            return [{"page": None, "text": txt}]
        except Exception as e:
            return None
    if ext == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader
            except ImportError:
                return None
        try:
            r = PdfReader(fp)
            pages = []
            for i, p in enumerate(r.pages):
                try:
                    pages.append({"page": i + 1, "text": p.extract_text() or ""})
                except Exception:
                    pages.append({"page": i + 1, "text": ""})
            return pages if any(p["text"].strip() for p in pages) else None  # 无文本层→None
        except Exception:
            return None
    if ext == '.docx':
        try:
            import docx
            d = docx.Document(fp)
            return [{"page": None, "text": "\n".join(p.text for p in d.paragraphs)}]
        except Exception:
            return None
    if ext in ('.xlsx', '.xls'):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(fp, read_only=True, data_only=True)
            buf = []
            for ws in wb.worksheets:
                buf.append(f"[sheet:{ws.title}]")
                for row in ws.iter_rows(values_only=True):
                    buf.append("\t".join(str(c) for c in row if c is not None))
            return [{"page": None, "text": "\n".join(buf)}]
        except Exception:
            return None
    return None

def sections_of(text):
    """按 markdown/编号标题粗分章节标题。"""
    out, cur = [], "(preamble)"
    for line in text.splitlines():
        s = line.strip()
        if re.match(r'^#{1,6}\s+', s) or re.match(r'^\d+(\.\d+)*\s+\S', s):
            cur = re.sub(r'^#{1,6}\s+', '', s)[:80]
        out.append((cur, line))
    return out

def chunk_doc(doc_id, rel, pages, digest):
    chunks = []
    for pg in pages:
        paras = re.split(r'\n\s*\n|\n', pg["text"]) if pg["text"] else []
        buf, para_idx = "", 0
        for line in re.split(r'\n\s*\n', pg["text"]):
            t = line.strip()
            if not t:
                continue
            if len(buf) + len(t) > CHUNK_MAX and buf:
                chunks.append(make_chunk(doc_id, rel, pg["page"], buf, para_idx, digest))
                para_idx += 1
                buf = t
            else:
                buf = (buf + "\n" + t).strip()
        if buf:
            chunks.append(make_chunk(doc_id, rel, pg["page"], buf, para_idx, digest))
    return chunks

def make_chunk(doc_id, rel, page, text, para_idx, digest):
    sents = SENT_SPLIT.split(text)
    first = (sents[0][:100] if sents else text[:100])
    sec = "(unknown)"
    for line in text.splitlines():
        s = line.strip()
        if re.match(r'^#{1,6}\s+', s) or re.match(r'^\d+(\.\d+)*\s+\S', s):
            sec = re.sub(r'^#{1,6}\s+', '', s)[:80]; break
    return {"doc_id": doc_id, "path": rel, "page": page, "para_idx": para_idx,
            "section_title": sec, "first_sentence": first, "text": text,
            "sha256_8": (digest or "")[:8]}

def tokenize(text):
    # 中英混合：英文按词，中文按 2-gram + 单句长词
    toks = set()
    for m in re.finditer(r'[A-Za-z][A-Za-z0-9_\-]{1,}', text):
        toks.add(m.group(0).lower())
    for m in re.finditer(r'[\u4e00-\u9fff]{2,}', text):
        s = m.group(0)
        toks.add(s)
        for i in range(len(s) - 1):
            toks.add(s[i:i + 2])
    return toks

def build(root, out_path, syn_path):
    syn = load_synonyms(syn_path)
    docs, chunks, unreadable = [], [], []
    cid = 0
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            fp = os.path.join(dirpath, name)
            rel = os.path.relpath(fp, root)
            ext = os.path.splitext(name)[1].lower()
            digest = None
            try:
                import hashlib
                digest = hashlib.sha256(open(fp, 'rb').read()).hexdigest()
            except Exception:
                pass
            pages = extract_text(fp, ext)
            if pages is None:
                unreadable.append({"path": rel, "reason": "no_text_layer_or_unsupported" if ext in ('.pdf',) else "unsupported_or_unreadable"})
                continue
            docs.append({"doc_id": cid, "path": rel, "ext": ext, "sha256": digest})
            chunks.extend(chunk_doc(cid, rel, pages, digest))
            cid += 1
    # 倒排索引
    inv = {}
    for ch in chunks:
        for t in tokenize(ch["text"]):
            inv.setdefault(t, []).append(ch["doc_id"] * 1000 + hash_key(ch))
    index = {"root": root, "docs": docs, "chunks": chunks, "unreadable": unreadable,
             "inverted": {k: sorted(set(v)) for k, v in inv.items()},
             "synonyms": syn, "n_chunks": len(chunks)}
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(index, open(out_path, "w"), ensure_ascii=False)
    print(f"indexed {len(docs)} docs, {len(chunks)} chunks, {len(unreadable)} unreadable -> {out_path}")

def hash_key(ch):
    return abs(hash(ch["text"])) % 1000000  # 简化块内定位键

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("root"); ap.add_argument("--out", required=True)
    ap.add_argument("--synonyms", default=os.path.join(os.path.dirname(__file__), "synonyms.json"))
    a = ap.parse_args()
    build(a.root, a.out, a.synonyms)
