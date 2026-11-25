#!/usr/bin/env python3
"""check_results.py — 结果与讨论章节校验器。

输入：
  ledger.json            数值台账：[{"id":"L-01","value":"28.4±1.2","unit":"mg/L","source":"Fig.2B"}, ...]
  manuscript_numbers.json 正文数值：["28.4±1.2", ...]
  figure_refs.json       {"catalog": ["Fig.1","Fig.2","Table1"], "cited": ["Fig.1","Fig.5"]}
  crossing.json          可选分节纪律：{"results_sentences": [{"text":"...","is_explanation": true}]}
校验：① 正文数值必须在台账中（NUM OK/FAIL）
     ② 正文引用图表号必须在图表清单中（FIG OK/FAIL）
     ③ 结果段解释性句子报警（CROSSING WARN）
输出：stdout 报告，退出码 0=全过，1=有 FAIL，2=输入错误。
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    ledger, nums, figs = load(sys.argv[1]), load(sys.argv[2]), load(sys.argv[3])
    fails = []
    ledger_vals = {str(x.get("value")).strip() for x in ledger}
    for v in nums:
        if str(v).strip() in ledger_vals:
            print(f"NUM OK    {v}")
        else:
            fails.append(f"number:{v}")
            print(f"NUM FAIL  {v} 不在数值台账（台账外数值禁止写入正文）")
    catalog = set(figs.get("catalog", []))
    for c in figs.get("cited", []):
        if c in catalog:
            print(f"FIG OK    {c}")
        else:
            fails.append(f"figure:{c}")
            print(f"FIG FAIL  {c} 引用了图表清单中不存在的编号")
    if len(sys.argv) >= 5:
        crossing = load(sys.argv[4])
        for i, s in enumerate(crossing.get("results_sentences", [])):
            if s.get("is_explanation"):
                print(f"CROSSING WARN  结果段第{i+1}句是解释性内容，应移入讨论：{s['text'][:30]}...")
    print(f"SUMMARY   fails={fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
