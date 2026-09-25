# ste

**One reading per sentence.** A coding-agent skill: all prose in ASD-STE100 Simplified Technical English, the controlled
language of aerospace maintenance manuals, adapted to software.

## Before and after

Kimi-K3, one prompt, no tools:

> Explain to a junior developer what a data race is and how ThreadSanitizer finds one, in about 150 words.

<table>
<tr><th>Without the skill</th><th>With the skill</th></tr>
<tr><td valign="top">A data race happens when two threads access the same memory location at the same time, at least one of them is writing, and there's no synchronization (like a mutex) to order those accesses. The result is undefined behavior—your program might work fine a thousand times, then corrupt data or crash mysteriously.<br><br>ThreadSanitizer (TSan) detects these at runtime using dynamic analysis. It instruments your compiled code to track every memory access. For each memory location, TSan maintains "shadow memory" recording which threads recently read or wrote there. When a new access occurs, it checks: does this conflict with a previous access from a different thread? It determines "conflict" using happens-before relationships—if Thread A's write isn't ordered before Thread B's read via synchronization primitives (mutex locks, atomic operations), TSan flags a race. This catches bugs that code review and testing often miss because they depend on specific thread timing.</td><td valign="top">A data race is a bug in multithreaded code. It happens when two threads use the same memory location at the same time. At least one of these threads must write to the memory. The threads do not use locks to control access. This makes the program behavior unpredictable. <br><br>ThreadSanitizer finds these bugs during program execution. It monitors every memory access. It records which thread reads or writes to each location. It also records the synchronization events. It checks if two accesses to the same location can happen at the same time. If they can, and one is a write, it reports a race. This tool helps the developer find bugs that are hard to reproduce. The developer must fix the race to make the code safe.</td></tr>
</table>

## Results

The shipped body is the measured local optimum: an 8-candidate one-axis tournament on Kimi-K3 found no variant with
fewer lint findings; adding rule text or removing it both lose compliance.

| L | candidate | K3 findings /1e3 words, cur -> cand | gain | chrF, cur -> cand | system tok, cur -> cand |
|---|---|---|---|---|---|
| A | compress | 79.0 -> 79.1 | -0.1% | 80.9 -> 82.0 | 217 -> 173 |
| B | neglist | 79.0 -> 107.3 | -35.7% | 80.9 -> 81.0 | 217 -> 212 |
| C | table | 79.0 -> 95.0 | -20.2% | 80.9 -> 81.8 | 217 -> 228 |
| D | example | 79.0 -> 89.3 | -13.0% | 80.9 -> 81.8 | 217 -> 239 |
| E | order | 79.0 -> 80.1 | -1.4% | 80.9 -> 80.8 | 217 -> 216 |
| F | lintloop | 79.0 -> 113.8 | -44.1% | 80.9 -> 80.9 | 217 -> 234 |
| G | trimmed | 79.0 -> 103.6 | -31.1% | 80.9 -> 80.3 | 217 -> 291 |
| H | floor80 | 79.0 -> 94.4 | -19.4% | 80.9 -> 82.6 | 217 -> 93 |

88.7% of residual findings are unapproved-word class, dominated by terms of art the linter cannot verify.
The run quarantined `moonshotai/Kimi-K2.6` and `GLM-5.3`: K2.6 returned HTTP 500 on all requests, and GLM-5.3
reasoned past its token budget and returned null content. Full transcript: `eval/opt/results/tournament.md`.

## Lint

`ste.py lint` lists each violation with the approved alternatives:

```console
$ echo "We basically set up the buffer; it is handled by the loop, e.g. in foo()." | python3 skills/ste/scripts/ste.py lint
-:1: semicolon: ;
-:1: latin: e.g.
-:1: passive: is handled
-:1: person: We
-:1: hedge: basically
-:1: phrasal: set up
-:1: word: handled -> MOVE, TOUCH, USE, CAREFUL
ste lint: 7 findings, checked with dictionary ~/.cache/ste/dictionary.tsv
```

## Install

| Harness | Command |
|---|---|
| Claude Code | `claude plugin marketplace add DiamonDinoia/skill-ste && claude plugin install ste@ste --scope user` |
| Codex CLI | `codex plugin marketplace add DiamonDinoia/skill-ste`, then `codex plugin add ste@ste` |
| Gemini CLI | `gemini extensions install https://github.com/DiamonDinoia/skill-ste --consent` |
| by hand | `git clone https://github.com/DiamonDinoia/skill-ste && ln -s "$PWD/skill-ste/skills/ste" ~/.claude/skills/ste` |

The three harnesses with a native manifest carry one in this repository: `.claude-plugin/` for Claude Code, `.codex-plugin/` for Codex, and `gemini-extension.json` for Gemini CLI. Any other harness: install by hand (last row).

Claude Code: in `/plugin`, enable auto-update for the `ste` marketplace. `claude plugin disable ste@ste` stops the
skill. `claude plugin update ste@ste` pulls the new release.

The STE dictionary is copyright ASD and not in this repository. Build it once with
`python3 <installed skill directory>/scripts/ste.py build` (Python 3.9+, `pdftotext`). Without the dictionary,
`lint` checks only grammar and punctuation.

## Validation

`test/run.sh` builds a container with each harness, installs the skill with each mechanism and checks that each
harness finds it. A copy with an invalid skill name must fail on the name check. Commands:

```sh
test/run.sh                              # podman, or: test/run.sh docker
eval/run.sh OUT 1 && eval/report.py OUT  # Claude Code prose: no skill, full rule set, this skill
```

## License

MIT for this repository. ASD-STE100 is © ASD; `ste.py build` uses the user's own copy of the spec.
