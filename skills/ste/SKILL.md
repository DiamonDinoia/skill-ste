---
name: ste
description: "Use for technical writing, or when the user says \"STE\": write prose in ASD-STE100 Simplified Technical English."
license: MIT. The ASD-STE100 dictionary is built locally from the user's own copy of the spec.
---

Write all prose (explanations, comments, docs, commit messages, PR text) in ASD-STE100
Simplified Technical English. Code, math, logs and identifiers stay verbatim. The code, the
data or the machine is the subject, never "I", "we" or "you". Use approved words ("make
sure", "obey", "do", "get", "use"), not unapproved synonyms such as
"verify", "perform", "obtain", "utilize". Use the term of art of the field.
Active voice: name the actor. One instruction per sentence. Maximum 20 words for each
instruction, 25 for each description. Think in these simple words and short sentences too, not only for
the output. The full rule set is rules.md.

When the user grants broad edit rights on a file (for example "edit as much as you want"),
decide the cuts and the rewrites. Do not ask for each change. List the cuts and fixes in the
report. A question about an already-granted change wastes a delegation round.

Correct an obvious typo silently. A repeated word ("maintanance maintenance") or a misspelled approved word becomes the approved form once; flag the correction in the report.

On request, check a text with `python3 scripts/ste.py lint FILE` (path relative to this skill): it lists
each violation with the approved alternatives. Run `python3 scripts/ste.py build` once
first: it downloads the official ASD-STE100 PDF and builds the dictionary. After one
correct run of `ste.py build` the dictionary stays at
~/.cache/ste/dictionary.tsv and lint runs offline. While that cache file is
there, a worker must not skip lint if the network is down.

A review or edit gate counts sentence length on the added lines of the diff, not on the whole file. A whole-file count fails a scoped brief on sentences that predate the change. Compare against the base diff or a pre-edit copy and require zero added sentences over the limit. A bold lead-in (`**Label.**`) glues to the sentence it starts under a naive word counter; split that sentence or count the line by hand.
