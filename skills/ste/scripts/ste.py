#!/usr/bin/env python3
"""Simplified Technical English checker for technical prose.

  ste.py build [PDF]    build the dictionary from the ASD-STE100 PDF (downloads the official copy if no PDF)
  ste.py lint [FILE]    list STE violations in FILE (default: stdin); exit 1 if there are any
  ste.py score FILE...  print the violation counts of each FILE as JSON lines

The dictionary is ASD copyright. It is built on the user's machine from the user's own copy and is never
redistributed. Without a dictionary, `lint` checks only the style rules and says so.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

PDF_URL = "https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf"
CACHE = Path(os.environ.get("STE_HOME") or Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ste")
DICT = CACHE / "dictionary.tsv"

POS = r"\((?:n|v|adj|adv|prep|conj|pron|art|TN|TV)(?:, [^)]*)?\)"
HEAD = re.compile(r"^([A-Za-z][\w'./-]*(?: [A-Za-z][\w'./-]*)*) (" + POS + r"),?(?=\s|$)")
PAGE_FURNITURE = re.compile(r"^\s*(Issue 9|Page 2-|2025-01-15|ASD-STE100 Simpl|Word\s+Approved|\(part of)")


def parse_dictionary(layout: str) -> list[tuple[str, str, bool, str]]:
    """Parse the `pdftotext -layout` text of Part 2 into (word, pos, approved, meaning or alternatives)."""
    lines = layout.split("\n")
    first = next(i for i, l in enumerate(lines) if l.startswith("abaft (prep)"))
    entries, cur, c2, c3 = [], None, None, None
    for l in lines[first - 12 :]:
        if "ALTERNATIVES" in l and "STE EXAMPLE" in l:
            c2, c3 = l.index("ALTERNATIVES"), l.index("STE EXAMPLE")
            continue
        if c2 is None or c3 is None or not l.strip() or PAGE_FURNITURE.match(l):
            continue
        col1, col2 = l[:c2].rstrip(), l[c2 - 2 : c3 - 1].strip()
        m = HEAD.match(col1.strip()) if col1[:1].strip() else None
        if m:
            cur = [m.group(1), m.group(2), []]
            entries.append(cur)
        if cur and col2:
            cur[2].append(col2)
    out = []
    for word, pos, text in entries:
        text = re.sub(r"\s+", " ", " ".join(text)).replace("For other meanings, use:", "| other meanings:")
        out.append((word, pos, word.isupper() or word == "A", text.strip()))
    return out


def build(pdf: str | None) -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    if pdf is None:
        pdf = str(CACHE / "ASD-STE100_ISSUE9.pdf")
        if not Path(pdf).exists():
            print(f"download: {PDF_URL}")
            urllib.request.urlretrieve(PDF_URL, pdf)
    layout = subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True, capture_output=True, text=True).stdout
    entries = parse_dictionary(layout)
    approved = sum(e[2] for e in entries)
    DICT.write_text("".join(f"{w}\t{p}\t{int(a)}\t{t}\n" for w, p, a, t in entries))
    print(f"dictionary: {DICT}: {approved} approved, {len(entries) - approved} unapproved entries")
    # Issue 9: 875 approved, 1274 unapproved words. A shortfall means lost pages.
    if approved < 750 or len(entries) - approved < 1150:
        print("error: entry count too low, the PDF layout changed", file=sys.stderr)
        return 1
    return 0


def load_dictionary() -> tuple[set[str], dict[str, tuple[str, set[str]]]] | None:
    """approved words, and unapproved word -> (alternatives, parts of speech)."""
    if not DICT.exists():
        return None
    approved, unapproved = set(), {}
    for row in DICT.read_text().splitlines():
        word, pos, ok, text = row.split("\t")
        w = word.lower()
        if ok == "1":
            approved.add(w)
            continue
        alts = list(dict.fromkeys(re.findall(r"[A-Z][A-Z'-]*(?: [A-Z][A-Z'-]*)*(?= \()", text)))
        if w.upper() in alts:  # a part-of-speech entry, "oil (v) -> OIL (n)": the word itself is approved
            continue
        old_alts, old_pos = unapproved.get(w, ("", set()))
        unapproved[w] = (", ".join(dict.fromkeys(filter(None, [old_alts, *alts]))) or text, old_pos | {pos.strip("()")})
    return approved, {w: a for w, a in unapproved.items() if w not in approved}


def lemmas(t: str) -> list[str]:
    c = [t]
    for suf, rep in (("ies", "y"), ("ied", "y"), ("ing", ""), ("ing", "e"), ("es", ""), ("ed", ""), ("ed", "e"), ("s", ""), ("d", "")):
        if t.endswith(suf) and len(t) - len(suf) >= 3:
            c.append(t[: -len(suf)] + rep)
    return c


# Technical nouns and verbs of computing (rules 1.5, 1.12) that the dictionary lists as unapproved.
TECHNICAL = set("""addition base block branch call compile convert delete file guard mask masked process program
real request round rounding run running runs setting settings split store stored wrap stability""".split())

DETERMINER = set("a an the this these that those each all some any no two three four five six its their".split())

LATIN = re.compile(r"\b(e\.g\.|i\.e\.|etc\.|viz\.|cf\.|et al\.)", re.I)
CONTRACTION = re.compile(r"\b\w+(n't|'re|'ve|'ll|'d|'m)\b|\b(it|that|there|what)'s\b", re.I)
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)( not)? (\w+ed|built|done|made|given|known|shown|taken|written|found|kept|left|put|read|run|set|sent|seen|split|held|thrown|hidden|chosen|broken|driven|bound)\b", re.I)
HEDGE = re.compile(r"\b(basically|essentially|simply|actually|really|very|quite|just|sort of|kind of)\b", re.I)
PERSON = re.compile(r"\b(I|we|our|us|you|your|let's)\b", re.I)
PHRASAL = re.compile(r"\b(set|look|carry|figure|find|end|point|turn|go|run|take|come|break|blow|fill|pick|sort|work|shut|hook|wire|kick|spin|back|clean|free)(s|ed|ing)? (up|into|out|through|over|down|off|on|in)\b", re.I)
SENTENCE = re.compile(r"[^.!?\n]+[.!?]?")


def strip_code(text: str) -> str:
    """Code is not prose: identifiers are technical nouns, blocks keep their own rules."""
    # A markdown wrapper is prose. ponytail: in a wrapper, a bare fence closes it, never opens code.
    out, code, wrapper = [], False, False
    for line in text.split("\n"):
        fence = re.match(r"\s*```\s*(\S*)", line)
        if not fence:
            out.append("" if code else line)
            continue
        out.append("")
        if code:
            code = bool(fence[1])  # only a bare fence closes a code block
        elif fence[1] in ("markdown", "md"):
            wrapper = True
        elif not fence[1] and wrapper:
            wrapper = False
        else:
            code = True
    return re.sub(r"`[^`\n]*`", "X", "\n".join(out))


def findings(text: str, dictionary) -> list[tuple[int, str, str]]:
    out = []
    for n, line in enumerate(strip_code(text).split("\n"), 1):
        prose = re.sub(r"^\s*([-*+]|\d+\.|#+|\|)\s*", "", line)
        for kind, rx in (("semicolon", re.compile(r";")), ("latin", LATIN), ("contraction", CONTRACTION),
                         ("passive", PASSIVE), ("person", PERSON), ("hedge", HEDGE), ("phrasal", PHRASAL), ("emdash", re.compile("—"))):
            out += [(n, kind, m.group(0)) for m in rx.finditer(prose)]
        for s in SENTENCE.findall(prose):
            words = len(re.findall(r"[\w'-]+", s))
            if words > 25:
                out.append((n, "long-sentence", f"{words} words: {s.strip()[:60]}"))
        if dictionary:
            approved, unapproved = dictionary
            tokens = re.findall(r"[a-z][a-z'-]*|\d+", prose.lower())
            for i, t in enumerate(tokens):
                pair = f"{t} {tokens[i + 1]}" if i + 1 < len(tokens) else ""
                if pair in unapproved:
                    out.append((n, "word", f"{pair} -> {unapproved[pair][0]}"))
                    continue
                if t in approved or t in TECHNICAL:
                    continue
                hit = next((l for l in lemmas(t) if l in unapproved), None)
                if not hit or any(l in approved or l in TECHNICAL for l in lemmas(t)):
                    continue
                alts, pos = unapproved[hit]
                # A verb-only entry after a determiner is a noun use: a technical noun (rule 1.5).
                if pos <= {"v"} and i and (tokens[i - 1] in DETERMINER or tokens[i - 1].isdigit()):
                    continue
                out.append((n, "word", f"{t} -> {alts}"))
    return out


def lint(path: str | None) -> int:
    text = Path(path).read_text() if path else sys.stdin.read()
    dictionary = load_dictionary()
    found = findings(text, dictionary)
    for n, kind, what in found:
        print(f"{path or '-'}:{n}: {kind}: {what}")
    route = f"dictionary {DICT}" if dictionary else "style rules only (no dictionary: run `ste.py build`)"
    print(f"ste lint: {len(found)} findings, checked with {route}")
    print(f"rules: {Path(__file__).resolve().parents[1] / 'rules.md'}")
    return 1 if found else 0


def score(paths: list[str]) -> int:
    dictionary = load_dictionary()
    for p in paths:
        text = Path(p).read_text()
        counts: dict[str, int] = {}
        for _, kind, _ in findings(text, dictionary):
            counts[kind] = counts.get(kind, 0) + 1
        print(json.dumps({"file": p, "words": len(re.findall(r"[\w'-]+", strip_code(text))), **counts}))
    return 0


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "build":
        sys.exit(build(args[0] if args else None))
    if cmd == "lint":
        sys.exit(lint(args[0] if args else None))
    if cmd == "score":
        sys.exit(score(args))
    print(__doc__, file=sys.stderr)
    sys.exit(2)
