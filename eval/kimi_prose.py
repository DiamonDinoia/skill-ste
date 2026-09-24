#!/usr/bin/env python3
"""Every prompt of eval/prompts.txt, REPS times, under each arm, through an OpenAI-compatible endpoint.
The arm file is the system prompt. Output: one table row per arm, rates per 1e3 words.

Usage: kimi_prose.py CACHE_DIR REPS ARM=FILE...   (ARM=- is the empty system prompt)
"""
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path[:0] = [str(here), str(here.parent / "skills/ste/scripts")]
import llm  # noqa: E402
import ste  # noqa: E402

cache, reps = Path(sys.argv[1]), int(sys.argv[2])
arms = {a.split("=", 1)[0]: ("" if a.split("=", 1)[1] == "-" else Path(a.split("=", 1)[1]).read_text())
        for a in sys.argv[3:]}
prompts = (here / "prompts.txt").read_text().splitlines()
dictionary = ste.load_dictionary()
if dictionary is None:
    sys.exit("error: no dictionary, run `skills/ste/scripts/ste.py build` first")

# rep r is a distinct request: the cache key includes it through the trailing marker
with ThreadPoolExecutor(12) as pool:
    jobs = {(a, p, r): pool.submit(llm.chat, s, p + "\n" * (r + 1), cache)
            for p in prompts for r in range(reps) for a, s in arms.items()}
    res = {k: f.result() for k, f in jobs.items()}

kinds = ["word", "passive", "person", "phrasal", "hedge", "long-sentence", "semicolon", "latin", "contraction"]
print(f"model {llm.MODEL}, {len(prompts)} prompts x {reps} reps per arm; the first arm is the system-token baseline\n")
print("| arm | system tok | output tok (median) | words/sentence | " + " | ".join(kinds) + " |")
print("|" + "---|" * (4 + len(kinds)))
first = next(iter(arms))
for a in arms:
    r = [res[(a, p, i)] for p in prompts for i in range(reps)]
    texts = [ste.strip_code(x["text"]) for x in r]
    words = sum(len(re.findall(r"[\w'-]+", t)) for t in texts)
    sentences = sum(len([s for s in ste.SENTENCE.findall(t) if re.search(r"\w", s)]) for t in texts)
    counts = {k: 0 for k in kinds}
    for x in r:
        for _, k, _ in ste.findings(x["text"], dictionary):
            counts[k] = counts.get(k, 0) + 1
    sys_tok = statistics.median(x["in"] - res[(first, p, i)]["in"] for (p, i), x in
                                zip([(p, i) for p in prompts for i in range(reps)], r))
    print(f"| {a} | {sys_tok:.0f} | {statistics.median(x['out'] for x in r):.0f} | {words / sentences:.1f} | "
          + " | ".join(f"{1e3 * counts[k] / words:.1f}" for k in kinds) + " |")
