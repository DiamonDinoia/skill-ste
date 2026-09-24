# S2 tournament: ste skill body candidates

2026-09-24, marco@ws, `python3 eval/opt/compare.py eval/opt/candidates/<file> --gate --name <L>`,
Kimi-K3 only, 12 prompts x 2 reps, chrF over the 31 ASD-STE100 references. Baseline: the frozen
current body (`eval/opt/cur.md`, 129 words, 217 system tokens). Gate: cand findings < cur findings
and cand chrF >= cur chrF - 1.0. Transcripts: `eval/opt/results/<L>.json` (gitignored).

## Gate results

| L | candidate | K3 findings /1e3 words, cur -> cand | gain | chrF, cur -> cand | system tok, cur -> cand |
|---|---|---|---|---|---|
| A | compress    | 79.0 -> 79.1  | -0.1%  | 80.9 -> 82.0 | 217 -> 173 |
| B | neglist     | 79.0 -> 107.3 | -35.7% | 80.9 -> 81.0 | 217 -> 212 |
| C | table       | 79.0 -> 95.0  | -20.2% | 80.9 -> 81.8 | 217 -> 228 |
| D | example     | 79.0 -> 89.3  | -13.0% | 80.9 -> 81.8 | 217 -> 239 |
| E | order       | 79.0 -> 80.1  | -1.4%  | 80.9 -> 80.8 | 217 -> 216 |
| F | lintloop    | 79.0 -> 113.8 | -44.1% | 80.9 -> 80.9 | 217 -> 234 |
| G | trimmed     | 79.0 -> 103.6 | -31.1% | 80.9 -> 80.3 | 217 -> 291 |
| H | floor80     | 79.0 -> 94.4  | -19.4% | 80.9 -> 82.6 | 217 -> 93 |

All 8 FAIL: findings did not fall. chrF passed for every candidate (all >= cur - 1.0). Unapproved
words are 88.7% of the current findings (197/222). A and E, the two candidates that stay in the
current body's distribution, land at -0.1% and -1.4%: the current rate is the local floor. B, C,
D, G relist or re-table the banned words and add 29 to 116 word findings: the word list backfires.
F adds the lint-loop instruction and has the worst rate, +44%. H drops the word lists and rises
+19%. Every candidate volume is >= 0.89 x cur words: no rate moved because of truncation.

Gate validity: `bash eval/opt/controls.sh` passes. The gate rejects a body identical to the
baseline (`control_same`) and an empty body (`control_empty`).

## Full acceptance (finalists)

No candidate passed the gate, so there are no finalists. No full acceptance run
(Kimi-K3 / GLM-5.3 / Mistral-Medium-3.5-128B) was started: a candidate above the current findings
rate on Kimi-K3 cannot pass the acceptance findings criterion.

## Eyeball

No winner, so the winner backstop is not applicable. As provenance for the null result, two cached
B-prose outputs (slow-inner-loop prompt, data-race prompt) were read: both are complete prose of
the expected length, no fragments, no code dumps. The higher rates are a real style effect.

## Winner

None. Keep the current body (129 words, 217 system tokens). Its full text:

```
Write all prose (explanations, comments, docs, commit messages, PR text) in ASD-STE100 Simplified Technical English. Code, math, logs and identifiers stay verbatim. The code, the data or the machine is the subject, never "I", "we" or "you". Use only STE-approved words: "make sure", "obey", "do", "get", "use". Do not replace them with unapproved synonyms such as "verify", "perform", "obtain", "utilize". Use the term of art of the field.
Active voice: name the actor. One instruction per sentence. Maximum 20 words for each instruction and 25 words for each description sentence.

On request, check a text with `python3 scripts/ste.py lint FILE` (path relative to this skill). It lists each violation with the approved alternatives. Run `python3 scripts/ste.py build` once first: it downloads the official ASD-STE100 PDF and builds the dictionary.
```
