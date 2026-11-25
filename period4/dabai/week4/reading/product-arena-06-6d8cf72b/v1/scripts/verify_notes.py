#!/usr/bin/env python3
"""笔记锚点校验：support_span 必须在原文中，anchor 指向的 section 必须存在。
用法: python3 scripts/verify_notes.py --notes knowledge_points.jsonl --corpus corpus.txt --sections sections.jsonl
      python3 scripts/verify_notes.py --selftest"""
import argparse
import json
import os
import sys


def load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def verify(notes_path, corpus_path, sections_path):
    corpus = open(corpus_path, encoding="utf-8").read()
    section_ids = {s["section_id"] for s in load_jsonl(sections_path)}
    problems = []
    total = 0
    for n in load_jsonl(notes_path):
        total += 1
        nid = n.get("kp_id", "?")
        span = n.get("support_span")
        if span and span not in corpus:
            problems.append((nid, "support_span not found in corpus"))
        anchor = n.get("anchor", {})
        sid = anchor.get("section_id")
        if not sid or sid not in section_ids:
            problems.append((nid, f"anchor section_id invalid: {sid}"))
        if "page_no" not in anchor:
            problems.append((nid, "anchor missing page_no"))
    return total, problems


def selftest():
    tmpdir = __import__("tempfile").mkdtemp()
    corpus = os.path.join(tmpdir, "corpus.txt")
    notes = os.path.join(tmpdir, "notes.jsonl")
    sections = os.path.join(tmpdir, "sections.jsonl")
    open(corpus, "w").write("92% CO2 conversion was obtained at 350 C.\n")
    with open(sections, "w") as f:
        f.write(json.dumps({"section_id": "S3", "level": 1, "title": "Results"}) + "\n")
    good = {"kp_id": "KP1", "type": "finding", "support_span": "92% CO2 conversion was obtained at 350 C",
            "anchor": {"section_id": "S3", "page_no": 4}}
    bad = {"kp_id": "KP2", "type": "concept", "support_span": "fabricated span",
           "anchor": {"section_id": "S9", "page_no": 1}}
    with open(notes, "w") as f:
        for d in (good, bad):
            f.write(json.dumps(d) + "\n")
    total, problems = verify(notes, corpus, sections)
    assert total == 2 and len(problems) == 2, problems
    print("selftest ok: 1 valid, 2 problems caught on fabricated note")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes")
    ap.add_argument("--corpus")
    ap.add_argument("--sections")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.notes and a.corpus and a.sections):
        print("usage: verify_notes.py --selftest | --notes <f> --corpus <f> --sections <f>")
        return 2
    total, problems = verify(a.notes, a.corpus, a.sections)
    print(f"{total} notes checked, {len(problems)} problems")
    for nid, msg in problems:
        print(f" - {nid}: {msg}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
