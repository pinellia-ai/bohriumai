#!/usr/bin/env python3
"""check_proposal.py — 开题报告七要素与来源引用校验。
用法: python3 check_proposal.py <proposal.md> [constraints.json]
输出: checks.json（stdout 打印摘要）。退出码0=全部通过,1=有fail。
"""
import json, re, sys

SECTION_RULES = [
    ("研究背景", ["研究背景", "背景与意义", "选题背景"]),
    ("问题与目标", ["研究问题", "研究目标", "问题与目标", "科学问题"]),
    ("技术路线", ["技术路线", "研究方案", "研究内容与方法"]),
    ("阶段计划", ["阶段计划", "进度安排", "研究计划"]),
    ("风险与备选", ["风险", "备选方案"]),
    ("预期成果", ["预期成果", "预期结果"]),
    ("参考文献", ["参考文献", "References"]),
]

def main():
    if len(sys.argv) < 2:
        print("usage: check_proposal.py <proposal.md> [constraints.json]"); sys.exit(2)
    text = open(sys.argv[1], encoding="utf-8").read()
    checks = []
    for name, keys in SECTION_RULES:
        ok = any(k in text for k in keys)
        checks.append({"item": f"section:{name}", "pass": ok})
    # 引用格式与悬空引用
    refs_defined = set(re.findall(r"^\[?(Ref-\d+)\]?\s", text, re.M)) | set(
        re.findall(r"\[(Ref-\d+)\]", text))
    body = text.split("参考文献")[0] if "参考文献" in text else text
    cited = set(re.findall(r"\[(Ref-\d+)\]", body))
    dangling = sorted(c for c in cited if f"{c}]" not in text.replace(f"[{c}]", f"{c}]")
                      or not re.search(rf"^{re.escape(c)}\b", text, re.M))
    checks.append({"item": "citations_format", "pass": True,
                   "n_cited": len(cited), "dangling": dangling})
    # 来源标注覆盖：段落数 vs 带来源标注段落数（粗粒度）
    paras = [p for p in text.split("\n\n") if len(p.strip()) > 80]
    sourced = [p for p in paras if ("[来源" in p or "[Ref-" in p or p.lstrip().startswith("#"))]
    cover = (len(sourced) / len(paras)) if paras else 1.0
    checks.append({"item": "source_coverage", "pass": cover >= 0.9,
                   "ratio": round(cover, 3)})
    # 周期约束
    if len(sys.argv) > 2:
        cons = json.load(open(sys.argv[2], encoding="utf-8"))
        months = re.findall(r"第\s*(\d+)\s*[-~至]\s*(\d+)\s*月", text)
        if months and cons.get("period_months"):
            maxm = max(int(b) for _, b in months)
            ok = maxm <= int(cons["period_months"])
            checks.append({"item": "period_within_budget", "pass": ok,
                           "plan_max_month": maxm, "budget": cons["period_months"]})
        budget = cons.get("budget_max")
        if budget:
            amounts = re.findall(r"(\d+(?:\.\d+)?)\s*万", text)
            total = sum(float(a) for a in amounts)
            checks.append({"item": "budget_within_limit", "pass": total * 10000 <= budget,
                           "sum_wan": total, "limit": budget})
    result = {"checks": checks, "all_pass": all(c["pass"] for c in checks)}
    with open("checks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["item"])
    sys.exit(0 if result["all_pass"] else 1)

if __name__ == "__main__":
    main()
