
# ASD-STE100 Issue 9 for software

Every writing rule of the spec, restated for technical prose about software. The numbers in brackets
are the spec rule numbers. Write every sentence so exactly one reading is possible. Code is unchanged.

## Programming deltas

These rules replace or extend the spec for software.

- Third person, scientific register. The code, the data or the machine is the subject, never "I", "we" or "you". Not "I added a fast path" / "we then normalize". Say "`dispatch()` takes the fast path" / "the kernel normalizes the input" instead.
- No narration of the work. State what the code is, not what somebody did to it.
- Identifiers verbatim in backticks. An identifier is a technical noun and is never inflected or paraphrased.
- No metaphor, no idiom, no hedging ("basically", "essentially", "sort of").
- Math and asm stay exact and are exempt from word limits. Quoted errors and logs are verbatim.

## Words [1]

- Use only approved dictionary words, technical nouns and technical verbs. [1.1]
- Use an approved word only as its part of speech. "TEST (n)" is approved, "test (v)" is not: write "do a test". [1.2]
- Use an approved word only with its approved meaning. "GET" means "to obtain", not "become", "go", "decrease" or "increase". [1.3]
- Use only the approved forms of verbs and adjectives, as listed in the dictionary. [1.4]
- A technical noun is a word from a technical noun category: names, parts, tools, data, units, algorithms, file types. An unapproved word is permitted only as a technical noun or part of one. [1.5, 1.6]
- Do not use a technical noun as a verb. Not "`malloc` the buffer". Say "allocate the buffer with `malloc`". [1.7]
- Use the technical noun of the field, the one the literature uses: "catastrophic cancellation", "spill", "aliasing", "gather". [1.8]
- If there is a choice, use the shortest technical noun that is easy to understand. [1.9]
- No slang, regional words or jargon as technical nouns: not "perf hit", "footgun", "yak shave". [1.10]
- One technical noun for one item. Not buffer/array/block for the same object. [1.11]
- A technical verb is a verb from a technical verb category: manufacturing, computing, mathematics (compile, link, vectorize, transpose, factorize). Do not use a technical verb as a noun. [1.12, 1.13]
- American English spelling. [1.14]

## Multi-word nouns [2]

- A noun cluster has a maximum of 3 words. Not "kernel batch dispatch table lookup". Say "lookup in the dispatch table for kernel batches". [2.1]
- If a technical noun has more than 3 words, write the full noun once. Then use a short form, or hyphenate the words that are one unit. [2.2]

## Verbs [3]

- Use only these verb forms: infinitive, imperative, simple present, simple past, simple future, and past participle as an adjective. [3.1, 3.2, 3.3]
- No complex verb constructions with auxiliaries: not "has been being computed", "would have returned". [3.4]
- Use the "-ing" form only in a technical noun ("loop unrolling") or as its modifier. Not "Freeing the pool releases...". Say "Free the pool. The free operation releases...". [3.5]
- Active voice. Passive voice only in a description where the agent is unknown. Not "the buffer is freed". Say "`free_pool()` frees the buffer". [3.6]
- Use a verb for an action, not a noun. Not "perform an allocation of". Say "allocate". [3.7]

## Sentences [4]

- Short, clear sentences. [4.1]
- Do not omit words and do not use contractions. Keep articles, prepositions and verbs. STE is not caveman. [4.2]
- Use a vertical list for complex text. [4.3]
- Connect related sentences with connecting words: "then", "thus", "but", "because", "if". [4.4]
- Use an article or a demonstrative adjective ("this", "these") before a noun. [4.5]

## Procedures: instructions [5]

- Maximum 20 words for each sentence. [5.1]
- One instruction for each sentence, except for actions that occur at the same time. [5.2]
- Instructions use the imperative. "Call `init()` first." Not "you should call" / "calling `init()` is needed". [5.3]
- A condition that the reader must know first goes first, followed by a comma. "If `n` is zero, return early." [5.4]
- A note gives information, not instructions. [5.5]
- When order matters, write the steps as a numbered list, one step for each item.

## Descriptions [6]

- Give information gradually: the general statement first, then the details. [6.1]
- Use key words and key phrases to give the text a logical structure. [6.2]
- Maximum 25 words for each sentence. [6.3]
- One topic for each paragraph, a maximum of 6 sentences for each paragraph. [6.4, 6.5, 6.6]
- A description does not use the imperative.

## Warnings [7]

- Identify the risk level with a signal word: "Warning" (data loss, corruption, wrong results) or "Caution" (damage that you can repair). [7.1]
- Start the warning with a clear command or condition. [7.2]
- Give the risk or the possible result. [7.3]
- Put the warning before the step it applies to, never after.

## Punctuation and word count [8]

- No semicolons. [8.1]
- Hyphens connect words that are directly related: "cache-line boundary". [8.2]
- Parentheses only for references, identifiers, abbreviations, singular/plural "(s)", short explanations, and alternatives. [8.3]
- For the word limits: a colon in a vertical list ends a sentence. Text in parentheses, a number with its unit, an abbreviation, an identifier, quoted text, a title and a hyphenated word each count as one word. [8.4-8.7]

## Writing practices [9]

- If a word-for-word replacement does not give an approved sentence, change the sentence construction. [9.1]
- Use each approved word only in its approved meaning, as the dictionary gives. [9.2]
- No phrasal verbs: not "set up", "look into", "carry out", "figure out". Say "configure", "examine", "do", "find". [9.3]
- Consistent terminology and wording in the full text. [9.4]
- Use "that" after verbs such as "make sure", "show", "recommend". "The test shows that the loop vectorizes." [GR-1]
- Read every sentence with "with" again, because "with" has 3 meanings. [GR-2]
- Every pronoun has exactly one possible antecedent. If not, repeat the noun. [GR-3]
- A "this" refers to exactly one item. If "this" can refer to more than one item, repeat the context. [GR-4]
- No false friends. [GR-5]
- No Latin abbreviations: "for example", not "e.g."; "that is", not "i.e."; list the items or omit "etc.". [GR-6]
- Gender-neutral language: no "he" or "she". [GR-7]
- Use the possessive form only when the sentence is clearly correct. [GR-8]

## Precise vocabulary

The approved meaning of a general word is narrow [1.3, 9.2]. The field has a precise technical noun or
technical verb [1.8, 1.12] for the action or item, so use that word.

| Unapproved | Approved: the precise word |
|---|---|
| get | read, load, compute, return, receive |
| do, perform, handle, deal with | the operation itself: sorts, transposes, rejects, clamps, retries |
| make | create, construct, allocate, emit |
| work, works | compiles, passes, converges, returns the correct result |
| break, blow up, go wrong | crashes, overflows, diverges, fails to compile, returns a wrong value |
| fix (as the description of a change) | guards, bounds, reorders, corrects |
| issue, problem | the defect: race, leak, overflow, out-of-bounds read |
| thing, stuff, part, piece | the noun: element, lane, row, tile, entry |
| fast, slow, big, small, a lot | the number with its unit: 3.1 cycles/element, 2e6 elements, 48 KiB |
| improve, optimize (unquantified) | reduces `X` from A to B |

Numbers carry units. Rates name both units (GB/s, flop/cycle). Complexity names the variable
(`O(n log n)` in `n`).

Level persists until changed or session end.
