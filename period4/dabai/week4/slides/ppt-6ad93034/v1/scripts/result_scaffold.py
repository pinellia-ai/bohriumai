#!/usr/bin/env python3
"""result_scaffold.py — 尽早落盘最小可用 result.json(断电/中断也有可评分产物)。

用法: python3 result_scaffold.py <case_id> <output_dir>
行为: 若 <output_dir>/result.json 已存在则原样保留(不覆盖已充实内容);
否则写入含 case_id/status=partial/空结构的最小骨架, 并 print 结果路径。
退出码: 0 成功; 2 参数缺失。
"""
import json
import os
import sys

SCHEMA = {
    "case_id": None,
    "status": "partial",          # ok | partial | failed
    "deliverables": {"source_pptx": None, "exported_pdf": None},
    "slides": [],
    "coverage": {"mainline": "partial", "page_structure": "partial",
                 "figure_refs": "partial", "narration": "partial",
                 "template": "partial", "export": "partial"},
    "version_log": [],
    "uncertainty": [],
    "gaps": [],
    "sources": []
}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"ok": False, "error": "usage: result_scaffold.py <case_id> <out_dir>"}))
        sys.exit(2)
    case_id, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "result.json")
    if os.path.isfile(path):
        print(json.dumps({"ok": True, "path": path, "action": "kept-existing"}))
        return
    data = dict(SCHEMA)
    data["case_id"] = case_id
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(json.dumps({"ok": True, "path": path, "action": "created"}))


if __name__ == "__main__":
    main()
