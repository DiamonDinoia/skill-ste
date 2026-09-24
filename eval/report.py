#!/usr/bin/env python3
"""Reduce the eval/run.sh output to one table per arm. Usage: eval/report.py OUT_DIR"""
import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills/ste/scripts"))
import ste  # noqa: E402

out = Path(sys.argv[1])
dictionary = ste.load_dictionary()
if dictionary is None:
    sys.exit("error: no dictionary, run `skills/ste/scripts/ste.py build` first")

rows = defaultdict(list)
for f in sorted(out.glob("*.json")):
    arm = f.name.split(".")[0]
    d = json.loads(f.read_text())
    if d.get("is_error"):
        sys.exit(f"error: {f}: {d.get('result')}")
    u = d["usage"]
    text = d["result"]
    counts = defaultdict(int)
    for _, kind, _ in ste.findings(text, dictionary):
        counts[kind] += 1
    rows[arm].append({
        "in": u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"],
        "out": u["output_tokens"], "turns": d["num_turns"], "cost": d["total_cost_usd"],
        "words": len(re.findall(r"[\w'-]+", ste.strip_code(text))), **counts})

kinds = ["word", "passive", "person", "phrasal", "hedge", "long-sentence", "semicolon", "latin", "contraction", "emdash"]
print(f"n per arm: {', '.join(f'{a}={len(r)}' for a, r in sorted(rows.items()))}; dictionary: {ste.DICT}\n")
print("| arm | input tok (median) | output tok (median) | output tok (sum) | cost USD (sum) | turns (mean) | words (sum) | "
      + " | ".join(f"{k} /1e3 words" for k in kinds) + " |")
print("|" + "---|" * (7 + len(kinds)))
for arm in ("base", "full", "skill"):
    r = rows[arm]
    words = sum(x["words"] for x in r)
    rate = [f"{1e3 * sum(x.get(k, 0) for x in r) / words:.1f}" for k in kinds]
    print(f"| {arm} | {statistics.median(x['in'] for x in r):.0f} | {statistics.median(x['out'] for x in r):.0f} | "
          f"{sum(x['out'] for x in r)} | {sum(x['cost'] for x in r):.2f} | {statistics.mean(x['turns'] for x in r):.1f} | "
          f"{words} | " + " | ".join(rate) + " |")
