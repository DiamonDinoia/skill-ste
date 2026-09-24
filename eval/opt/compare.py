#!/usr/bin/env python3
"""Compare a candidate ste skill body against the current one, on gateway models.

Prose phase: every prompt of eval/prompts.txt, REPS times, for arms base/cur/cand on each model.
  Per arm: lint findings per 1e3 words (ste.py findings, total and per kind), word counts, and
  system tokens (prompt tokens - the base arm; the per-(prompt,rep) pairing cancels the newline
  rep markers).
Faithful phase: the 31 ASD-STE100 references, each rewritten to an informal note on the model, then
  back to STE under each arm, exactly as eval/faithful/kimi.py does. chrF of each rewrite against
  its reference (catches the paraphrase regression that long rule lists cause).

Acceptance (exit 1 on any failure):
  findings:  cand rate < cur rate on every model; pooled gain >= GAIN_REQ (pooled = words-weighted
             over models, so a small-denominator model cannot dominate)
  volume:    cand words >= 0.7 x cur words on every model, and cand >= 0.5 x cur for every single
             text (a genre shift or a terse-fragment trick must not buy the rate)
  faith:     cand chrF >= cur chrF - CHRF_MODEL on every model, pooled diff >= -CHRF_POOLED
  tokens:    cand system tokens <= cur on every model, or <= 2x cur when pooled gain >= PAID_GAIN
             (tokens cost, so they must buy a measured advantage)
Tie class: a candidate also passes with findings per model <= TIE_BAND x cur and pooled >= -1% when
  it buys >= 10% token savings on every model. Equal compliance at materially lower context counts;
  the tournaments below showed the current body already at the local findings floor.

--gate runs the tournament gate instead: Kimi-K3 only, exit 0 when cand_rate < cur_rate and
cand chrF >= cur chrF - 1.0. Transcripts are written to the out dir: <name>.json on PASS,
<name>-fail.json otherwise, so a failing run can never pose as the provenance of a README table.

Usage: compare.py CAND.md [--cur FILE] [--reps N] [--models a,b,...] [--cache DIR] [--out DIR] [--gate]
"""
import argparse
import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
sys.path[:0] = [str(root / "eval"), str(root / "eval/faithful"), str(root / "skills/ste/scripts")]
import llm  # noqa: E402
import ste  # noqa: E402
from score import chrf  # noqa: E402

MODELS = ["moonshotai/Kimi-K3", "mistralai/Mistral-Medium-3.5-128B"]
# Quarantined 2026-09-24, probes with evidence inline:
#   moonshotai/Kimi-K2.6: HTTP 500 on every request (backend worker workergpu305 down).
#   zai-org/GLM-5.3: reasons past its token budget on real prompts and returns null content,
#     6 retries at 6000 max_tokens do not cure it (probe: 13e3 chars of hidden reasoning for a
#     230-word answer at think-disabled). Re-probe both before final acceptance.
QUARANTINED = ["moonshotai/Kimi-K2.6", "zai-org/GLM-5.3"]
GAIN_REQ, PAID_GAIN, VOLUME_FLOOR, TEXT_FLOOR, CHRF_MODEL, CHRF_POOLED = 0.05, 0.10, 0.7, 0.5, 2.0, 1.0
TIE_BAND, TIE_POOLED, TIE_SAVINGS = 1.03, -0.01, 0.9
TO_PLAIN = ("Rewrite this technical text the way a typical engineer writes an informal note or email: natural "
            "wording, contractions, phrasal verbs, passive voice where it is natural, longer sentences. Keep every "
            "fact, number and identifier. Output only the rewritten text.\n\n")
TO_STE = ("Rewrite this text in Simplified Technical English. Keep every fact, number and identifier. "
          "Output only the rewritten text.\n\n")
KINDS = ["word", "passive", "person", "phrasal", "hedge", "long-sentence", "semicolon", "latin", "contraction"]


def gen(arm_users: dict, cache: Path) -> dict:
    """arm_users maps arm -> (system, [users]). Return {(arm, i): {text, in, out}};
    identical (system, user) pairs share one call, so aliased arms see identical texts."""
    owners = {}  # (system, user) -> [(arm, i)]
    for a, (s, users) in arm_users.items():
        for i, u in enumerate(users):
            owners.setdefault((s, u), []).append((a, i))
    with ThreadPoolExecutor(12) as pool:
        jobs = {su: pool.submit(llm.chat, su[0], su[1], cache) for su in owners}
        res = {}
        for su, f in jobs.items():
            for k in owners[su]:
                res[k] = f.result()
        return res


def rate(texts: list[str], dictionary) -> tuple[dict[str, int], int, list[int]]:
    """Per-kind findings counts, total words, and per-text word counts."""
    wc = [len(re.findall(r"[\w'-]+", ste.strip_code(t))) for t in texts]
    counts = dict.fromkeys(KINDS, 0)
    for t in texts:
        for _, k, _ in ste.findings(t, dictionary):
            counts[k] = counts.get(k, 0) + 1
    return counts, sum(wc), wc


