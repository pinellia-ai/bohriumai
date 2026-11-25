#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patent_check — 专利号规范化、同族归并、分类号解析与法律状态口径审计（真实可运行，仅标准库）。

用法：
  python3 patent_check.py --records /app/work/records.jsonl --workdir /app/work

输出 patents.json：
  normalized（逐条公开号规范化，格式=国家代码+序号+种类代码）/ families（简单族归并：同优先权/同申请人+同标题近似）/
  classifications（IPC/CPC 解析到部大类小类）/ legal_status_audit（状态+来源+查询日期+滞后声明）/
  risk_flags（字段缺失、状态过期、同族口径不明）
不判定侵权、不评估价值、不替代法律意见。
"""
import argparse, json, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import searchlib as SL

KIND = {"A": "公开", "B": "授权", "U": "实用新型", "S": "外观设计", "T": "翻译文本",
        "A1": "公开(首次)", "A2": "公开(再次)", "B1": "授权(首次)", "B2": "授权(再版)", "T1": "翻译公开", "T2": "翻译授权"}

def normalize_number(raw):
    """公开号规范化：CN123456789A → (CN, 123456789, A)。返回 dict 或 None。"""
    if not raw:
        return None
    s = re.sub(r"[\s\-,.]", "", str(raw)).upper()
    m = re.match(r"^([A-Z]{2})(\d{6,})([A-Z]\d?)$", s)
    if not m:
        m = re.match(r"^([A-Z]{2})(\d{6,})$", s)
        if not m:
            return None
        return {"country": m.group(1), "serial": m.group(2), "kind": None, "normalized": s}
    return {"country": m.group(1), "serial": m.group(2), "kind": m.group(3),
            "kind_meaning": KIND.get(m.group(3), "未知名义"), "normalized": s}

def parse_classification(raw):
    """IPC/CPC 解析：如 'H01M 10/0562' → {section, class, subclass, group, subgroup}。"""
    out = []
    for part in re.split(r"[;,|\s]{2,}|\n", str(raw or "")):
        part = part.strip()
        m = re.match(r"^([A-H])\s?(\d{1,2})?\s?([A-Z])?\s?(\d{1,5}/\d{1,6})?", part)
        if not m:
            continue
        out.append({"raw": part, "section": m.group(1),
                    "class": (m.group(1) + str(m.group(2))) if m.group(2) else None,
                    "subclass": (m.group(1) + str(m.group(2)) + m.group(3)) if m.group(3) else None,
                    "group_subgroup": m.group(4)})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--workdir", default="/app/work")
    args = ap.parse_args()
    records = SL.load_jsonl(args.records)
    if not records:
        print("no records", file=sys.stderr)
        return 2

    normalized, risk_flags = [], []
    for r in records:
        f = r.get("fields", {})
        looks_patent = any(k in f for k in ("patent_number", "classification", "legal_status", "claims"))
        pn = normalize_number(f.get("patent_number") or f.get("id"))
        cls = parse_classification(f.get("classification", ""))
        entry = {"record_id": r["record_id"], "source": r["source"],
                 "raw_number": f.get("patent_number") or f.get("id"),
                 "normalized_number": pn, "classifications": cls,
                 "title": f.get("title"), "date": f.get("date"),
                 "legal_status": f.get("legal_status"),
                 "looks_patent": looks_patent}
        normalized.append(entry)
        if looks_patent and not pn:
            risk_flags.append({"record_id": r["record_id"],
                               "risk": "号码缺失或格式无法规范化（如仅申请人编号/内部ID）",
                               "evidence": str(f.get("patent_number") or f.get("id"))[:80]})
        if looks_patent and not f.get("legal_status"):
            risk_flags.append({"record_id": r["record_id"],
                               "risk": "法律状态缺失：语料未提供状态字段，不推测有效/失效"})

    # 同族归并：同一规范号去 kind 差异 / 同优先权日期+申请人 / 标题近似
    by_serial = defaultdict(list)
    for e in normalized:
        if e["normalized_number"]:
            by_serial[(e["normalized_number"]["country"], e["normalized_number"]["serial"])].append(e)
    families = []
    for (cc, serial), members in sorted(by_serial.items()):
        kinds = sorted({m["normalized_number"]["kind"] for m in members if m["normalized_number"]["kind"]})
        if len(members) > 1 or len(kinds) > 1:
            families.append({"family_key": cc + serial, "members": [m["record_id"] for m in members],
                             "kind_codes": kinds,
                             "kind_note": "同 serial 不同 kind code=公开/授权文本形态差异，同族口径=简单族；扩展族（优先权链）需优先权字段，语料缺失则标口径不明",
                             "merge_basis": [{"record_id": m["record_id"], "source": m["source"],
                                              "number": m["normalized_number"]["normalized"]} for m in members]})
    if any(not e.get("date") for e in normalized if e["looks_patent"]):
        risk_flags.append({"record_id": None, "risk": "部分记录缺申请日/公开日：扩展族（优先权链）口径不明"})

    # 同标题+同申请人 跨局族候选（简单族之外的归并证据，不自动等同同族）
    by_title = defaultdict(list)
    for e in normalized:
        if e["looks_patent"] and e.get("title"):
            by_title[SL.norm_title(e["title"])[:120]].append(e)
    title_groups = []
    for t, members in sorted(by_title.items()):
        if len(members) > 1 and len({m["normalized_number"]["country"] for m in members if m["normalized_number"]}) > 1:
            title_groups.append({"title_norm": t,
                                 "members": [m["record_id"] for m in members],
                                 "note": "同标题跨国家局：疑似同族/同申请主题，是否并入同一族需优先权字段佐证（unknown_scope 待人工）"})

    out = {"normalized": normalized,
           "families": families,
           "family_rule": "简单族=同国家同 serial；扩展族需优先权号字段（缺失时显式标注 unknown_scope）",
           "title_family_candidates": title_groups,
           "classifications_note": "IPC/CPC 解析到部/大类/小类/小组；未提供的记录不推测",
           "legal_status_audit": {"fields_present": sum(1 for e in normalized if e["legal_status"]),
                                  "note": "法律状态仅报告语料内登记值+来源+查询时间；转载页面不作为登记依据；不在快照内声称当前有效性"},
           "risk_flags": risk_flags,
           "boundary_note": "不做侵权判定/FTO/价值评估/法律意见；结果只来自授权来源文件并标注库名（source.file）"}
    SL.write_json(os.path.join(args.workdir, "patents.json"), out)
    SL.write_json(os.path.join(args.workdir, "patents_summary.json"), {
        "count": len(normalized), "families": len(families), "risk_flags": len(risk_flags)})
    print("normalized=%d families=%d risks=%d" % (len(normalized), len(families), len(risk_flags)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
