#!/usr/bin/env python3
"""Round trip on the ASD-STE100 Part 1 STE examples (refs.jsonl), through an OpenAI-compatible endpoint:
  1. no instructions: rewrite each reference as an informal engineer's note (the plain text);
  2. each arm: rewrite the plain text back into STE, with the arm file as the system prompt.
Each rewrite is scored against the reference with chrF and word F1, plus lint findings per 1e3 words.

Usage: kimi.py CACHE_DIR ARM=FILE...   (ARM=- is the empty system prompt)
"""
import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path[:0] = [str(here), str(here.parent), str(here.parents[1] / "skills/ste/scripts")]
import llm  # noqa: E402
import ste  # noqa: E402
from score import chrf, word_f1  # noqa: E402

TO_PLAIN = ("Rewrite this technical text the way a typical engineer writes an informal note or email: natural "
            "wording, contractions, phrasal verbs, passive voice where it is natural, longer sentences. Keep every "
            "fact, number and identifier. Output only the rewritten text.\n\n")
TO_STE = ("Rewrite this text in Simplified Technical English. Keep every fact, number and identifier. "
          "Output only the rewritten text.\n\n")

cache = Path(sys.argv[1])
arms = {a.split("=", 1)[0]: ("" if a.split("=", 1)[1] == "-" else Path(a.split("=", 1)[1]).read_text())
        for a in sys.argv[2:]}  # the first arm is the baseline for the system-token column
if not (here / "refs.jsonl").exists():
    sys.exit("error: no refs.jsonl, run `eval/faithful/extract.py` first")
refs = [json.loads(l)["ste"] for l in open(here / "refs.jsonl")]
dictionary = ste.load_dictionary()
if dictionary is None:
    sys.exit("error: no dictionary, run `skills/ste/scripts/ste.py build` first")



def rewrite(arm: str, system: str, text: str) -> dict:
    """An arm named *-lint gets one revision pass with the `ste.py lint` findings, as the agent does."""
    r = llm.chat(system, TO_STE + text, cache)
    found = ste.findings(r["text"], dictionary)
    if not arm.endswith("-lint") or not found:
        return r
    report = "\n".join(f"{kind}: {what}" for _, kind, what in found)
    r2 = llm.chat(system, f"{TO_STE}{text}\n\nYour draft:\n{r['text']}\n\n`ste.py lint` findings:\n{report}\n\n"
                  "Fix each real violation. A technical noun of the field stays. Output only the final text.", cache)
    return {"text": r2["text"], "in": r["in"], "out": r["out"] + r2["out"]}


with ThreadPoolExecutor(12) as pool:
    plain = list(pool.map(lambda r: llm.chat("", TO_PLAIN + r, cache)["text"], refs))
    jobs = {(a, i): pool.submit(rewrite, a, s, p) for a, s in arms.items() for i, p in enumerate(plain)}
    res = {k: f.result() for k, f in jobs.items()}

ids = range(len(refs))
print(f"model {llm.MODEL}, n = {len(refs)} references")
print(f"control: reference vs itself = {statistics.mean(chrf(r, r) for r in refs):.1f} chrF; "
      f"reference vs the next reference = {statistics.mean(chrf(refs[i], refs[(i + 1) % len(refs)]) for i in ids):.1f}\n")


def row(name, texts, sys_tokens="", out_tokens=""):
    words = sum(len(re.findall(r"[\w'-]+", t)) for t in texts)
    lint = sum(len(ste.findings(t, dictionary)) for t in texts)
    c = [chrf(t, refs[i]) for i, t in enumerate(texts)]
    print(f"| {name} | {statistics.mean(c):.1f} | {statistics.stdev(c) / len(c) ** 0.5:.1f} | "
          f"{statistics.mean(word_f1(t, refs[i]) for i, t in enumerate(texts)):.1f} | {1e3 * lint / words:.1f} | "
          f"{words} | {sys_tokens} | {out_tokens} |")


print("| arm | chrF (mean) | chrF (s.e.) | word F1 (mean) | lint /1e3 words | words | system tok | output tok (sum) |")
print("|---|---|---|---|---|---|---|---|")
row("reference (STE)", refs)
row("plain", plain)
for a in arms:
    r = [res[(a, i)] for i in ids]
    base_in = [res[(next(iter(arms)), i)]["in"] for i in ids]
    row(a, [x["text"] for x in r], str(round(statistics.median(x["in"] - b for x, b in zip(r, base_in)))),
        str(sum(x["out"] for x in r)))

first = next(iter(arms))
print(f"\npaired chrF difference against {first} (mean +/- s.e. over the {len(refs)} references):")
for a in list(arms)[1:]:
    d = [chrf(res[(a, i)]["text"], refs[i]) - chrf(res[(first, i)]["text"], refs[i]) for i in ids]
    print(f"  {a}: {statistics.mean(d):+.1f} +/- {statistics.stdev(d) / len(d) ** 0.5:.1f}")
