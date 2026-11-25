#!/usr/bin/env python3
"""qa_check.py — 问答准备包校验: 引用闭合 + 口径数字保真。

用法: python3 qa_check.py <qa_pack.json> <slides_plan.json> [source.txt]
检查:
  1. qa_pack 非空且每条有 question / slide_ref / answer_key;
  2. slide_ref 指向 slides_plan 中真实存在的页 idx;
  3. backup_slide(若给)同样指向真实页;
  4. 若提供源文本: answer_key 中的数字必须见于源文本(口径一致, 防答问口径与页面/原文矛盾)。
退出码: 0 通过; 1 引用断裂或数字不一致; 2 输入缺失。
输出: JSON 报告。
"""
import json
import os
import re
import sys

NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*[%±×·])?")


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: qa_check.py qa_pack.json slides_plan.json [source.txt]"}))
        sys.exit(2)
    qa_path, plan_path = sys.argv[1], sys.argv[2]
    if not (os.path.isfile(qa_path) and os.path.isfile(plan_path)):
        print(json.dumps({"ok": False, "error": "input file missing"}))
        sys.exit(2)
    qa = json.load(open(qa_path, encoding="utf-8"))
    plan = json.load(open(plan_path, encoding="utf-8"))
    idxs = {s.get("idx") for s in plan.get("slides", [])}
    src = ""
    for p in sys.argv[3:]:
        if os.path.isfile(p):
            src += open(p, encoding="utf-8", errors="ignore").read() + "\n"
    issues = []
    qas = qa.get("qa_pack") if isinstance(qa, dict) else qa
    if not isinstance(qas, list) or not qas:
        print(json.dumps({"ok": False, "error": "qa_pack empty"}))
        sys.exit(1)
    for i, item in enumerate(qas):
        for k in ("question", "slide_ref", "answer_key"):
            if k not in item:
                issues.append({"qa": i, "type": "missing_field", "detail": k})
        ref = item.get("slide_ref")
        if ref not in idxs:
            issues.append({"qa": i, "type": "broken_ref",
                           "detail": "slide_ref %r not in plan idxs" % ref})
        bs = item.get("backup_slide")
        if bs is not None and bs not in idxs:
            issues.append({"qa": i, "type": "broken_ref",
                           "detail": "backup_slide %r not in plan idxs" % bs})
        if src:
            ak = item.get("answer_key") or []
            for line in (ak if isinstance(ak, list) else [str(ak)]):
                for num in NUM_RE.findall(str(line)):
                    if num.strip() and num.strip() not in src:
                        issues.append({"qa": i, "type": "number_mismatch",
                                       "detail": "%r not in source" % num})
    report = {"ok": not issues, "n_qa": len(qas), "issues": issues}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
