#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bilingual — 跨语言术语对齐与双语字段匹配（真实可运行，仅标准库）。

用法：
  python3 bilingual.py --input /input --workdir /app/work --glossary /app/work/glossary.json
      [--query "科研问题原文"]

glossary.json 结构（由 Agent 从语料观察+领域知识构建，逐条带依据）：
  {"concepts": [{"concept_id":"C1","zh":"细胞焦亡","en":"pyroptosis",
                 "variants":["pyroptotic"," GAS"],"basis":"语料 R0007 标题出现 pyroptosis"}],
   "abbreviations": [{"abbr":"GAS","meanings":["gasdermin","Group A Streptococcus"],
                      "ambiguity_note":"缩写歧义：按语料共现判定"}]}

输出 bilingual.json：
  glossary_used（实际用到的概念与变体，逐条带 basis）/ language_stats（逐记录语言判定）/
  cross_lingual_hits（每条命中的语种+版本：original/translation/bilingual）/ 
  false_positive_checks（高风险命中的回译/语义核对记录）/ untranslated（术语表未覆盖概念）
"""
import argparse, json, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

CJK = re.compile(r"[\u4e00-\u9fff]")
KANA = re.compile(r"[\u3040-\u30ff]")
HANGUL = re.compile(r"[\uac00-\ud7af]")
CYRILLIC = re.compile(r"[\u0400-\u04ff]")

def detect_language(text):
    """语言判定（字符级启发式），输出语种+置信。"""
    t = text or ""
    if CJK.search(t):
        return {"language": "zh", "confidence": "high", "method": "CJK字符占比"}
    if KANA.search(t):
        return {"language": "ja", "confidence": "high", "method": "假名字符"}
    if HANGUL.search(t):
        return {"language": "ko", "confidence": "high", "method": "谚文字符"}
    if CYRILLIC.search(t):
        return {"language": "ru", "confidence": "high", "method": "西里尔字符"}
    if re.search(r"[a-zA-Z]", t):
        return {"language": "en", "confidence": "medium", "method": "拉丁字符默认（可能为其他拉丁语种，标注不确定）"}
    return {"language": "unknown", "confidence": "low", "method": "无可识别字符"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="/input")
    ap.add_argument("--workdir", default="/app/work")
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--query", default="")
    args = ap.parse_args()

    records, load_log = SL.load_records(args.input)
    if not records:
        print("corpus empty", file=sys.stderr)
        return 2
    with open(args.glossary, encoding="utf-8") as fh:
        glo = json.load(fh)

    # 每条记录语言判定 + 版本判定（原文/译文/双语刊）
    lang_stats = []
    for r in records:
        f = r.get("fields", {})
        declared = f.get("language")
        det = detect_language(r.get("text", "")[:2000])
        version = "original"
        title = f.get("title", "")
        if declared and CJK.search(str(declared)):
            version = "bilingual_or_declared_non_en"
        if f.get("abstract") and CJK.search(f["abstract"]) and re.search(r"[a-zA-Z]", title):
            version = "bilingual"
        lang_stats.append({"record_id": r["record_id"], "declared_language": declared,
                           "detected": det, "version": version, "source": r["source"]})

    # 术语表覆盖审计
    used, untranslated = [], []
    corpus_text = " ".join(r.get("text", "")[:5000] for r in records).lower()
    for c in glo.get("concepts", []):
        variants = [c.get("zh", "")] + [c.get("en", "")] + list(c.get("variants", []))
        ct = SL.norm_text(corpus_text)
        found = [v for v in variants if v and SL.norm_text(v) in ct]
        entry = {"concept_id": c["concept_id"], "zh": c.get("zh"), "en": c.get("en"),
                 "variants_tried": variants, "found_in_corpus": found,
                 "basis": c.get("basis", "Agent 从语料观察+领域知识构建"),
                 "in_query": bool(args.query and c.get("zh") and c["zh"] in args.query)}
        if found:
            used.append(entry)
        else:
            entry["status"] = "glossary_term_not_in_corpus"
            untranslated.append(entry)

    # 跨语言命中：任一概念变体命中即计入，标注命中的语种与版本
    hits = []
    for r in records:
        f = r.get("fields", {})
        text = r.get("text", "")
        matched = []
        for c in glo.get("concepts", []):
            for v in [c.get("zh"), c.get("en")] + list(c.get("variants", [])):
                if v and SL.norm_text(v) in SL.norm_text(text):
                    matched.append({"concept_id": c["concept_id"], "matched_variant": v})
                    break
        if matched:
            st = next((s for s in lang_stats if s["record_id"] == r["record_id"]), {})
            quote = ""
            for jp, val in r.get("text_parts", []):
                if any(SL.norm_text(m["matched_variant"]) in SL.norm_text(val) for m in matched):
                    quote = val.strip()[:160]
                    break
            hits.append({"record_id": r["record_id"], "title": f.get("title"),
                         "matched_concepts": matched,
                         "language": st.get("detected", {}).get("language"),
                         "version": st.get("version"),
                         "evidence_quote": quote, "source": r["source"]})

    # 假阳性复核：缩写歧义项
    fp_checks = []
    for a in glo.get("abbreviations", []):
        if len(a.get("meanings", [])) > 1:
            fp_checks.append({"abbr": a["abbr"], "risk": "一词多义",
                              "meanings": a["meanings"],
                              "rule": "命中该缩写的记录需核对上下文共现词；词面对应语义不同者剔除并记录",
                              "status": "pending_manual_or_context_check"})

    out = {"query": args.query, "glossary_used": used, "untranslated": untranslated,
           "language_stats": lang_stats,
           "language_summary": dict(Counter(s["detected"]["language"] for s in lang_stats)),
           "cross_lingual_hits": hits, "hit_count": len(hits),
           "false_positive_checks": fp_checks,
           "honesty_note": "语言判定为字符级启发式；受控翻译仅在 Agent 有翻译能力时对查询/术语进行并保留对照；不声称覆盖全球非英语文献",
           "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}
    SL.write_json(os.path.join(args.workdir, "bilingual.json"), out)
    # 同步供 run_search 使用的术语表（term→变体 扁平化）
    flat = {}
    for c in glo.get("concepts", []):
        flat[c.get("en") or c.get("zh") or c["concept_id"]] = [v for v in [c.get("zh"), c.get("en")] + list(c.get("variants", [])) if v]
    SL.write_json(os.path.join(args.workdir, "glossary_used.json"), flat)
    print("records=%d hits=%d glossary_used=%d untranslated=%d" %
          (len(records), len(hits), len(used), len(untranslated)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
