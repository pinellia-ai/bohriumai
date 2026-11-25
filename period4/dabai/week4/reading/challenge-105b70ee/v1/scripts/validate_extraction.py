#!/usr/bin/env python3
"""validate_extraction.py — 校验结构化抽取结果（105b70ee 用）。

用法:
  python3 validate_extraction.py --result result.json --fields target-fields.json \
      [--source-dir DIR | --source-json INDEX]
  python3 validate_extraction.py --selftest     # 内置合成示例自测

校验项:
  1) field_id 100% 覆盖、无多余
  2) status 枚举合法 (reported/not_reported/source_conflict/extraction_failed)
  3) reported 字段 quote 非空且能在来源文本中子串匹配
  4) value 与 quote 同现（value 的数字片段须出现在 quote 中）
"""
import argparse, json, os, re, sys

STATUSES = {"reported", "not_reported", "source_conflict", "extraction_failed"}


def collect_source_text(source_dir=None, source_json=None):
    texts = []
    if source_dir:
        for root, _dirs, files in os.walk(source_dir):
            for fn in files:
                p = os.path.join(root, fn)
                try:
                    with open(p, encoding="utf-8", errors="ignore") as f:
                        texts.append(f.read())
                except OSError:
                    pass
    if source_json:
        with open(source_json, encoding="utf-8") as f:
            idx = json.load(f)
        items = idx if isinstance(idx, list) else idx.get("sources", [])
        for it in items:
            t = it.get("text") or it.get("content") or ""
            if t:
                texts.append(t)
    return "\n".join(texts)


def numeric_fragments(value):
    """取 value 中的数字片段，用于与 quote 同现校验。"""
    return re.findall(r"\d+(?:\.\d+)?", str(value or ""))


def validate(result, fields, source_text):
    errors, warnings = [], []
    req = {f.get("field_id") for f in fields}
    got = {f.get("field_id") for f in result.get("fields", [])}
    missing, extra = req - got, got - req
    if missing:
        errors.append(f"字段缺失: {sorted(missing)}")
    if extra:
        errors.append(f"多余字段: {sorted(extra)}")
    for f in result.get("fields", []):
        fid = f.get("field_id", "?")
        st = f.get("status")
        if st not in STATUSES:
            errors.append(f"{fid}: 非法 status '{st}'")
            continue
        if st == "reported":
            q = f.get("quote") or ""
            if not q:
                errors.append(f"{fid}: reported 但 quote 为空")
            elif source_text and q not in source_text:
                errors.append(f"{fid}: quote 无法在来源文本中子串匹配")
            for num in numeric_fragments(f.get("value")):
                if q and num not in q:
                    warnings.append(f"{fid}: 数值片段 {num} 未出现在 quote 中")
        if st == "source_conflict" and not f.get("conflicts"):
            errors.append(f"{fid}: source_conflict 但 conflicts 为空")
        if st in ("not_reported", "extraction_failed") and not f.get("notes"):
            warnings.append(f"{fid}: {st} 建议在 notes 说明检索/失败原因")
    return errors, warnings


def selftest():
    source = ("p12: The Fe-modified biochar achieved a removal efficiency of "
              "94.2 ± 1.8% under pH 7. p13: The surface area was 210 m2/g.")
    fields = [{"field_id": "removal_efficiency"}, {"field_id": "surface_area"},
              {"field_id": "bandgap"}]
    result = {"case_id": "demo", "status": "success", "fields": [
        {"field_id": "removal_efficiency", "status": "reported", "value": "94.2 ± 1.8",
         "quote": "achieved a removal efficiency of 94.2 ± 1.8% under pH 7",
         "paragraph_id": "p12", "conflicts": [], "notes": ""},
        {"field_id": "surface_area", "status": "reported", "value": "210",
         "units": "m2/g", "quote": "The surface area was 210 m2/g.",
         "paragraph_id": "p13", "conflicts": [], "notes": ""},
        {"field_id": "bandgap", "status": "not_reported", "value": None,
         "quote": None, "paragraph_id": None, "conflicts": [],
         "notes": "检索正文/表格/图注/补充材料均未报告带隙"}]}
    errs, warns = validate(result, fields, source)
    print(f"selftest: errors={errs} warnings={warns}")
    return not errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result"); ap.add_argument("--fields")
    ap.add_argument("--source-dir"); ap.add_argument("--source-json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if not (a.result and a.fields):
        ap.error("--result 与 --fields 必填（或用 --selftest）")
    with open(a.result, encoding="utf-8") as f:
        result = json.load(f)
    with open(a.fields, encoding="utf-8") as f:
        fields = json.load(f)
    if isinstance(fields, dict):
        fields = fields.get("fields", fields.get("target_fields", []))
    src = collect_source_text(a.source_dir, a.source_json)
    errs, warns = validate(result, fields, src)
    for e in errs:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    print(f"共 {len(result.get('fields', []))} 字段, {len(errs)} 错误, {len(warns)} 警告")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
