#!/usr/bin/env python3
"""verify_evidence.py — 文献证据写作核验器。

输入：
  quotes.json    证据表摘录：[{"claim_id":"C-03","quote":"reduced latency by 32%","location":"p.6"}, ...]
  originals.json 原文关键句：[{"ref":"p.6","text":"... we reduced latency by 32% ..."}, ...]
  manuscript.json 可选：{"sentences": [{"text":"研究证实 X 显著优于 Y","grade_used":"C"}], "strong_words":["证实","显著"]}
校验：① 摘录逐字比对（EXACT/ALTERED/MISSING）
     ② 强度抽查：句子含强表述词但等级为 C/D → WARN
输出：stdout 报告，退出码 0=全过，1=有 FAIL/ALTERED，2=输入错误。
"""
import json
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    quotes, originals = load(sys.argv[1]), load(sys.argv[2])
    fails = []
    for q in quotes:
        quote, loc = q["quote"], q.get("location", "")
        hit = next((o for o in originals if loc and loc in str(o.get("ref", ""))), None)
        if hit is None:
            fails.append(q.get("claim_id", "?"))
            print(f"MISSING  {q.get('claim_id','?')} 定位 {loc} 在原文清单中找不到")
        elif quote in hit["text"]:
            print(f"EXACT    {q.get('claim_id','?')} 摘录逐字一致 @ {loc}")
        else:
            fails.append(q.get("claim_id", "?"))
            print(f"ALTERED  {q.get('claim_id','?')} 摘录与原文不一致 @ {loc}")
    if len(sys.argv) >= 4:
        ms = load(sys.argv[3])
        strong = set(ms.get("strong_words", []))
        low = {"C", "D"}
        for s in ms.get("sentences", []):
            if str(s.get("grade_used", "")).upper() in low and any(w in s["text"] for w in strong):
                print(f"STRENGTH WARN  低等级({s['grade_used']})使用了强表述：{s['text'][:30]}...")
    print(f"SUMMARY  fails={fails}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