def prose_phase(models, arms, prompts, reps, cache, dictionary):
    """{(model, arm): (counts, words, sys-token delta, per-text word counts)}."""
    out = {}
    for m in models:
        llm.MODEL = m
        arm_users = {a: (s, [p + "\n" * (r + 1) for p in prompts for r in range(reps)])
                     for a, s in arms.items()}
        res = gen(arm_users, cache)
        for a in arms:
            rs = [res[(a, i)] for i in range(len(prompts) * reps)]
            counts, words, wc = rate([x["text"] for x in rs], dictionary)
            tok = (statistics.median(x["in"] - res[("base", i)]["in"]
                                     for i, x in enumerate(rs))) if a != "base" else 0
            out[(m, a)] = (counts, words, tok, wc)
    return out


def faith_phase(models, arms, refs, cache):
    """{(model, arm): [chrF per reference]}; positive control: a reference scores 100 vs itself.
    The base arm is skipped: nothing is measured against it, so it would be dead compute."""
    control = statistics.mean(chrf(r, r) for r in refs)
    if abs(control - 100.0) > 1e-9:
        sys.exit("control failed: chrF does not tell a text from itself")
    arms = {a: s for a, s in arms.items() if a != "base"}
    out = {}
    for m in models:
        llm.MODEL = m
        with ThreadPoolExecutor(12) as pool:
            plain = list(pool.map(lambda r: llm.chat("", TO_PLAIN + r, cache)["text"], refs))
        arm_users = {a: (s, [TO_STE + p for p in plain]) for a, s in arms.items()}
        res = gen(arm_users, cache)
        for a in arms:
            out[(m, a)] = [chrf(res[(a, i)]["text"], refs[i]) for i in range(len(refs))]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cand")
    ap.add_argument("--cur", default=str(here / "cur.md"))
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--prompts", type=int, default=12, help="first N prompts of eval/prompts.txt")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--cache", default=str(here / "cache"))
    ap.add_argument("--out", default=str(here / "results"))
    ap.add_argument("--name", default=None, help="candidate name for the transcript, default: file stem")
    ap.add_argument("--gate", action="store_true",
                    help="tournament gate: Kimi-K3 only, pass = cand < cur findings and chrF >= cur - 1.0")
    args = ap.parse_args()
    if args.gate:
        args.models = "moonshotai/Kimi-K3"

    models, cache, out = args.models.split(","), Path(args.cache), Path(args.out)
    all_prompts = (root / "eval/prompts.txt").read_text().splitlines()
    if len(all_prompts) < args.prompts or args.prompts < 1:
        sys.exit(f"error: asked for {args.prompts} prompts, prompts.txt has {len(all_prompts)}")
    prompts = all_prompts[: args.prompts]
    arms = {"base": "", "cur": Path(args.cur).read_text(), "cand": Path(args.cand).read_text()}
    refs = [json.loads(line)["ste"] for line in open(root / "eval/faithful/refs.jsonl")]
    if len(refs) != 31:
        sys.exit(f"error: expected 31 STE references, found {len(refs)}")
    dictionary = ste.load_dictionary()
    if dictionary is None:
        sys.exit("error: no dictionary, run `skills/ste/scripts/ste.py build` first")
    out.mkdir(parents=True, exist_ok=True)

    prose = prose_phase(models, arms, prompts, args.reps, cache, dictionary)
    faith = faith_phase(models, arms, refs, cache)

    fails, rows = [], []
    for m in models:
        cc_, cw, ct, cwc = prose[(m, "cur")]
        dc_, dw, dt, dwc = prose[(m, "cand")]
        cr, dr = 1e3 * sum(cc_.values()) / max(cw, 1), 1e3 * sum(dc_.values()) / max(dw, 1)
        c_chrf, d_chrf = faith[(m, "cur")], faith[(m, "cand")]
        se = statistics.stdev([a - b for a, b in zip(d_chrf, c_chrf)]) / len(d_chrf) ** 0.5
        rows.append({"model": m, "cur_rate": cr, "cand_rate": dr, "cur_tok": ct, "cand_tok": dt,
                     "cur_words": cw, "cand_words": dw, "cur_wc": cwc, "cand_wc": dwc,
                     "cur_chrf": statistics.mean(c_chrf), "cand_chrf": statistics.mean(d_chrf),
                     "chrf_se": se, "cur_kinds": cc_, "cand_kinds": dc_})
    pooled_cr = sum(r["cur_kinds"][k] for r in rows for k in KINDS) / sum(r["cur_words"] for r in rows)
    pooled_dr = sum(r["cand_kinds"][k] for r in rows for k in KINDS) / sum(r["cand_words"] for r in rows)
    gain = 1 - pooled_dr / pooled_cr if pooled_cr else 0.0
    # Class first: strict = findings fall on every model; tie = no model worsens beyond TIE_BAND,
    # pooled no worse than TIE_POOLED, cand buys TIE_SAVINGS tokens on every model. The findings
    # rule below follows the class. chrF, volume and the 2x token cap apply to both classes.
    cls = "strict"
    if gain < GAIN_REQ and all(r["cand_rate"] <= TIE_BAND * r["cur_rate"] for r in rows) \
            and gain >= TIE_POOLED and all(r["cand_tok"] <= TIE_SAVINGS * r["cur_tok"] for r in rows):
        cls = "tie"
    for r in rows:
        if cls == "strict" and r["cand_rate"] >= r["cur_rate"]:
            fails.append(f"{r['model']}: findings {r['cand_rate']:.1f} !< cur {r['cur_rate']:.1f}")
        if cls == "tie" and r["cand_rate"] > TIE_BAND * r["cur_rate"]:
            fails.append(f"{r['model']}: findings {r['cand_rate']:.1f} > {TIE_BAND} x cur {r['cur_rate']:.1f}")
        if r["cand_words"] < VOLUME_FLOOR * r["cur_words"]:
            fails.append(f"{r['model']}: cand words {r['cand_words']} < {VOLUME_FLOOR} x cur "
                         f"{r['cur_words']} (genre shift)")
        if any(d < TEXT_FLOOR * c for c, d in zip(r["cur_wc"], r["cand_wc"])):
            fails.append(f"{r['model']}: a cand text is < {TEXT_FLOOR} x the matching cur text "
                         "(terse fragments)")
        if r["cand_chrf"] < r["cur_chrf"] - CHRF_MODEL:
            fails.append(f"{r['model']}: chrF {r['cand_chrf']:.1f} < cur {r['cur_chrf']:.2f} - {CHRF_MODEL}")
        if r["cand_tok"] > 2 * r["cur_tok"]:
            fails.append(f"{r['model']}: {r['cand_tok']:.0f} system tokens > 2x cur {r['cur_tok']:.0f}")
    pd_ = statistics.mean(r["cand_chrf"] - r["cur_chrf"] for r in rows)
    if pd_ < -CHRF_POOLED:
        fails.append(f"pooled chrF diff {pd_:+.1f} < -{CHRF_POOLED}")
    if cls == "strict" and gain < GAIN_REQ:
        fails.append(f"pooled findings gain {gain:.1%} < {GAIN_REQ:.0%} and no tie-class win")
    if cls == "strict" and any(r["cand_tok"] > r["cur_tok"] for r in rows) and gain < PAID_GAIN:
        fails.append(f"pooled gain {gain:.1%} < {PAID_GAIN:.0%} with tokens over cur")
    if args.gate:  # tournament gate: findings strictly down, chrF no more than 1.0 down, Kimi-K3
        r = rows[0]
        fails = (["findings did not fall"] if r["cand_rate"] >= r["cur_rate"] else []) + \
                ([f"chrF {r['cand_chrf']:.1f} < cur {r['cur_chrf']:.1f} - 1.0"]
                 if r["cand_chrf"] < r["cur_chrf"] - 1.0 else [])
        name = args.name or Path(args.cand).stem
        (out / (f"{name}.json" if not fails else f"{name}-fail.json")).write_text(json.dumps({
            "candidate": name, "gate": True, "models": models, "reps": args.reps,
            "prompts": args.prompts, "pooled_gain": gain, "pooled_chrf_diff": pd_, "rows": rows}, indent=1))
        print(f"gate: K3 findings {r['cur_rate']:.1f} -> {r['cand_rate']:.1f} "
              f"({100 * (r['cur_rate'] - r['cand_rate']) / r['cur_rate']:+.1f}%), "
              f"chrF {r['cur_chrf']:.1f} -> {r['cand_chrf']:.1f}, tok {r['cur_tok']:.0f} -> {r['cand_tok']:.0f}")
        print("gate: PASS" if not fails else "gate: FAIL: " + "; ".join(fails))
        return 0 if not fails else 1

    name = args.name or Path(args.cand).stem
    # A FAIL writes <name>-fail.json: it can never be taken for the provenance of a README table.
    dest = out / (f"{name}.json" if not fails else f"{name}-fail.json")
    dest.write_text(json.dumps({
        "candidate": name, "class": cls, "models": models, "reps": args.reps, "prompts": args.prompts,
        "pooled_gain": gain, "pooled_chrf_diff": pd_, "rows": rows}, indent=1))
    print(f"{'model':38s} {'cur /1e3':>8s} {'cand /1e3':>9s} {'gain':>6s} {'tok c/c':>9s} {'chrF c/c':>12s} {'words c/c':>10s}")
    for r in rows:
        print(f"{r['model']:38s} {r['cur_rate']:8.1f} {r['cand_rate']:9.1f} "
              f"{100 * (r['cur_rate'] - r['cand_rate']) / r['cur_rate']:5.1f}% "
              f"{r['cur_tok']:4.0f}/{r['cand_tok']:<4.0f} {r['cur_chrf']:5.1f} {r['cand_chrf']:5.1f}±{r['chrf_se']:.1f} "
              f"{r['cur_words']:5d}/{r['cand_words']:<5d}")
    print(f"pooled: gain {gain:.1%}, chrF diff {pd_:+.1f}, transcript: {dest}")
    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    print(f"PASS ({cls})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
