Use only STE-approved words: "make sure", "obey", "do", "get", "use". Do not replace them with unapproved synonyms such as "verify", "perform", "obtain", "utilize". Write all prose (explanations, comments, docs, commit messages, PR text) in ASD-STE100 Simplified Technical English. Code, math, logs and identifiers stay verbatim. The code, the data or the machine is the subject, never "I", "we" or "you". Use the term of art of the field.
Active voice: name the actor. One instruction per sentence.

On request, check a text with `python3 scripts/ste.py lint FILE` (path relative to this skill). It lists each violation with the approved alternatives. Run `python3 scripts/ste.py build` once first: it downloads the official ASD-STE100 PDF and builds the dictionary.
Maximum 20 words for each instruction and 25 words for each description sentence.
