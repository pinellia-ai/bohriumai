#!/usr/bin/env python3
"""校验三元组证据：evidence_span 必须出现在原文文本中（子串匹配）。
用法: python3 scripts/verify_graph.py --triples triples.jsonl --corpus corpus.txt
      python3 scripts/verify_graph.py --selftest"""
import argparse
import json
import os
import sys


def verify(triples_path, corpus_path):
    corpus = open(corpus_path, encoding="utf-8").read()
    bad = []
    total = 0
    for line in open(triples_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        t = json.loads(line)
        total += 1
        for key in ("triple_id", "subject", "predicate", "object",
                    "evidence_span", "source_ref", "strength"):
            if key not in t:
                bad.append((t.get("triple_id", "?"), f"missing {key}"))
        if t.get("evidence_span") and t["evidence_span"] not in corpus:
            bad.append((t.get("triple_id", "?"), "evidence_span not found in corpus"))
        if t.get("strength") == "direct" and not t.get("self_reported"):
            bad.append((t.get("triple_id", "?"), "direct edge must be self_reported"))
    return total, bad


def selftest():
    tmpdir = __import__("tempfile").mkdtemp()
    corpus = os.path.join(tmpdir, "corpus.txt")
    triples = os.path.join(tmpdir, "triples.jsonl")
    open(corpus, "w").write("GraphQA outperforms the strongest GNN baseline by 3.2% on Cora.\n")
    with open(triples, "w") as f:
        f.write(json.dumps({
            "triple_id": "T001", "subject": "E1", "predicate": "outperforms",
            "object": "E2", "evidence_span": "outperforms the strongest GNN baseline",
            "source_ref": {"page_no": 1}, "strength": "direct", "self_reported": True,
        }) + "\n")
        f.write(json.dumps({
            "triple_id": "T002", "subject": "E3", "predicate": "uses",
            "object": "E4", "evidence_span": "fabricated span",
            "source_ref": {}, "strength": "direct", "self_reported": False,
        }) + "\n")
    total, bad = verify(triples, corpus)
    assert total == 2 and len(bad) == 2, bad
    print("selftest ok: 1 verified, 2 caught:", bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--triples")
    ap.add_argument("--corpus")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.triples or not a.corpus:
        print("usage: verify_graph.py --triples <f> --corpus <f> | --selftest")
        return 2
    total, bad = verify(a.triples, a.corpus)
    print(f"{total} triples checked, {len(bad)} problems")
    for tid, msg in bad:
        print(f" - {tid}: {msg}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
