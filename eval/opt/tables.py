#!/usr/bin/env python3
"""Render the README benchmark tables from a compare.py transcript, or check a README against them.

Usage: tables.py RESULT.json [--check README.md]
--check exits 1 when the README does not contain the rendered tables verbatim.
"""
import json
import sys
from pathlib import Path

SHORT = {"moonshotai/Kimi-K3": "Kimi-K3", "moonshotai/Kimi-K2.6": "Kimi-K2.6",
         "zai-org/GLM-5.3": "GLM-5.3", "mistralai/Mistral-Medium-3.5-128B": "Mistral-Medium-3.5"}


def render(t: dict) -> str:
    models = [SHORT.get(r["model"], r["model"]) for r in t["rows"]]
    lines = [f"| arm | findings /1e3 words, {' | '.join(models)} | sys tokens, {' | '.join(models)} |",
             "|---|" + "---|" * (2 * len(models))]
    for arm in ("cur", "cand"):
        label = {"cur": "previous body", "cand": "this skill"}[arm]
        rates = " | ".join(f"{r[arm + '_rate']:.1f}" for r in t["rows"])
        tok = " | ".join(f"{r[arm + '_tok']:.0f}" for r in t["rows"])
        lines.append(f"| {label} | {rates} | {tok} |")
    lines += ["", f"| arm | chrF vs STE reference, {' | '.join(models)} |", "|---|" + "---|" * len(models)]
    for arm in ("cur", "cand"):
        label = {"cur": "previous body", "cand": "this skill"}[arm]
        lines.append("| " + label + " | " + " | ".join(f"{r[arm + '_chrf']:.1f}" for r in t["rows"]) + " |")
    lines.append(f"Paired chrF s.e. per model: {' / '.join(str(r['chrf_se']) for r in t['rows'])}. "
                 f"Pooled findings gain: {t['pooled_gain']:.1%}; pooled chrF diff: {t['pooled_chrf_diff']:+.1f}.")
    return "\n".join(lines)


def main() -> int:
    t = json.loads(Path(sys.argv[1]).read_text())
    rendered = render({**t, "rows": [{**r, "chrf_se": round(r["chrf_se"], 1)} for r in t["rows"]]})
    if "--check" in sys.argv[2:]:
        if len(sys.argv) < 4:
            sys.exit("usage: tables.py RESULT.json --check README.md")
        readme = Path(sys.argv[3]).read_text()
        missing = [line for line in rendered.split("\n") if line and line not in readme]
        if missing:
            print("FAIL: README is missing these generated lines:")
            print("\n".join(missing))
            return 1
        print("PASS: README contains the transcript tables")
        return 0
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
