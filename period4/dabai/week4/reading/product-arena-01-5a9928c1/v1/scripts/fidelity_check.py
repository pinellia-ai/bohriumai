#!/usr/bin/env python3
"""翻译保真核验：数字保真 / 术语一致 / 引用标记计数。
用法: python3 scripts/fidelity_check.py --selftest
      python3 scripts/fidelity_check.py --segments segs.jsonl --translation trans.jsonl --glossary glossary.json"""
import argparse
import json
import re
import sys

NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*[x×]\s*10[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)?(?:\s*%|°C|K\b)?")
CITE_RE = re.compile(r"\[\d+\]|Figure\s*\d|Fig\.\s*\d|Table\s*\d")


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def check_numbers(segs, trans):
    tgt_all = " ".join(t.get("tgt_text", "") for t in trans)
    missing = []
    for s in segs:
        for n in NUM_RE.findall(s.get("src_text", "")):
            n_norm = n.replace(" ", "")
            if n_norm not in tgt_all.replace(" ", ""):
                missing.append((s["seg_id"], n))
    return missing


def check_terms(trans, glossary):
    problems = []
    for t in trans:
        for en, zh in glossary.items():
            if re.search(r"\b" + re.escape(en) + r"\b", t.get("src_text", "")):
                if zh not in t.get("tgt_text", "") and en not in t.get("tgt_text", ""):
                    problems.append((t["seg_id"], en, zh))
    return problems


def check_citations(segs, trans):
    src = len(CITE_RE.findall(" ".join(s.get("src_text", "") for s in segs)))
    tgt = len(CITE_RE.findall(" ".join(t.get("tgt_text", "") for t in trans)))
    return src, tgt, src == tgt


def selftest():
    segs = [{"seg_id": "P1", "src_text": "The catalyst achieves 92% conversion at 350 °C as shown in Figure 2."}]
    trans = [{"seg_id": "P1", "tgt_text": "该催化剂在 350 °C 下实现 92% 转化率，见图 Figure 2。"}]
    glossary = {"catalyst": "催化剂"}
    missing = check_numbers(segs, trans)
    assert missing == [], missing
    assert check_terms(trans, glossary) == []
    src, tgt, ok = check_citations(segs, trans)
    assert src == 1 and tgt == 1 and ok, (src, tgt)
    # negative case: dropped number must be caught
    bad_trans = [{"seg_id": "P1", "tgt_text": "该催化剂实现转化率，见图。"}]
    assert check_numbers(segs, bad_trans) != [], "dropped number not caught"
    print("selftest ok: numbers/citations pass; dropped number caught")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments")
    ap.add_argument("--translation")
    ap.add_argument("--glossary")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.segments and a.translation and a.glossary):
        print("usage: fidelity_check.py --selftest | --segments <f> --translation <f> --glossary <f>")
        return 2
    segs = load(a.segments)
    trans = load(a.translation)
    glossary = json.load(open(a.glossary, encoding="utf-8"))
    missing = check_numbers(segs, trans)
    terms = check_terms(trans, glossary)
    src, tgt, ok = check_citations(segs, trans)
    print(json.dumps({
        "numbers_missing": missing,
        "term_problems": terms,
        "citations": {"src": src, "tgt": tgt, "match": ok},
    }, ensure_ascii=False, indent=1))
    return 1 if (missing or terms or not ok) else 0


if __name__ == "__main__":
    sys.exit(main())
