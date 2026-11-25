#!/usr/bin/env python3
"""文内引用↔文末条目 双向对账脚本。
用法:
  python3 cite_audit.py manuscript.txt bib.json [--style numeric|author_year]
manuscript.txt: 稿件纯文本; bib.json: 条目数组 [{"key","title","authors","year","doi",...}]
输出: JSON 对账报告; 发现问题时退出码 1。仅用标准库。"""
import json, re, sys, unicodedata

def norm_title(t):
    t = unicodedata.normalize("NFKC", str(t)).lower()
    return re.sub(r"[^\w\s]", "", t).strip()

def extract_citations(text):
    """提取文内引用点: [n]/[n,m]/[n-m] 或 \cite{key}，带位置(段落序号+所在句)。"""
    points = []
    paras = [p for p in text.split("\n") if p.strip()]
    for pi, para in enumerate(paras, 1):
        sents = re.split(r"(?<=[.。!?！？])\s*", para)
        for si, sent in enumerate(sents, 1):
            for m in re.finditer(r"\\cite\{([^}]+)\}", sent):
                keys = [k.strip() for k in m.group(1).split(",")]
                points.append({"marker": m.group(0), "keys": keys,
                               "locus": f"P{pi}-S{si}", "claim": sent.strip()[:80]})
            for m in re.finditer(r"\[(\d+(?:\s*[,，\-–]\s*\d+)*)\]", sent):
                nums = set()
                for part in re.split(r"[,，]", m.group(1)):
                    if re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$", part):
                        a, b = map(int, re.match(r"^\s*(\d+)\s*[-–]\s*(\d+)\s*$", part).groups())
                        nums.update(range(a, b + 1))
                    elif part.strip().isdigit():
                        nums.add(int(part.strip()))
                if nums:
                    points.append({"marker": m.group(0), "keys": [str(n) for n in sorted(nums)],
                                   "locus": f"P{pi}-S{si}", "claim": sent.strip()[:80]})
    return points

def detect_duplicates(entries):
    by_doi, by_ty = {}, {}
    dups = []
    for e in entries:
        doi = str(e.get("doi") or "").strip().lower()
        if doi:
            if doi in by_doi:
                dups.append({"basis": "doi_same", "kept": by_doi[doi]["key"], "merged": e.get("key")})
            else:
                by_doi[doi] = e
        nt = norm_title(e.get("title", ""))
        ya = str(e.get("year", ""))
        if nt and (nt, ya) in by_ty:
            dups.append({"basis": "title+year", "kept": by_ty[(nt, ya)]["key"], "merged": e.get("key")})
        elif nt:
            by_ty[(nt, ya)] = e
    return dups

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    style = "author_year" if "--style author_year" in sys.argv else "numeric"
    text = open(args[0], encoding="utf-8").read()
    entries = json.load(open(args[1], encoding="utf-8"))
    points = extract_citations(text)
    ekeys = {str(e.get("key")) for e in entries}
    cited = set()
    dangling = []
    for p in points:
        for k in p["keys"]:
            if k in ekeys:
                cited.add(k)
            else:
                dangling.append({"marker": p["marker"], "key": k, "locus": p["locus"]})
    orphans = sorted(ekeys - cited)
    numbering_issues = []
    if style == "numeric":
        firsts, seen = [], set()
        for p in points:
            for k in p["keys"]:
                if k not in seen:
                    seen.add(k)
                    firsts.append(k)
        ordered_numeric = [k for k in firsts if k.isdigit()]
        if ordered_numeric != sorted(ordered_numeric):
            numbering_issues.append("正文数字编号首现顺序非递增")
    misplaced = [p["locus"] for p in points if len(p["claim"]) < 10]
    dups = detect_duplicates(entries)
    report = {
        "cited_points": len(points), "entries": len(entries),
        "dangling_citations": dangling, "orphan_entries": orphans,
        "numbering_issues": numbering_issues,
        "possible_duplicates": dups,
        "ok": not (dangling or orphans or numbering_issues),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["ok"] else 1)

if __name__ == "__main__":
    main()
