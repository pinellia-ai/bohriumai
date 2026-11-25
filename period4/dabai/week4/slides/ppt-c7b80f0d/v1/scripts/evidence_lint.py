#!/usr/bin/env python3
"""evidence_lint.py — 校验 result.json 的证据映射与事实保真。

用法: python3 evidence_lint.py <result.json> [source.txt ...]
检查项:
  A. 结构: case_id 存在; status ∈ {ok, partial, failed}; slides 非空且每页有
     evidence.locator / locator_type(合法枚举) / quote; coverage 六要素齐备。
  B. 溯源: quote 非空且 <=200 字符。
  C. 数字保真: 页面 bullets/claim 中出现的数字(含单位)必须能在源文本中找到;
     找不到则记 mismatch(防"按印象取整/改写数据")。
  D. 状态一致性: status=ok 时 C 类 mismatch 必须为 0, 否则退出码 1。
退出码: 0 通过; 1 存在 FAIL 级问题; 2 输入缺失。
输出: 逐项 PASS/FAIL 的 JSON 报告(stdout)。
"""
import json
import os
import re
import sys

LOC_TYPES = {"figure", "table", "section", "equation", "data", "abstract", "appendix"}
SIX = ["mainline", "page_structure", "figure_refs", "narration", "template", "export"]
NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*[%±×·])?")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: evidence_lint.py result.json [source.txt ...]"}))
        sys.exit(2)
    res_path = sys.argv[1]
    if not os.path.isfile(res_path):
        print(json.dumps({"ok": False, "error": "result.json missing"}))
        sys.exit(2)
    res = json.load(open(res_path, encoding="utf-8"))
    src_text = ""
    for p in sys.argv[2:]:
        if os.path.isfile(p):
            src_text += open(p, encoding="utf-8", errors="ignore").read() + "\n"
    checks = []

    def chk(cid, ok, detail):
        checks.append({"id": cid, "verdict": "PASS" if ok else "FAIL", "detail": detail})
        return ok

    has_case = chk("case_id", bool(res.get("case_id")), "case_id=%r" % res.get("case_id"))
    status = res.get("status")
    chk("status_enum", status in {"ok", "partial", "failed"}, "status=%r" % status)
    slides = res.get("slides") or res.get("evidence_map") or []
    chk("slides_nonempty", isinstance(slides, list) and len(slides) > 0,
        "slides=%d" % (len(slides) if isinstance(slides, list) else -1))
    mismatches = []
    if isinstance(slides, list):
        for i, s in enumerate(slides):
            ev = s.get("evidence") or {}
            chk("ev_locator_s%d" % (s.get("idx", i + 1)), bool(ev.get("locator")),
                "locator missing" if not ev.get("locator") else ev["locator"])
            lt = ev.get("locator_type")
            chk("ev_loc_type_s%d" % (s.get("idx", i + 1)), lt in LOC_TYPES,
                "locator_type=%r" % lt)
            q = ev.get("quote") or ""
            chk("ev_quote_s%d" % (s.get("idx", i + 1)), 0 < len(q) <= 200,
                "quote len=%d" % len(q))
            if src_text:
                texts = [str(s.get("claim", ""))] + [str(b) for b in (s.get("bullets") or [])]
                for t in texts:
                    for num in NUM_RE.findall(t):
                        if num.strip() and num.strip() not in src_text:
                            mismatches.append({"slide": s.get("idx", i + 1), "number": num})
    cov = res.get("coverage") or {}
    for k in SIX:
        chk("coverage_%s" % k, cov.get(k) in {"done", "partial", "na"},
            "coverage.%s=%r" % (k, cov.get(k)))
    if src_text and mismatches:
        chk("number_fidelity", False, "%d 个数字未见于源文本" % len(mismatches))
    else:
        chk("number_fidelity", True, "no numbers or all found")
    ok_state = True
    if status == "ok":
        bad = [c for c in checks if c["verdict"] == "FAIL"]
        ok_state = not bad
        chk("status_consistency", ok_state, "status=ok but %d FAIL" % len(bad))
    report = {"ok": all(c["verdict"] == "PASS" for c in checks) and ok_state,
              "status": status, "checks": checks,
              "number_mismatches": mismatches}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
