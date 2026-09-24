#!/usr/bin/env python3
"""Rebuild refs.jsonl, the STE example texts of ASD-STE100 Part 1, from the PDF and refs.lock.
The texts are (c) ASD and are not in the repository. Each refs.lock line selects one extracted
candidate by hash and keeps its first N words.
Usage: extract.py [PDF]   (default: the PDF that `ste.py build` downloads)"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[1] / "skills/ste/scripts"))
import ste  # noqa: E402

pdf = sys.argv[1] if len(sys.argv) > 1 else str(ste.CACHE / "ASD-STE100_ISSUE9.pdf")
lines = subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True, capture_output=True, text=True).stdout.split("\n")
end = next(i for i, l in enumerate(lines) if l.startswith("abaft (prep)"))  # Part 2 starts here
furniture = re.compile(r"^\s*(Issue 9|Page \d|2025-01-15|ASD-STE100|Part 1 - Writing rules|\d-\d-\d+)\s*$")
refs, cur = [], None
for l in lines[:end]:
    s = l.strip()
    m = re.match(r"^(Non-STE|STE):\s*(.*)$", s)
    if m:
        if cur: refs.append(cur)
        cur = {"kind": m.group(1), "text": m.group(2)}
        continue
    if cur is None: continue
    if not s or furniture.match(l) or re.match(r"^(Rule \d|Example|Note|Help|Section|Refer|WRITE|Do not|In STE)", s):
        refs.append(cur); cur = None; continue
    cur["text"] += " " + s
if cur: refs.append(cur)
# The spec's word-count notes, "(10 words)", are not part of the example.
candidates = {}
for r in refs:
    t = re.sub(r"\s+", " ", re.sub(r"\(\d+ words?\)", "", r["text"])).strip()
    if r["kind"] == "STE":
        candidates[hashlib.sha256(t.encode()).hexdigest()[:16]] = t
out = []
for line in open(here / "refs.lock"):
    if line.startswith("#"): continue
    i, h, n = line.split()
    if h not in candidates:
        sys.exit(f"error: refs.lock id {i}: no candidate with hash {h}, the PDF differs from Issue 9")
    out.append(json.dumps({"id": int(i), "ste": " ".join(candidates[h].split()[: int(n)])}) + "\n")
(here / "refs.jsonl").write_text("".join(out))
print(f"{here / 'refs.jsonl'}: {len(out)} references")
