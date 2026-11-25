#!/usr/bin/env python3
"""LaTeX 工程静态审计：环境配对、\\ref↔\\label 闭合、\\cite↔bib 闭合、重复 label、主文件结构。
用法: python3 latex_audit.py main.tex [refs.bib ...]  （发现问题退出码 1）"""
import json, re, sys

BEGIN = re.compile(r"\\begin\{(\w+\*?)\}")
END = re.compile(r"\\end\{(\w+\*?)\}")
REF = re.compile(r"\\(?:auto)?[er]?ref\{([^}]+)\}")
LABEL = re.compile(r"\\label\{([^}]+)\}")
CITE = re.compile(r"\\cite[pt]?\{([^}]+)\}")
BIBITEM = re.compile(r"\\bibitem\{([^}]+)\}")
INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")

def strip_comments(s):
    out = []
    for line in s.splitlines():
        i = line.find("%")
        out.append(line if i < 0 else line[:i])
    return "\n".join(out)

def keys_in(m):
    ks = []
    for g in m:
        ks.extend(k.strip() for k in g.split(","))
    return ks

def read_tex(path):
    text = strip_comments(open(path, encoding="utf-8", errors="replace").read())
    for m in INPUT.finditer(text):
        sub = m.group(1)
        for ext in ("", ".tex"):
            try:
                text = text.replace(m.group(0), strip_comments(
                    open(sub + ext, encoding="utf-8", errors="replace").read()))
                break
            except OSError:
                pass
    return text

def main():
    tex_path = sys.argv[1]
    text = read_tex(tex_path)
    audit = {"unmatched_env": [], "dangling_refs": [], "orphan_labels": [],
             "dangling_cites": [], "orphan_bib": [], "duplicate_labels": [],
             "structure_issues": []}
    # 1) 环境配对
    stack = []
    pos = {"begin": [(m.start(), m.group(1)) for m in BEGIN.finditer(text)],
           "end": [(m.start(), m.group(1)) for m in END.finditer(text)]}
    events = [(p, "b", e) for p, e in pos["begin"]] + [(p, "e", e) for p, e in pos["end"]]
    events.sort()
    line_of = lambda p: text.count("\n", 0, p) + 1
    for _, kind, env in events:
        if kind == "b":
            stack.append((env, line_of(_)))
        else:
            if not stack or stack[-1][0] != env:
                audit["unmatched_env"].append(f"end-only: {env} @ L{line_of(_)}")
                if stack and env in [e for e, _ in stack]:
                    while stack and stack[-1][0] != env:
                        audit["unmatched_env"].append(f"begin-only: {stack[-1][0]} @ L{stack[-1][1]}")
                        stack.pop()
                    stack.pop()
            else:
                stack.pop()
    for env, ln in stack:
        audit["unmatched_env"].append(f"begin-only: {env} @ L{ln}")
    # 2) ref/label 闭合
    labels = keys_in(LABEL.findall(text))
    refs = keys_in(REF.findall(text))
    from collections import Counter
    for k, c in Counter(labels).items():
        if c > 1:
            audit["duplicate_labels"].append(k)
    lset = set(labels)
    audit["dangling_refs"] = [f"{k} @ {r}" for r, k in
                              [(f"L{line_of(m.start())}", m.group(1).strip()) for m in REF.finditer(text)]
                              if k not in lset]
    audit["orphan_labels"] = sorted(lset - set(refs))
    # 3) cite/bib 闭合
    cites = keys_in(CITE.findall(text))
    bibkeys = set()
    for p in sys.argv[2:]:
        bib = open(p, encoding="utf-8", errors="replace").read()
        bibkeys |= {m.group(1).strip() for m in re.finditer(r"@\w+\{([^,\s]+)\s*,", bib)}
        bibkeys |= set(BIBITEM.findall(bib))
    bibkeys |= set(BIBITEM.findall(text))
    audit["dangling_cites"] = sorted({k for k in cites if k not in bibkeys})
    audit["orphan_bib"] = sorted(bibkeys - set(cites))
    # 4) 主文件结构
    if not re.search(r"\\documentclass\{", text):
        audit["structure_issues"].append("缺 \\documentclass")
    if not re.search(r"\\begin\{document\}", text):
        audit["structure_issues"].append("缺 \\begin{document}")
    if not re.search(r"\\end\{document\}", text):
        audit["structure_issues"].append("缺 \\end{document}")
    problems = [v for v in audit.values() if v]
    print(json.dumps({"ok": not problems, "audit": audit}, ensure_ascii=False, indent=2))
    sys.exit(0 if not problems else 1)

if __name__ == "__main__":
    main()
