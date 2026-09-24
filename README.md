# ste

**One reading per sentence.** An agent skill that makes coding agents write technical prose in Simplified
Technical English (ASD-STE100 Issue 9), the controlled language of aerospace maintenance manuals, adapted to
software.

## Before and after

Claude Opus 5.5 (`claude-opus-5-5`), one prompt from `eval/prompts.txt`, no tools, no edits:

> Explain to a junior developer what a data race is and how ThreadSanitizer finds one, in about 150 words.

<table>
<tr><th>Without the skill</th><th>With the skill</th></tr>
<tr><td valign="top">A data race occurs when two threads access the same memory location concurrently, at least one access is a write, and no synchronization (mutex, atomic, join) orders them. In C++ the result is undefined behaviour, not merely a stale value: the compiler may cache, reorder or tear the access, so the program can fail rarely and unreproducibly.<br><br>ThreadSanitizer (<code>-fsanitize=thread</code> in gcc and clang) instruments every load, store and synchronization call at compile time. Each thread carries a vector clock, a logical timestamp per thread. Lock, unlock, atomic and thread-create/join operations propagate these clocks, which builds the happens-before relation between events. For every 8 bytes of application memory, shadow memory records the recent accesses: thread, clock, size, read or write. On each new access TSan compares it against those records. If two accesses conflict and neither happens-before the other, it reports a race with both stack traces.<br><br>TSan detects races only on paths that actually execute, so test coverage bounds what it can find.</td><td valign="top">A data race is a defect in a multithreaded program. It occurs when two threads use the same memory location at the same time. At least one of the two threads writes to that location. No synchronization sets an order between the two operations. Examples of synchronization are a mutex, an atomic operation and a thread join.<br><br>In C and C++, a data race causes undefined behavior. The program can give a different result on each run. The compiler can also change the code in ways that break it.<br><br>ThreadSanitizer (TSan) is a tool in the compiler. Compile the program with <code>-fsanitize=thread</code>. The compiler then adds a check before each memory read and write. At run time, TSan records which thread used each location. It uses vector clocks to follow the happens-before order between threads. Two operations can have no happens-before order, and one of them can be a write. In that case, TSan reports a race and shows the two stack traces.<br><br>TSan finds only the races on code paths that the test runs.</td></tr>
</table>

## Results

Claude Opus 5.5, 11 prose prompts (`eval/run.sh OUT 1`, then `eval/report.py OUT`). Rates are
`ste.py lint` findings per 1e3 words. `full` is every ASD-STE100 rule restated for software, 2.9e3 tokens.

| arm | added context (tok) | output tok (sum) | words (sum) | unapproved words | passive | sentences > 25 words | semicolons |
|---|---|---|---|---|---|---|---|
| no skill | 0 | 15722 | 3626 | 95.7 | 9.4 | 2.8 | 4.4 |
| all rules (`full`) | 2935 | 25473 | 3755 | 70.6 | 2.1 | 0.5 | 0.0 |
| this skill | 229 | 10333 | 1979 | 57.1 | 2.0 | 0.0 | 0.0 |

The skill adds 229 tokens of context. Against no skill, it cuts output tokens by 34% and words by 45%. Its lint rates
are at or below those of the full rule set in every column of the table, with 8% of the added context.

### Faithfulness to real STE

The benchmark uses 31 STE example texts from ASD-STE100 Part 1. A model rewrites each example as an informal
note. Then each arm rewrites the note back into STE. chrF (character 6-gram F-score, 0 to 100) compares each
result with the original STE text. Two controls calibrate the scale: a text against itself scores 100.0, and a
text against a different example scores 22.5.

| arm | added context (Kimi tok) | chrF, Kimi-K3 | paired diff, Kimi-K3 | chrF, Opus 5.5 | paired diff, Opus 5.5 |
|---|---|---|---|---|---|
| informal note | | 70.7 | | 65.0 | |
| no skill | 0 | 80.3 | | 80.3 | |
| this skill | 217 | 78.8 | -1.5 +/- 1.8 | 78.7 | -2.0 +/- 1.4 |
| 450-word rule summary | 584 | 76.2 | -4.1 +/- 2.2 | 78.9 | -1.4 +/- 1.8 |
| all rules (`full`) | 2091 | 76.1 | -4.1 +/- 2.4 | 79.1 | -1.0 +/- 1.4 |

The rewrite request already says "Simplified Technical English", so the no-skill arm also knows the target.
Long rule lists make the model paraphrase into unapproved synonyms: "verify" for "make sure", "follow" for
"obey", "perform". Those synonyms move the text away from the original. A paired diff is the mean over the
references of (arm chrF - no-skill chrF), +/- one standard error. On Opus 5.5, every arm is within 1.5
standard errors of no skill. On Kimi-K3, the skill is within one standard error, and the two long rule sets
lose 4 chrF.

