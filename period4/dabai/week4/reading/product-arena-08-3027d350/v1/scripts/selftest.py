#!/usr/bin/env python3
"""构造最小示意 result.json 实跑 validate_result.py（自测用）。"""
import json
import subprocess
import sys
import tempfile
import os

sample = {
    "case_id": "demo",
    "status": "partial",
    "document": {
        "metadata": {}, "sections": [],
        "paragraphs": [{"para_id": "P1", "page_no": 1, "reading_order": 0}],
        "tables": [{"table_id": "T1", "page_no": 1, "cells": []}],
        "figures": [],
    },
    "evidence_and_boundary": {"unresolved": [{"element": "x", "reason": "image_table"}]},
    "run_status": {"state": "partial"},
    "sources": [], "uncertainty_notes": [], "change_log": [],
}


def main():
    script = os.path.join(os.path.dirname(__file__), "validate_result.py")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(sample, f)
        tmp = f.name
    rc = subprocess.call([sys.executable, script, tmp])
    os.unlink(tmp)
    assert rc == 0, "selftest failed"
    print("selftest ok")


if __name__ == "__main__":
    main()
