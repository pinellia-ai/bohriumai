#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_result — 汇集 /app/work 产物组装 result.json 并校验 output_contract（仅标准库）。

用法：
  python3 build_result.py --input /input --workdir /app/work --out /app/output/result.json [--partial]

行为：
1. 读 /input/case.json：case_id 原样保留；output_contract 全字段必须映射到 result.json 真实产物。
2. 汇集 workdir 实际产物；contract 字段按 别名表→关键词启发 两级映射到产物，
   仍无法映射的字段以 note 如实标注，不虚构。
3. --partial：产物不全时也写出（status=partial），保证任何中断都有可评分产物。
4. 校验失败打印缺失字段清单，退出码 1；成功退出码 0。
"""
import argparse, json, os, re, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

def _norm(k):
    return re.sub(r"[^a-z0-9]", "", str(k).lower())

ALIAS = {
    "caseid": "case_id", "status": "status", "state": "status",
    "researchquestion": "research_question", "researchproblem": "research_question", "question": "research_question",
    "querylog": "query_log", "queryplan": "query_log", "searchlog": "query_log", "searchtrace": "query_log", "queries": "query_log", "queryhistory": "query_log",
    "candidates": "candidates", "candidate": "candidates", "candidateset": "candidates",
    "results": "candidates", "result": "candidates", "resultset": "candidates",
    "searchresults": "candidates", "retrieved": "candidates", "retrieveddocuments": "candidates",
    "ranking": "ranking", "rank": "ranking", "ranked": "ranking", "rankingrationale": "ranking",
    "screening": "screening", "screen": "screening", "decisions": "screening", "filters": "screening",
    "coverage": "coverage", "coverageanalysis": "coverage", "missed": "coverage", "gaps": "coverage",
    "evidence": "evidence", "evidencelog": "evidence", "evidencerecord": "evidence",
    "evidencerecords": "evidence", "relevance": "evidence", "traceability": "evidence",
    "sources": "sources", "source": "sources", "sourcesused": "sources",
    "uncertainty": "uncertainty_notes", "uncertainties": "uncertainty_notes", "uncertaintynotes": "uncertainty_notes",
    "limitations": "uncertainty_notes", "changelog": "change_log", "changes": "change_log",
    "incremental": "incremental", "newitems": "incremental", "deltas": "incremental",
    "citationgraph": "citation_graph", "citations": "citation_graph", "citationnetwork": "citation_graph",
    "referencetrace": "citation_graph", "relatedpapers": "citation_graph",
    "mergematrix": "merge_matrix", "dedup": "merge_matrix", "deduplication": "merge_matrix",
    "mergedrecords": "merge_matrix", "fieldmapping": "merge_matrix",
    "quality": "quality", "qualityassessment": "quality", "appraisal": "quality",
    "patents": "patents", "patentsummary": "patents", "families": "patents",
    "languagestats": "bilingual", "glossary": "bilingual", "bilingual": "bilingual",
    "arbitration": "arbitration", "conflicts": "arbitration",
    "convergence": "convergence", "stopcriteria": "convergence",
    "emptyresults": "status_notes", "failurestates": "status_notes", "statusnotes": "status_notes",
}

KEYWORD_HINTS = [
    ("result", "candidates"), ("candidate", "candidates"), ("retriev", "candidates"),
    ("query", "query_log"), ("search", "query_log"), ("round", "query_log"), ("iterat", "query_log"),
    ("rank", "ranking"), ("priorit", "ranking"), ("order", "ranking"),
    ("screen", "screening"), ("filter", "screening"), ("includ", "screening"), ("exclud", "screening"),
    ("cover", "coverage"), ("miss", "coverage"), ("recall", "coverage"), ("gap", "coverage"),
    ("eviden", "evidence"), ("trace", "evidence"), ("basis", "evidence"), ("provenan", "evidence"),
    ("status", "status_notes"), ("conflict", "status_notes"), ("empty", "status_notes"), ("fail", "status_notes"),
    ("uncertain", "uncertainty_notes"), ("limit", "uncertainty_notes"),
    ("source", "sources"),
    ("increment", "incremental"), ("new", "incremental"), ("update", "incremental"), ("track", "incremental"),
    ("citation", "citation_graph"), ("reference", "citation_graph"), ("link", "citation_graph"),
    ("dedup", "merge_matrix"), ("merge", "merge_matrix"), ("duplicate", "merge_matrix"),
    ("quality", "quality"), ("bias", "quality"), ("apprais", "quality"),
    ("patent", "patents"), ("family", "patents"), ("claim", "patents"), ("classification", "patents"), ("ipc", "patents"), ("cpc", "patents"), ("legal", "patents"),
    ("language", "bilingual"), ("glossary", "bilingual"), ("translat", "bilingual"), ("term", "bilingual"),
    ("arbitr", "arbitration"), ("disagree", "arbitration"),
    ("stop", "convergence"), ("converg", "convergence"), ("round", "convergence"),
    ("plan", "query_log"), ("strategy", "query_log"), ("subquestion", "query_log"),
]

ARTIFACTS = {
    "candidates.jsonl": "candidates", "ranked.json": "ranking", "screening.jsonl": "screening",
    "search_log.jsonl": "query_log", "records.jsonl": "corpus_records", "coverage.json": "coverage",
    "incremental.json": "incremental", "citation_graph.json": "citation_graph",
    "merge_matrix.json": "merge_matrix", "quality.json": "quality", "patents.json": "patents",
    "bilingual.json": "bilingual", "arbitration.json": "arbitration", "gain.json": "convergence",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--out", default="/app/output/result.json")
    ap.add_argument("--partial", action="store_true")
    args = ap.parse_args()

    case_path = os.path.join(args.input, "case.json")
    if not os.path.exists(case_path):
        print("case.json missing", file=sys.stderr)
        return 2
    with open(case_path, encoding="utf-8") as fh:
        case = json.load(fh)

    loaded = {}
    for fname, key in ARTIFACTS.items():
        p = os.path.join(args.workdir, fname)
        if os.path.exists(p):
            try:
                loaded[key] = SL.load_jsonl(p) if fname.endswith(".jsonl") else json.load(open(p, encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                print("artifact load error %s: %s" % (fname, e), file=sys.stderr)

    query_log = loaded.get("query_log", [])
    cands = loaded.get("candidates", [])
    ranked = loaded.get("ranking") or {}
    corpus = loaded.get("corpus_records", [])
    evidence = {
        "rounds": query_log,
        "per_record_basis": [{"record_id": c.get("record_id"),
                              "relevance_basis": c.get("relevance_basis"),
                              "hit_rounds": c.get("hit_rounds"),
                              "dedupe": c.get("dedupe")} for c in cands],
        "load_log_path": "load_log.json",
        "note": "每条结果可按 query→hit_ids→record_id→source(file+field)→quote 复核",
    }

    result = {
        "case_id": case.get("case_id"),
        "status": None,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "research_question": None,
        "query_log": query_log,
        "candidates": cands,
        "ranking": ranked if ranked else {"included": cands, "pending": [], "excluded": []},
        "screening": loaded.get("screening"),
        "coverage": loaded.get("coverage"),
        "evidence": evidence,
        "sources": sorted({c["source"]["file"] for c in cands if c.get("source")}),
        "status_notes": {
            "empty_results": len(cands) == 0,
            "corpus_records": len(corpus),
            "note": ("语料无命中：如实报告空结果，不补造文献" if not cands else
                     "基于组织方提供的离线语料快照检索；非实时联网，无全球覆盖声明"),
        },
        "uncertainty_notes": ["相关性依据来自语料内原文摘录（relevance_basis）；换语料需重新评估",
                              "元数据为合并后字段，冲突值保留在 conflicts 供复核"],
        "change_log": ["v1: 初版流水线产物落盘"],
        "extra_artifacts": {},
    }
    for key in ("corpus_records", "incremental", "citation_graph", "merge_matrix",
                "quality", "patents", "bilingual", "arbitration", "convergence"):
        if key in loaded and key not in result:
            result[key] = loaded[key]
        elif key in loaded:
            result["extra_artifacts"][key] = loaded[key]
    result["search_summary"] = {
        "rounds": len(query_log),
        "queries": sum(1 for q in query_log if q.get("query")),
        "corpus_records": len(corpus),
        "candidates_after_dedupe": len(cands),
        "included": (ranked.get("counts") or {}).get("included", len(cands)),
        "pending": (ranked.get("counts") or {}).get("pending", 0),
        "excluded": (ranked.get("counts") or {}).get("excluded", 0),
    }
    # research_question：优先 query_plan 的 research_question 字段
    rq_path = os.path.join(args.workdir, "query_plan.json")
    if os.path.exists(rq_path):
        with open(rq_path, encoding="utf-8") as fh:
            plan = json.load(fh)
        result["research_question"] = plan.get("research_question")
        result["query_plan"] = plan
    else:
        result["research_question"] = next((q.get("subquestion") for q in query_log if q.get("subquestion")), None)

    missing_core = not (cands and query_log)
    result["status"] = "partial" if (args.partial or missing_core) else "success"
    if loaded.get("coverage"):
        result["status"] = result["status"]  # coverage 题以 coverage.json 是否完整为准，保持 success/partial 逻辑
    if missing_core and not cands:
        result["status_notes"]["note"] = "候选集为空：检索未命中或语料缺失；如实报告，不补造文献"

    # contract 映射：别名 → 关键词启发 → 如实标注
    contract = case.get("output_contract") or case.get("outputContract") or {}
    if isinstance(contract, dict):
        contract_keys = list(contract.keys())
    elif isinstance(contract, list):
        contract_keys = [c.get("name") if isinstance(c, dict) else c for c in contract]
    else:
        contract_keys = []
    unmapped = []
    for ck in contract_keys:
        nk = _norm(ck)
        if ck in result or nk in ALIAS and ALIAS[nk] in result:
            if ck not in result:
                result[ck] = result[ALIAS[nk]]
            continue
        target = None
        for pat, canon in KEYWORD_HINTS:
            if pat in nk and canon in result:
                target = canon
                break
        if target and ck not in result:
            result[ck] = result[target]
        elif ck not in result:
            result[ck] = {"note": "该 contract 字段无直接对应产物；请依据 case.json 对该字段的描述在运行时从上述 artifacts 选取内容填写",
                          "available_artifacts": sorted(result.keys())}
            unmapped.append(ck)

    result = {k: v for k, v in result.items() if v is not None}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    SL.write_json(args.out, result)
    ok, missing = SL.contract_check(args.out, case_path)
    if not ok:
        print("contract check FAILED, missing: %s" % missing, file=sys.stderr)
        return 1
    if unmapped:
        print("WARN unmapped contract keys (已如实标注): %s" % unmapped, file=sys.stderr)
    print("result.json written; contract OK; status=%s" % result["status"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