Kimi-K3 prose (12 prompts x 3 reps, `eval/kimi_prose.py`), findings per 1e3 words, no skill -> this skill:
unapproved words 115.1 -> 89.9, passive 5.5 -> 1.9, person 12.1 -> 2.8, contractions 3.3 -> 0.0. The median
output falls from 263 to 172 tokens.


## What the skill does

`skills/ste/SKILL.md` is about 130 words. It tells the agent to write all prose in ASD-STE100, keep code, math
and logs verbatim, use the code or the machine as the subject, and not paraphrase approved STE words into
unapproved synonyms. It also gives the active-voice rule and the 20-word and 25-word sentence limits. The
benchmarks above show that a longer rule list adds context and makes the result less faithful.

`skills/ste/rules.md` restates every ASD-STE100 writing rule for software, with the spec rule numbers. It is
not loaded into the context: `ste.py lint` prints its path, and the agent reads it when a rule is unclear.

`skills/ste/scripts/ste.py lint` checks a text against the rules and the STE dictionary. For each violation, it
prints the approved alternatives. The agent runs it on request.

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

The STE dictionary (875 approved and 1274 unapproved words) is copyright ASD and is not in this repository. Run
`python3 skills/ste/scripts/ste.py build` once. That command downloads the free official PDF from
[asd-ste100.org](https://www.asd-ste100.org/STE_downloads.html) and builds the dictionary in `~/.cache/ste`.
Without the dictionary, `lint` checks only the grammar and punctuation rules and says so.

## Install

| Harness | Command |
|---|---|
| Claude Code | `claude plugin marketplace add DiamonDinoia/ste-skill && claude plugin install ste@ste --scope user` |
| Codex CLI | `codex plugin marketplace add DiamonDinoia/ste-skill`, then install `ste` from `/plugins` |
| Gemini CLI | `gemini extensions install https://github.com/DiamonDinoia/ste-skill --consent` |
| opencode, Cursor, Copilot, Codex | `npx skills add DiamonDinoia/ste-skill --skill ste -g -y -a codex -a opencode -a cursor -a github-copilot` |
| any agent that `gh skill` supports | `gh skill install DiamonDinoia/ste-skill ste --agent claude-code --scope user` (`gh skill install --help` lists the agents) |
| any agent, by hand | `git clone https://github.com/DiamonDinoia/ste-skill && ln -s "$PWD/ste-skill/skills/ste" ~/.claude/skills/ste` |

`npx skills add` writes one copy to `~/.agents/skills/ste`, which Codex, opencode, Cursor and Copilot read.
opencode also reads `~/.claude/skills`. After the install, build the dictionary once:

```sh
python3 <installed skill directory>/scripts/ste.py build
```

The skill loads when a task asks for technical prose, or on request (`/ste` in Claude Code). To apply it to every
answer, add one line to `CLAUDE.md` or `AGENTS.md`: `Write all prose in STE (the ste skill).`

## Validation

`test/run.sh` builds a container with Claude Code, Codex, Gemini CLI, opencode and the `skills` CLI. In that
container, it installs the skill from this repository with the mechanism of each harness and checks that each
harness finds the skill. It also builds the dictionary from the official PDF and runs `lint`. Then it runs the
same checks on a copy with an invalid skill name. That run must fail, and on the name check.

```sh
test/run.sh            # podman, or: test/run.sh docker
```

Benchmarks:

```sh
awk 'n>=2; /^---$/{n++}' skills/ste/SKILL.md > skill.md   # the skill body, without the frontmatter
python3 eval/faithful/extract.py   # the 31 STE references: (c) ASD, rebuilt from the PDF and refs.lock
: > empty.md
eval/run.sh OUT 1 && eval/report.py OUT                    # Claude Code prose: no skill, full, skill
eval/faithful/run.sh FOUT base=empty.md skill=skill.md && eval/faithful/score.py FOUT
# any OpenAI-compatible endpoint: LLM_BASE_URL, LLM_API_KEY, LLM_MODEL; ARM=- is no system prompt
python3 eval/faithful/kimi.py CACHE base=- skill=skill.md full=skills/ste/rules.md
python3 eval/kimi_prose.py CACHE 3 base=- skill=skill.md full=skills/ste/rules.md
```

## License

MIT for this repository. ASD-STE100 is © ASD; `ste.py build` uses the user's own copy of the spec.
