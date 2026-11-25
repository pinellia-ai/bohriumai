#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_locators.py — 把稿件文本切成带稳定定位器的段落单元。

用法: python3 make_locators.py <input_path...> --outdir /app/work
输入: /input/ 下的 txt/md/pdf/docx/html 材料（pdf 用 pdftotext，docx 解 XML，html 剥标签）
输出: <outdir>/paragraphs.csv (para_id,file,section_hint,page,first20,text)
      <outdir>/locators.json  ([{"file":..,"locator":"P001","section_hint":..}])
退出码: 0=至少解析出 1 段; 2=全部失败（调用方据此标 partial/failed）
"""
import argparse, csv, json, os, re, subprocess, sys

def read_txt(path):
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return open(path, encoding=enc).read(), {}
        except Exception:
            continue
    return "", {}

def read_pdf(path):
    try:
        out = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, timeout=120)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.decode("utf-8", "replace"), {"method": "pdftotext"}
    except Exception:
        pass
    try:
        from pypdf import PdfReader  # noqa
        r = PdfReader(path)
        pages = [(p.extract_text() or "") for p in r.pages]
        return "\n\n".join(pages), {"method": "pypdf", "pages": len(pages)}
    except Exception:
        return "", {"method": "failed"}

def read_docx(path):
    try:
        import zipfile, xml.etree.ElementTree as ET
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        paras = ["".join(t.text or "" for t in p.iter("{%s}t" % ns["w"]))
                 for p in root.iter("{%s}p" % ns["w"])]
        return "\n\n".join(paras), {"method": "docx-xml"}
    except Exception:
        return "", {"method": "failed"}

def read_html(path):
    raw, _ = read_txt(path)
    raw = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", "\n", raw), {"method": "html-strip"}

READERS = {".txt": read_txt, ".md": read_txt, ".pdf": read_pdf,
           ".docx": read_docx, ".html": read_html, ".htm": read_html}

SECTION_RE = re.compile(
    r"^\s*((abstract|introduction|methods?|materials|results?|discussion|conclusion|references|背景|摘要|关键词|引言|方法|材料|结果|讨论|结论|参考文献)\b.*)$",
    re.I)

def split_paras(text):
    paras, cur = [], []
    for line in text.splitlines():
        if line.strip():
            cur.append(line.strip())
        elif cur:
            paras.append("\n".join(cur)); cur = []
    if cur:
        paras.append("\n".join(cur))
    return [p for p in paras if len(p.strip()) >= 20]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--outdir", default="/app/work")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rows, locators = [], []
    pid = 0
    for path in a.inputs:
        ext = os.path.splitext(path)[1].lower()
        rd = READERS.get(ext)
        if rd is None:
            print(f"SKIP unsupported: {path}"); continue
        text, meta = rd(path)
        if not text.strip():
            print(f"FAIL no text: {path} meta={meta}"); continue
        print(f"OK {path} method={meta.get('method')} chars={len(text)}")
        section = "front"
        page = ""
        for para in split_paras(text):
            m = SECTION_RE.match(para)
            if m:
                section = m.group(1).strip()[:60]
            pid += 1
            locator = f"P{pid:03d}"
            rows.append({"para_id": locator, "file": os.path.basename(path),
                         "section_hint": section, "page": page,
                         "first20": para[:20], "text": para})
            locators.append({"file": os.path.basename(path), "locator": locator,
                             "section_hint": section})
    with open(os.path.join(a.outdir, "paragraphs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["para_id", "file", "section_hint", "page", "first20", "text"])
        w.writeheader(); w.writerows(rows)
    with open(os.path.join(a.outdir, "locators.json"), "w", encoding="utf-8") as f:
        json.dump(locators, f, ensure_ascii=False, indent=1)
    print(f"paragraphs={len(rows)} -> {a.outdir}")
    sys.exit(0 if rows else 2)

if __name__ == "__main__":
    main()
