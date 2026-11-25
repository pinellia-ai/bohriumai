#!/usr/bin/env python3
"""validate_itemcard.py — 校验题卡 JSONL 的 10 个必填字段与取值枚举。
用法: python3 validate_itemcard.py items.jsonl
退出码: 0=全部通过; 1=有校验错误; 2=用法/文件错误。
"""
import json
import sys

REQUIRED = ["item_id", "task_type", "input_type", "difficulty", "prompt",
            "input_material_ref", "reference_answer", "scoring_rule",
            "failure_modes", "data_license"]
TASK_TYPES = {"qa", "extraction", "verification", "parsing"}
INPUT_TYPES = {"plaintext", "table_text", "paragraph_numbered", "pdf_text", "figure_caption"}
DIFFS = {"easy", "medium", "hard"}
RULES = {"exact", "fields", "numeric_tol", "verdict", "manual_only"}


def main(path):
    errors = []
    cells = set()
    items = []
    try:
        with open(path, encoding="utf-8") as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    it = json.loads(line)
                except json.JSONDecodeError as e:
                    errors.append(f"L{ln}: JSON 解析失败: {e}")
                    continue
                items.append(it)
                for k in REQUIRED:
                    if k not in it or it[k] in (None, "", []):
                        errors.append(f"L{ln}: 缺必填字段 {k}")
                if it.get("task_type") not in TASK_TYPES:
                    errors.append(f"L{ln}: task_type 非法: {it.get('task_type')}")
                if it.get("input_type") not in INPUT_TYPES:
                    errors.append(f"L{ln}: input_type 非法: {it.get('input_type')}")
                if it.get("difficulty") not in DIFFS:
                    errors.append(f"L{ln}: difficulty 非法: {it.get('difficulty')}")
                if it.get("scoring_rule") not in RULES:
                    errors.append(f"L{ln}: scoring_rule 非法: {it.get('scoring_rule')}")
                if not isinstance(it.get("failure_modes"), list) or not it.get("failure_modes"):
                    errors.append(f"L{ln}: failure_modes 必须是非空列表")
                ra = it.get("reference_answer")
                if it.get("scoring_rule") != "manual_only":
                    if not isinstance(ra, dict) or "value" not in ra:
                        errors.append(f"L{ln}: reference_answer 需为含 value 的对象")
                if isinstance(ra, dict):
                    if not ra.get("locators"):
                        errors.append(f"L{ln}: reference_answer.locators 缺失（无法回查原文）")
                cells.add((it.get("input_type"), it.get("difficulty")))
    except FileNotFoundError:
        print(f"ERROR: 文件不存在: {path}")
        return 2

    ids = [it.get("item_id") for it in items]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errors.append(f"item_id 重复: {sorted(dup)}")

    # 矩阵覆盖：input_type x difficulty 组合数
    filled = len(cells)
    print(f"items={len(items)} matrix_cells={filled}")
    if len(items) < 1:
        errors.append("题数 <1")
    for e in errors:
        print("FAIL:", e)
    print("RESULT:", "PASS" if not errors else "FAIL")
    return 0 if not errors else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
