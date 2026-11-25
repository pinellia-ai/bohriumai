#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""searchlib — 离线语料检索流水线核心库（仅标准库，真实可运行）。

设计约束（与题面一致）：
- 只在组织方提供的离线语料（/input 下材料文件）上检索；绝不联网、绝不编造文献。
- 每条结果带 source（语料文件+字段/JSON路径）+ relevance_basis（命中的原文短句）。
- 每轮检索记录 {查询式, 匹配字段, 命中数, 命中ID}，写入 search_log.jsonl，可复跑。
"""
import json, os, re, csv, math, sys, io, unicodedata
from collections import Counter, OrderedDict, defaultdict

STOPWORDS = set("""a an the of for in on to and or is are was were with by from as at into about
between within over under this that these those it its be been being we our their they there
which who whom what when where how why not no nor but if then than also such can could may might
will would shall should must do does did done using used use vs et al via per based study studies
paper papers article articles journal result results method methods""".split())

# 常见文献字段别名（大小写不敏感；抽取时归一到规范名）
FIELD_ALIASES = {
    "title": ["title", "name", "paper_title", "article_title", "dc:title", "TI"],
    "authors": ["authors", "author", "creator", "creators", "dc:creator", "authorString", "AU", "author_list"],
    "year": ["year", "pubyear", "publication_year", "pubYear", "issued", "date", "created-date", "PY"],
    "doi": ["doi", "DOI", "dc:identifier", "url_doi"],
    "venue": ["journal", "venue", "container-title", "source", "journal-title", "booktitle", "SO", "publicationName"],
    "abstract": ["abstract", "summary", "abstractText", "AB", "description"],
    "type": ["type", "pubtype", "publication_type", "article-type", "genre", "DT", "worktype"],
    "language": ["language", "lang", "LA", "iso_language"],
    "id": ["id", "pmid", "pmcid", "arxiv_id", "cord_uid", "record_id", "uid", "accession"],
    "references": ["references", "reference", "refs", "cited_by", "citations", "cites", "reference_list", "referenced_works"],
    "keywords": ["keywords", "keyword", "mesh_terms", "subject", "subjects", "DE", "topics"],
    "claims": ["claims", "claim", "claim1", "independent_claims"],
    "classification": ["classification", "ipc", "cpc", "ipc_codes", "cpc_codes", "classifications"],
    "patent_number": ["patent_number", "publication_number", "public_number", "pn", "doc_number"],
    "legal_status": ["legal_status", "status", "patent_status"],
    "date": ["date", "publication_date", "date_published", "filing_date", "priority_date", "granted_date"],
}

def norm_text(s):
    """小写、去重音、非字母数字转空格。"""
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", s.lower()).strip()

def tokenize(s):
    toks = [t for t in norm_text(s).split() if t not in STOPWORDS and len(t) > 1]
    # 中文字符切单字二元组合，保证中文可检索
    out = []
    for t in toks:
        if re.search(r"[\u4e00-\u9fff]", t):
            chars = re.findall(r"[\u4e00-\u9fff]|[a-z0-9]+", t)
            out.extend(chars)
            out.extend([chars[i] + chars[i + 1] for i in range(len(chars) - 1)
                        if len(chars[i]) == 1 and len(chars[i + 1]) == 1])
        else:
            out.append(t)
    return out

def norm_title(s):
    return norm_text(s)

def norm_doi(s):
    m = re.search(r"10\.\d{4,9}/\S+", str(s or ""), re.I)
    return m.group(0).strip(".,;\"'").lower() if m else ""

def norm_patent_number(s):
    """专利号规范化：去空格标点，保留字母前缀与数字。"""
    if s is None:
        return ""
    s = re.sub(r"[\s,.\-]", "", str(s)).upper()
    return s

# ---------- Step 1: 语料装载与记录抽取 ----------

def list_material_files(input_dir):
    files = []
    for root, _dirs, names in os.walk(input_dir):
        for n in sorted(names):
            p = os.path.join(root, n)
            try:
                size = os.path.getsize(p)
            except OSError:
                continue
            files.append({"path": p, "rel": os.path.relpath(p, input_dir), "size": size})
    return files

def _guess_field(fname_key):
    k = str(fname_key).strip().lower()
    for canonical, aliases in FIELD_ALIASES.items():
        if any(a.lower() == k for a in aliases):
            return canonical
    return None

def _flatten(obj, prefix=""):
    """把嵌套 dict 展平成 (jsonpath, value)。"""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(_flatten(v, prefix + "." + str(k) if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(_flatten(v, prefix + "[%d]" % i if prefix else "[%d]" % i))
    else:
        out.append((prefix, obj))
    return out

def _record_from_mapping(mapping, source_file, source_field):
    rec = {"source": {"file": source_file, "field": source_field}, "fields": {}, "raw": mapping}
    texts = []
    flat = _flatten(mapping)
    for jp, val in flat:
        if not isinstance(val, (str, int, float)):
            continue
        leaf = jp.split(".")[-1].split("[")[0] if jp else ""
        canon = _guess_field(leaf)
        if canon and canon not in rec["fields"]:
            rec["fields"][canon] = str(val)
        if isinstance(val, str) and len(val) > 1:
            texts.append((jp, val))
    rec["text_parts"] = texts
    rec["text"] = " ".join(v for _jp, v in texts)
    return rec

def _collect_records(obj, source_file, source_field, out, depth=0):
    if depth > 6:
        return
    if isinstance(obj, list):
        if obj and all(isinstance(x, dict) for x in obj) and len(obj) >= 1:
            for i, x in enumerate(obj):
                _collect_records(x, source_file, source_field + ("[%d]" % i if len(obj) > 1 else ""), out, depth + 1)
        return
    if isinstance(obj, dict):
        # 若 dict 含文献字段（title 等），视为一条记录
        leaf_keys = {_guess_field(str(k).split(".")[0].split("[")[0].strip().lower()) for k in obj}
        if "title" in leaf_keys or "abstract" in leaf_keys:
            out.append(_record_from_mapping(obj, source_file, source_field))
            return
        for k, v in obj.items():
            _collect_records(v, source_file, source_field + "." + str(k) if source_field else str(k), out, depth + 1)

def load_records(input_dir, skip=("case.json",)):
    """扫描 /input 全部材料，抽取文献记录。返回 (records, load_log)。"""
    records, load_log = [], []
    for f in list_material_files(input_dir):
        base = os.path.basename(f["path"])
        if base in skip:
            load_log.append({"file": f["rel"], "action": "skip_meta", "records": 0})
            continue
        ext = base.rsplit(".", 1)[-1].lower() if "." in base else ""
        n0 = len(records)
        try:
            if ext in ("json",):
                with io.open(f["path"], encoding="utf-8") as fh:
                    obj = json.load(fh)
                _collect_records(obj, f["rel"], "$", records)
            elif ext in ("jsonl", "ndjson"):
                with io.open(f["path"], encoding="utf-8") as fh:
                    for i, line in enumerate(fh):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            _collect_records(json.loads(line), f["rel"], "$.line%d" % (i + 1), records)
                        except json.JSONDecodeError:
                            load_log.append({"file": f["rel"], "line": i + 1, "action": "jsonl_parse_error"})
            elif ext in ("csv", "tsv"):
                delim = "\t" if ext == "tsv" else ","
                with io.open(f["path"], encoding="utf-8", errors="replace", newline="") as fh:
                    for i, row in enumerate(csv.DictReader(fh, delimiter=delim)):
                        if any(v for v in row.values() if v):
                            _collect_records({k: v for k, v in row.items()}, f["rel"], "$.row%d" % (i + 1), records)
            elif ext in ("txt", "md"):
                with io.open(f["path"], encoding="utf-8", errors="replace") as fh:
                    raw = fh.read()
                paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
                rec = {"source": {"file": f["rel"], "field": "$.paragraphs"},
                       "fields": {}, "raw": None,
                       "text_parts": [("P%03d" % (i + 1), p) for i, p in enumerate(paras)],
                       "text": raw}
                records.append(rec)
            else:
                load_log.append({"file": f["rel"], "action": "unsupported_ext", "records": 0})
                continue
            load_log.append({"file": f["rel"], "action": "loaded", "records": len(records) - n0})
        except Exception as e:  # noqa: BLE001 — 降级不中断
            load_log.append({"file": f["rel"], "action": "load_error", "error": str(e)[:200]})
    # 分配 record_id + 归一字段
    for i, r in enumerate(records):
        r["record_id"] = "R%04d" % (i + 1)
        for k in ("title", "abstract", "authors", "year", "doi", "venue", "type",
                  "language", "id", "keywords", "references", "patent_number",
                  "classification", "legal_status", "date", "claims"):
            v = r["fields"].get(k)
            if isinstance(v, str) and v.strip() in ("", "None", "null"):
                r["fields"].pop(k, None)
        r["norm"] = {"title": norm_title(r["fields"].get("title", "")),
                     "doi": norm_doi(r["fields"].get("doi", "")),
                     "year": re.search(r"(19|20)\d{2}", str(r["fields"].get("year", "")) or "") and
                             re.search(r"(19|20)\d{2}", str(r["fields"].get("year", ""))).group(0) or None}
    return records, load_log

# ---------- Step 2: 术语扩展 ----------

def expand_terms(query, glossary=None):
    """query: str；glossary: {term: [同义/变体...]}。返回展开后的词组列表（每个元素=一组同义词）。"""
    groups = []
    if glossary:
        ql = norm_text(query)
        for term, variants in glossary.items():
            if norm_text(term) and norm_text(term) in ql:
                groups.append([term] + list(variants))
    base = [q for q in re.split(r"[;,/]| and | AND ", query) if q.strip()]
    for b in base:
        if norm_text(b):
            groups.append([b])
    if not groups:
        groups.append([query])
    return groups

# ---------- Step 3: BM25-lite 检索 ----------

class Index(object):
    def __init__(self, records):
        self.records = records
        self.tfs, self.dls = [], []
        for r in records:
            toks = tokenize(r.get("text", ""))
            self.tfs.append(Counter(toks))
            self.dls.append(len(toks))
        self.N = len(records)
        self.avgdl = (sum(self.dls) / self.N) if self.N else 0.0
        self.df = Counter()
        for tf in self.tfs:
            for t in tf:
                self.df[t] += 1

    def _idf(self, term):
        n = self.df.get(term, 0)
        return math.log((self.N - n + 0.5) / (n + 0.5) + 1.0) if self.N else 0.0

    def search(self, query, topk=20, field_boosts=None, min_score=0.0):
        """field_boosts: {canonical_field: weight}，title 等字段命中加权。"""
        field_boosts = field_boosts or {"title": 3.0, "keywords": 1.5, "patent_number": 3.0, "classification": 2.0}
        scores = defaultdict(float)
        matched = defaultdict(set)
        qtoks = set(tokenize(query))
        norm_query = norm_text(query)
        for i, r in enumerate(self.records):
            for t in qtoks:
                f = self.tfs[i].get(t, 0)
                if not f:
                    continue
                dl = self.dls[i] or 1
                s = self._idf(t) * (2.0 * f) / (f + 1.2 * (0.25 + 0.75 * dl / (self.avgdl or 1)))
                for canon, w in field_boosts.items():
                    fv = r.get("fields", {}).get(canon, "")
                    if fv and t in tokenize(fv):
                        s += self._idf(t) * w * 0.5
                if s > 0:
                    scores[i] += s
                    matched[i].add(t)
            # 短语直配（标题/文号等整串匹配）强加分
            for canon in ("title", "patent_number", "id", "doi"):
                fv = norm_text(r.get("fields", {}).get(canon, ""))
                if fv and norm_query and (norm_query in fv or fv in norm_query) and len(norm_query) > 3:
                    scores[i] += 8.0
                    matched[i].add(canon + ":phrase")
        ranked = sorted(((s, i) for i, s in scores.items() if s > min_score), reverse=True)[:topk]
        return ranked, matched

def relevance_basis(record, matched_terms):
    """从 record 原文里摘出命中词所在短句作为 relevance_basis（引用原文短句）。"""
    basis = []
    for jp, val in record.get("text_parts", [])[:80]:
        vnorm = norm_text(val)
        hit = [t for t in matched_terms if t and norm_text(t) and norm_text(t) in vnorm]
        if hit:
            snippet = val.strip().replace("\n", " ")[:160]
            basis.append({"field": jp, "quote": snippet, "hit_terms": sorted(set(hit))[:6]})
        if len(basis) >= 3:
            break
    return basis

# ---------- Step 4: 去重与合并 ----------

def dedupe_key(rec):
    doi = rec.get("norm", {}).get("doi")
    if doi:
        return "doi:" + doi
    t = rec.get("norm", {}).get("title", "")
    y = rec.get("norm", {}).get("year") or ""
    if t:
        return "title:" + t[:120] + "|" + str(y)
    pid = rec.get("fields", {}).get("id") or rec.get("fields", {}).get("patent_number")
    return "id:" + norm_text(pid)[:120] if pid else "raw:" + norm_text(rec.get("text", ""))[:120]

def title_similar(a, b, threshold=0.85):
    ta, tb = set(tokenize(a)), set(tokenize(b))
    if not ta or not tb:
        return False
    j = len(ta & tb) / float(len(ta | tb))
    return j >= threshold

def dedupe(records, extra_pairs=None):
    """精确键分桶 + 标题模糊二次归并。返回 groups: [{key, members, merge_basis}]。"""
    buckets = OrderedDict()
    for r in records:
        buckets.setdefault(dedupe_key(r), []).append(r)
    keys = list(buckets.keys())
    groups = []
    used = set()
    for i, k in enumerate(keys):
        if k in used:
            continue
        members = list(buckets[k])
        used.add(k)
        # 标题模糊归并（DOI 不同但标题近似且年份一致的也合并，保留证据）
        rep = members[0].get("norm", {}).get("title", "")
        yr = members[0].get("norm", {}).get("year")
        for j in range(i + 1, len(keys)):
            if keys[j] in used:
                continue
            o = buckets[keys[j]][0]
            onorm = o.get("norm", {})
            if rep and title_similar(rep, onorm.get("title", "")) and (yr == onorm.get("year") or not yr or not onorm.get("year")):
                members.extend(buckets[keys[j]])
                used.add(keys[j])
        basis = []
        if len(members) > 1:
            basis = [{"record_id": m["record_id"], "source": m["source"],
                      "matched_on": dedupe_key(m)} for m in members]
        groups.append({"key": k, "members": members, "merge_basis": basis})
    return groups

FIELD_PRIORITY = {"doi": 0, "title": 1, "authors": 2, "year": 3, "venue": 4, "abstract": 5,
                  "type": 6, "language": 7, "id": 8, "keywords": 9, "references": 10,
                  "patent_number": 1, "classification": 6, "legal_status": 8, "date": 5, "claims": 7}

def merge_group(group, source_priority=None):
    """组内合并为一条规范记录：字段级优先级 + 冲突保留。"""
    members = group["members"]
    prio = source_priority or []
    def rank(rec):
        f = rec["source"]["file"]
        for i, p in enumerate(prio):
            if p in f:
                return i
        return len(prio)
    merged = {"record_ids": [m["record_id"] for m in members],
              "sources": [m["source"] for m in members],
              "fields": {}, "field_sources": {}, "conflicts": {}}
    for canon in set(c for m in members for c in m.get("fields", {})):
        vals = [(m, m["fields"][canon]) for m in members if canon in m.get("fields", {})]
        if not vals:
            continue
        vals.sort(key=lambda mv: (rank(mv[0]), -len(str(mv[1]))))
        merged["fields"][canon] = vals[0][1]
        merged["field_sources"][canon] = vals[0][0]["source"]
        distinct = {str(v) for _m, v in vals}
        if len(distinct) > 1:
            merged["conflicts"][canon] = [{"value": v, "source": m["source"]} for m, v in vals]
    merged["norm"] = {"title": norm_title(merged["fields"].get("title", "")),
                      "doi": norm_doi(merged["fields"].get("doi", "")),
                      "year": merged["fields"].get("year")}
    return merged

# ---------- Step 5: 引文图（references 字段） ----------

def build_citation_graph(records):
    """返回 {seed_record_id: {"references": [target_record_id|raw_ref], ...}}。
    references 命中语料内其他记录时给 record_id，否则保留 raw 并标 not_in_corpus。"""
    index = {}
    for r in records:
        t = r.get("norm", {}).get("title", "")
        if t:
            index[t[:120]] = r
        d = r.get("norm", {}).get("doi")
        if d:
            index["doi:" + d] = r
    graph = {}
    for r in records:
        refs = r.get("fields", {}).get("references", "")
        if not refs:
            continue
        edges = []
        for part in re.split(r"[;\n]|\s{2,}", refs):
            part = part.strip()
            if len(part) < 4:
                continue
            target = None
            nd = norm_doi(part)
            if nd and ("doi:" + nd) in index:
                target = index["doi:" + nd]["record_id"]
            if target is None:
                nt = norm_title(part)
                if nt and nt[:120] in index:
                    target = index[nt[:120]]["record_id"]
            edges.append({"raw": part[:200], "target_record_id": target,
                          "in_corpus": target is not None})
        graph[r["record_id"]] = edges
    return graph

# ---------- Step 6: 覆盖率 ----------

def hit_match(target, records, strict_year=False):
    """命中判定：DOI 精确 → 标题+作者+年份近似。返回 (record_id|None, method)。"""
    tdoi = norm_doi(json.dumps(target, ensure_ascii=False)) if isinstance(target, dict) else norm_doi(str(target))
    ttitle = target.get("title", "") if isinstance(target, dict) else str(target)
    tyear = (target.get("year") or "") if isinstance(target, dict) else ""
    tauth = (target.get("authors") or "") if isinstance(target, dict) else ""
    if tdoi:
        for r in records:
            if r.get("norm", {}).get("doi") and r["norm"]["doi"] == tdoi:
                return r["record_id"], "doi_exact"
    ttn = norm_title(ttitle)
    for r in records:
        if ttn and title_similar(ttn, r.get("norm", {}).get("title", ""), 0.85):
            if strict_year and tyear and r.get("norm", {}).get("year") and str(tyear) != str(r["norm"]["year"]):
                continue
            if tauth:
                ta = set(norm_text(tauth).split())
                ra = set(norm_text(r.get("fields", {}).get("authors", "")).split())
                if ta and ra and not (ta & ra):
                    continue
            return r["record_id"], "title_fuzzy"
    return None, "miss"

def classify_miss(reason_evidence):
    """漏检归因：根据证据字符串归类为可操作原因码。"""
    ev = norm_text(reason_evidence)
    if "no_doi" in ev or "缺 doi" in ev:
        return "identifier_abnormal"
    if "year_out" in ev or "时间窗" in ev:
        return "time_window"
    if "field" in ev:
        return "field_restriction"
    if "synonym" in ev or "同义" in ev:
        return "synonym_gap"
    return "not_indexed"

# ---------- 工具 ----------

def write_json(path, obj):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)

def write_jsonl(path, rows):
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

def load_jsonl(path):
    rows = []
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def contract_check(result_path, case_json_path):
    """对照 case.json 的 output_contract 检查 result.json 字段覆盖。返回 (ok, missing)。"""
    with io.open(case_json_path, encoding="utf-8") as fh:
        case = json.load(fh)
    with io.open(result_path, encoding="utf-8") as fh:
        result = json.load(fh)
    contract = case.get("output_contract") or case.get("outputContract") or {}
    if isinstance(contract, dict) and not contract:
        contract_keys = []
    elif isinstance(contract, dict):
        contract_keys = list(contract.keys())
    elif isinstance(contract, list):
        contract_keys = [c.get("name") if isinstance(c, dict) else c for c in contract]
    else:
        contract_keys = []
    missing = []
    for k in contract_keys:
        if k == "case_id":
            if result.get("case_id") != case.get("case_id"):
                missing.append("case_id != case.json 值")
            continue
        if k not in result:
            missing.append(k)
    if result.get("case_id") != case.get("case_id"):
        missing.append("case_id 未原样保留")
    return (len(missing) == 0, missing)
