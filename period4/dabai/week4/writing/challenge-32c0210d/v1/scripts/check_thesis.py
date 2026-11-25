#!/usr/bin/env python3
"""check_thesis.py — 长文档跨章一致性校验。
用法: python3 check_thesis.py <chapters_dir_or_merged.md> [work_dir]
work_dir 含 glossary.json / chapter-tree.md（可选）。
退出码 0=全过, 1=有 fail。
"""
import json, os, re, sys, glob

def all_text(path):
    files = []
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "**", "*.md"), recursive=True))
        text = "\n\n".join(open(f, encoding="utf-8").read() for f in files)
    else:
        files = [path]
        text = open(path, encoding="utf-8").read()
    return text, files

def main():
    if len(sys.argv) < 2:
        print("usage: check_thesis.py <chapters_dir_or_merged.md> [work_dir]"); sys.exit(2)
    text, files = all_text(sys.argv[1])
    work = sys.argv[2] if len(sys.argv) > 2 else "."
    checks = []
    # 1) 标题层级不跳级
    levels, skips = [], []
    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+\S", line)
        if m:
            lv = len(m.group(1))
            if levels and lv > levels[-1] + 1:
                skips.append(line.strip()[:40])
            levels.append(lv)
    checks.append({"item": "heading_levels", "pass": not skips, "skips": skips})
    # 2) 图表/公式编号连续（Figure 1..N 无缺号）
    figs = sorted(set(int(n) for n in re.findall(r"Fig(?:ure)?[-\s](\d+)", text)))
    gaps = [i for i in range(1, (max(figs) + 1) if figs else 1) if i not in figs]
    checks.append({"item": "figure_numbering", "pass": not gaps, "gaps": gaps})
    # 3) 悬空引用：C-n / M-n / R-n / Fig-n 必须有定义处
    for tag, pat_def, pat_use in [
        ("C-n", r"\[(C-\d+)\]\s*[:：]", r"\[(C-\d+)\]"),
        ("M-n", r"\[(M-\d+)\]", r"\[(M-\d+)\]"),
        ("R-n", r"^\[(R-\d+)\]", r"\[(R-\d+)\]")]:
        defined = set(re.findall(pat_def, text, re.M))
        used = set(re.findall(pat_use, text))
        if tag == "M-n":  # 索引可能在 work 目录 material-index
            idx = os.path.join(work, "material-index.md")
            if os.path.exists(idx):
                defined |= set(re.findall(r"M-\d+", open(idx, encoding="utf-8").read()))
        dangling = sorted(u for u in used - defined)
        checks.append({"item": f"dangling_{tag}", "pass": not dangling, "dangling": dangling})
    # 4) 术语禁用变体
    glo = os.path.join(work, "glossary.json")
    if os.path.exists(glo):
        glossary = json.load(open(glo, encoding="utf-8"))
        bad = []
        for term in glossary if isinstance(glossary, list) else glossary.get("terms", []):
            for v in term.get("banned_variants", []):
                if re.search(rf"\b{re.escape(v)}\b", text) or v in text:
                    bad.append(v)
        checks.append({"item": "banned_term_variants", "pass": not bad, "found": bad})
    # 5) 字数预算：chapter-tree.md 中 "预算N字" 汇总 vs 实际
    tree = os.path.join(work, "chapter-tree.md")
    if os.path.exists(tree):
        budget = sum(int(n) for n in re.findall(r"预算[:：]?\s*(\d+)\s*字", open(tree, encoding="utf-8").read()))
        actual = len(re.sub(r"\s", "", re.sub(r"[#|`>\[\]()\-]|Fig(?:ure)?[-\s]\d+|\[(?:C|M|R)-\d+\]", "", text)))
        if budget:
            dev = abs(actual - budget) / budget
            checks.append({"item": "word_budget_total", "pass": dev <= 0.15,
                           "budget": budget, "actual": actual, "dev": round(dev, 3)})
    result = {"checks": checks, "all_pass": all(c["pass"] for c in checks)}
    out = "consistency-report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
