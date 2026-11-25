#!/usr/bin/env python3
"""check_paper.py — 论文稿件事实一致性校验。
用法: python3 check_paper.py <draft.md> <references.md> <material-index.md>
退出码 0=全过, 1=有 fail。
"""
import json, re, sys

ABSTRACT_KEYS = ["摘要", "Abstract"]

def main():
    if len(sys.argv) < 4:
        print("usage: check_paper.py <draft.md> <references.md> <material-index.md>"); sys.exit(2)
    draft = open(sys.argv[1], encoding="utf-8").read()
    refs = open(sys.argv[2], encoding="utf-8").read()
    index = open(sys.argv[3], encoding="utf-8").read()
    checks = []
    # 1) 悬空材料引用
    m_defined = set(re.findall(r"^\|\s*(M-\d+)\s*\|", index, re.M)) | set(re.findall(r"\b(M-\d+)\b", index))
    m_cited = set(re.findall(r"\[(M-\d+)\]", draft))
    m_dangling = sorted(c for c in m_cited if c not in m_defined)
    checks.append({"item": "material_refs", "pass": not m_dangling, "dangling": m_dangling})
    # 2) 悬空文献引用
    r_defined = set(re.findall(r"^\[(R-\d+)\]", refs, re.M))
    r_cited = set(re.findall(r"\[(R-\d+)\]", draft))
    r_dangling = sorted(c for c in r_cited if c not in r_defined)
    r_unused = sorted(d for d in r_defined if d not in r_cited)
    checks.append({"item": "citation_refs", "pass": not r_dangling,
                   "dangling": r_dangling, "unused_in_refs": r_unused})
    # 3) 摘要数值应出现在结果段
    res = {}
    abs_m = re.search(r"(摘要|Abstract)(.*?)(?=\n#|\Z)", draft, re.S)
    body_m = re.search(r"(##?\s*(结果|Results))(.*?)(?=\n#|\Z)", draft, re.S)
    if abs_m and body_m:
        abs_nums = set(re.findall(r"\d+(?:\.\d+)?", abs_m.group(2)))
        body_nums = set(re.findall(r"\d+(?:\.\d+)?", body_m.group(3)))
        only_abs = sorted(n for n in abs_nums if n not in body_nums)
        checks.append({"item": "abstract_numbers_in_results", "pass": not only_abs,
                       "only_in_abstract": only_abs})
    else:
        checks.append({"item": "abstract_numbers_in_results", "pass": True, "note": "abstract/results section not both found"})
    # 4) 未标注来源的事实句（含数字但没有 [M-n]/[R-n] 标注）
    sentences = re.split(r"[。！？\n]", draft)
    fact_sents = [s for s in sentences if re.search(r"\d", s) and len(s.strip()) > 15
                  and not s.strip().startswith(("#", "|", "<", "-"))]
    unsourced = [s.strip()[:40] for s in fact_sents if "[M-" not in s and "[R-" not in s]
    ratio = (len(unsourced) / len(fact_sents)) if fact_sents else 0.0
    checks.append({"item": "unsourced_facts", "pass": ratio <= 0.2,
                   "ratio": round(ratio, 3), "examples": unsourced[:5]})
    result = {"checks": checks, "all_pass": all(c["pass"] for c in checks)}
    with open("consistency.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
