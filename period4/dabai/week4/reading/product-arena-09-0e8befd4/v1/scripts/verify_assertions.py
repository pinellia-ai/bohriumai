#!/usr/bin/env python3
"""校验 nanopublication 四部分结构与证据子串匹配。
用法: python3 scripts/verify_assertions.py --nanopubs nanopubs.jsonl --corpus corpus.txt
      python3 scripts/verify_assertions.py --selftest"""
import argparse
import json
import os
import sys

PARTS = ["Head", "Assertion", "Provenance", "PublicationInfo"]
NP_FIELDS = ["np_id", "Head", "Assertion", "Provenance", "PublicationInfo"]
ASSERTION_FIELDS = ["subject", "predicate", "object", "qualifier"]
PROVENANCE_FIELDS = ["evidence_span", "evidence_loc", "doc_title", "authors"]


def verify(nanopubs_path, corpus_path=None):
    corpus = open(corpus_path, encoding="utf-8").read() if corpus_path else None
    problems = []
    total = 0
    for line in open(nanopubs_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        np_ = json.loads(line)
        total += 1
        np_id = np_.get("np_id", "?")
        for f in NP_FIELDS:
            if f not in np_:
                problems.append((np_id, f"missing part: {f}"))
        a = np_.get("Assertion", {})
        for f in ASSERTION_FIELDS:
            if f not in a:
                problems.append((np_id, f"Assertion missing {f}"))
        p = np_.get("Provenance", {})
        for f in PROVENANCE_FIELDS:
            if f not in p:
                problems.append((np_id, f"Provenance missing {f}"))
        span = p.get("evidence_span")
        if span and corpus and span not in corpus:
            problems.append((np_id, "evidence_span not found in corpus"))
    return total, problems


def selftest():
    tmpdir = __import__("tempfile").mkdtemp()
    corpus = os.path.join(tmpdir, "corpus.txt")
    nps = os.path.join(tmpdir, "nps.jsonl")
    open(corpus, "w").write("92% CO2 conversion was obtained at 350 C.\n")
    good = {"np_id": "NP001",
            "Head": {"np_id": "NP001"},
            "Assertion": {"subject": "cat", "predicate": "achieves", "object": "92%", "qualifier": "350 C"},
            "Provenance": {"evidence_span": "92% CO2 conversion was obtained at 350 C",
                           "evidence_loc": {"page_no": 1}, "doc_title": "T", "authors": ["A"]},
            "PublicationInfo": {"extracted_at_runtime": True}}
    bad = {"np_id": "NP002", "Head": {}, "Assertion": {"subject": "x"},
           "Provenance": {"evidence_span": "not in corpus"}}
    with open(nps, "w") as f:
        for d in (good, bad):
            f.write(json.dumps(d) + "\n")
    total, problems = verify(nps, corpus)
    assert total == 2 and len(problems) >= 3, problems
    print("selftest ok: 1 valid, problems caught:", problems)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nanopubs")
    ap.add_argument("--corpus")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.nanopubs:
        print("usage: verify_assertions.py --nanopubs <f> [--corpus <f>] | --selftest")
        return 2
    total, problems = verify(a.nanopubs, a.corpus)
    print(f"{total} nanopubs checked, {len(problems)} problems")
    for nid, msg in problems:
        print(f" - {nid}: {msg}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
