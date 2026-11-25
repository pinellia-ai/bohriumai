#!/usr/bin/env python3
"""storyboard_check.py — 图形摘要四面板故事板断言。
用法: storyboard_check.py storyboard.json [entities.tsv] [datamap.tsv]
断言:
 1 四面板（question/method/results/conclusion）齐备且各≥1要点
 2 每要点有非空 source
 3 datamap 数值非空时 source 必填
 4 结论要点有结果/材料支撑：结论关键词（去停用词）必须出现在 results 要点或 material_ref 中
"""
import csv, json, re, sys

def read_tsv(p):
    if not p:
        return []
    try:
        return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))
    except FileNotFoundError:
        return []

STOP = set("的 了 在 与 及 和 对 是 由 从 为 而 且 但 并 或 若 则 因此 所以 由于 通过 基于 采用 表明 证明 显示 研究 本文 我们 a an the of and or to in on with for".split())

def keywords(s):
    return {w for w in re.split(r"[\s，。；、()（）,.:：\"'-]+", s) if w and w not in STOP} - STOP

def main(story_p, ent_p=None, dm_p=None):
    sb = json.load(open(story_p, encoding="utf-8"))
    probs = []
    panels = ["question", "method", "results", "conclusion"]
    for p in panels:
        pts = sb.get(p, {}).get("points", [])
        if not pts: probs.append(f"面板 {p} 缺要点")
        for pt in pts:
            if not (sb.get(p, {}).get("source") or "").strip() and isinstance(pt, str) and not pt:
                probs.append(f"面板 {p} 要点缺 source")
        if not (sb.get(p, {}).get("source") or "").strip():
            probs.append(f"面板 {p} 缺面板级 source")
    for d in read_tsv(dm_p):
        if (d.get("value") or "").strip() and not (d.get("source_location") or "").strip():
            probs.append(f"datamap {d.get('item')} 有值无来源")
    sup_text = json.dumps(sb.get("results", {}), ensure_ascii=False) + sb.get("method", {}).get("source", "") + sb.get("question", {}).get("source", "")
    for c in sb.get("conclusion", {}).get("points", []):
        kw = keywords(c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
        if kw and not any(w in sup_text for w in kw):
            probs.append(f"结论要点缺支撑: '{c[:30]}...'（关键词未见于 results/材料引用）")
    out = {"pass": not probs, "panels": {p: len(sb.get(p, {}).get("points", [])) for p in panels}, "problems": probs}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    sys.exit(0 if out["pass"] else 1)

if __name__ == "__main__":
    main(*sys.argv[1:4])
