#!/usr/bin/env python3
"""Score each round-trip rewrite against its ASD-STE100 reference. Usage: score.py OUT_DIR

chrF: character 6-gram F-score (beta 2) of the rewrite against the reference, 0..100, as in Popovic (2015).
wordF1: F1 of the case-folded word multisets. Both are 100 for the reference itself and fall with each change.
"""
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills/ste/scripts"))
import ste  # noqa: E402


def ngrams(s: str, n: int) -> Counter:
    s = re.sub(r"\s+", " ", s.strip().lower())
    return Counter(s[i : i + n] for i in range(len(s) - n + 1))


def chrf(hyp: str, ref: str, order: int = 6, beta: float = 2.0) -> float:
    p = r = 0.0
    for n in range(1, order + 1):
        h, g = ngrams(hyp, n), ngrams(ref, n)
        match = sum((h & g).values())
        p += match / max(sum(h.values()), 1)
        r += match / max(sum(g.values()), 1)
    p, r = p / order, r / order
    return 0.0 if p + r == 0 else 100 * (1 + beta**2) * p * r / (beta**2 * p + r)


def word_f1(hyp: str, ref: str) -> float:
    h, g = Counter(re.findall(r"[\w'-]+", hyp.lower())), Counter(re.findall(r"[\w'-]+", ref.lower()))
    match = sum((h & g).values())
    if not match:
        return 0.0
    p, r = match / sum(h.values()), match / sum(g.values())
    return 100 * 2 * p * r / (p + r)


def main() -> None:
    out = Path(sys.argv[1])
    if not (Path(__file__).parent / "refs.jsonl").exists():
        sys.exit("error: no refs.jsonl, run `eval/faithful/extract.py` first")
    refs = {json.loads(l)["id"]: json.loads(l)["ste"] for l in open(Path(__file__).parent / "refs.jsonl")}
    dictionary = ste.load_dictionary()
    if dictionary is None:
        sys.exit("error: no dictionary, run `skills/ste/scripts/ste.py build` first")

    # Control: the reference against itself must score 100, a shuffled pairing must score far lower.
    assert all(abs(chrf(t, t) - 100) < 1e-9 and abs(word_f1(t, t) - 100) < 1e-9 for t in refs.values())
    ids = sorted(refs)
    shuffled = statistics.mean(chrf(refs[i], refs[ids[(k + 1) % len(ids)]]) for k, i in enumerate(ids))
    print(f"control: reference vs itself = 100.0 chrF; reference vs a different reference = {shuffled:.1f} chrF")

    rows, by_id = defaultdict(list), defaultdict(dict)  # by_id: arm -> reference id -> chrF
    for f in sorted(out.glob("*.*.json")):
        arm, i = f.name.rsplit(".", 2)[0], int(f.name.rsplit(".", 2)[1])
        d = json.loads(f.read_text())
        if d.get("is_error"):
            sys.exit(f"error: {f}: {d.get('result')}")
        text, ref = d["result"].strip(), refs[i]
        lint = len(ste.findings(text, dictionary))
        words = len(re.findall(r"[\w'-]+", text))
        rows[arm].append((chrf(text, ref), word_f1(text, ref), lint, words, d["usage"]["output_tokens"]))
        by_id[arm][i] = rows[arm][-1][0]

    print(f"\nn = {len(refs)} references\n")
    print("| arm | chrF (mean) | word F1 (mean) | lint findings /1e3 words | words (sum) | output tok (sum) |")
    print("|---|---|---|---|---|---|")
    for arm, r in sorted(rows.items(), key=lambda kv: -statistics.mean(x[0] for x in kv[1])):
        words = sum(x[3] for x in r)
        print(f"| {arm} | {statistics.mean(x[0] for x in r):.1f} | {statistics.mean(x[1] for x in r):.1f} | "
              f"{1e3 * sum(x[2] for x in r) / words:.1f} | {words} | {sum(x[4] for x in r)} |")


    print("\npaired chrF difference against base (mean +/- s.e. over the references both arms have):")
    for arm in sorted(a for a in by_id if a not in ("base", "plain")):
        d = [by_id[arm][i] - by_id["base"][i] for i in by_id[arm] if i in by_id["base"]]
        print(f"  {arm}: {statistics.mean(d):+.1f} +/- {statistics.stdev(d) / len(d) ** 0.5:.1f} (n = {len(d)})")


if __name__ == "__main__":
    main()
