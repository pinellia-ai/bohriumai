#!/usr/bin/env python3
"""deck_diff.py — 演示稿迭代对比: 两版页级计划的逐页差异与修改记录。

用法: python3 deck_diff.py <plan_v1.json> <plan_v2.json> [out_changelog.json]
比较维度:
  - 页级: 新增/删除/移动(按 title 匹配同页); 
  - 字段级: 同页内 title/claim/bullets/notes/figure.ref/evidence.locator 的变化;
  - 汇总 changelog: 每轮"改了什么", 供版本记录(version_log)与回退定位。
退出码: 0 成功; 2 输入缺失/不合法。
"""
import json
import os
import sys

FIELDS = ["title", "claim", "bullets", "notes", "figure", "evidence"]


def load(path):
    if not os.path.isfile(path):
        print(json.dumps({"ok": False, "error": "missing: %s" % path}))
        sys.exit(2)
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"ok": False, "error": "bad json %s: %s" % (path, e)}))
        sys.exit(2)


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: deck_diff.py v1.json v2.json [out.json]"}))
        sys.exit(2)
    a, b = load(sys.argv[1]), load(sys.argv[2])
    idx_a = {s.get("title", "#%d" % i): s for i, s in enumerate(a.get("slides", []))}
    idx_b = {s.get("title", "#%d" % i): s for i, s in enumerate(b.get("slides", []))}
    added = [t for t in idx_b if t not in idx_a]
    removed = [t for t in idx_a if t not in idx_b]
    changed = []
    for t, sb in idx_b.items():
        if t not in idx_a:
            continue
        sa = idx_a[t]
        diffs = {}
        for f in FIELDS:
            if sa.get(f) != sb.get(f):
                diffs[f] = {"v1": sa.get(f), "v2": sb.get(f)}
        if diffs:
            changed.append({"slide": t, "fields": list(diffs.keys()), "diff": diffs})
    changelog = {
        "v1_slides": len(a.get("slides", [])), "v2_slides": len(b.get("slides", [])),
        "added": added, "removed": removed, "changed": changed,
        "summary": "新增%d页 删除%d页 修改%d页" % (len(added), len(removed), len(changed))}
    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(changelog, f, ensure_ascii=False, indent=1)
    print(json.dumps(changelog, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
