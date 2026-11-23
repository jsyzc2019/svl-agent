# criterion_note.md — T3 (written 2026-11-23T09:39:30Z, before any expected-answer file exists)

## 1. What I looked at

Only the 16 pairs inside `samples_blind.json`, read as character strings, plus their surface
differences. I did not consult `paper_flat.txt` while designing the rule, and nothing in
`criterion.py` can consult it (it opens no file and takes only two strings).

The observable differences I wrote down, pair by pair, before naming any rule (verbatim fragments):

| pair id | what differs between text_a and text_b (surface observation) |
|---|---|
| P01 | nothing at all, the two strings are identical |
| P02 | text_a says `at approximately 2.0 ns`; text_b says `at 2.0 ns` — the numeral survives, a bounding adverb disappears |
| P03 | text_a `0-10 ns`; text_b `0-10000 ps` — the numeral changes and the unit word changes with it |
| P04 | text_a `Ni(511) at 700 K`; text_b `Ni(0.25 eV) at 700 K` — one numeral is swapped for a different numeral carrying a different unit word |
| P05 | text_a `first 25 ns`; text_b `first 25000 ps` — same shape as P03 |
| P06 | nothing at all, identical strings |
| P07 | text_a `from 100 ns`; text_b `from 100000 ps` — same shape as P03 |
| P08 | text_a `from 8.2-10.0 ns`; text_b `from 5-10.0 ns` — a numeral replaced, unit untouched |
| P09 | text_a `Figure 4`; text_b `Figure 0` — a numeral replaced |
| P10 | text_a `rate 10^{-4}`; text_b `rate 26.2^{-4}` — a numeral replaced |
| P11 | text_a `over 26.2 ns`; text_b `over .` — numeral and unit both gone |
| P12 | text_a `persist for 20 ps`; text_b `persist for and is counted` — numeral and unit both gone |
| P13 | text_a `the full 26.2 ns trajectory`; text_b `the full 10 kJ trajectory` — numeral plus unit replaced by a foreign pair |
| P14 | nothing at all, identical strings |
| P15 | text_a begins `5 are Boltzmann marginals`; text_b begins `are Boltzmann marginals` — numeral gone |
| P16 | text_a `final checkpoint ( 26.2 ns per replica)`; text_b `final checkpoint ( 2 fs per replica)` — numeral plus unit replaced by a foreign pair |

Three clusters emerge and they are exhaustive over these 16 pairs:

* **C1 (P01, P06, P14)** — every element of text_a is still in text_b.
* **C2 (P03, P05, P07)** — a numeral is gone, but a *different* numeral of a different magnitude
  appeared in its place, next to a different unit word.
* **C3 (P02, P04, P08, P09, P10, P11, P12, P13, P15, P16)** — a numeral that text_a states has no
  equal-value counterpart in text_b, or a bounding adverb that text_a states is simply missing.

## 2. The rule I induced

    judge(text_a, text_b) returns True  <=>
        (a) every numeric quantity stated by text_a is re-stated by text_b with the same value
            (matched as a multiset of values, so "10 … 10" needs two tens in text_b), AND
        (b) every limiting expression in _LIMITERS that occurs in text_a also occurs in text_b.

Clause (a) rejects C3 and also rejects C2 — in C2 the stated value literally disappears (10 becomes
10000) and the surface evidence carries no arithmetic relation between the two spellings.
Clause (b) catches the adverb loss (P02).
Clause (a)+(b) accept C1 and accept a pure re-ordering, because both clauses are order-insensitive.

The accepted set is therefore *smaller* than the rejected set on these samples, and I made no
attempt to fix that: a rule that would split the same evidence the other way would have to smuggle
in knowledge about how the strings were produced.

### Conventions inside the rule, stated explicitly
* Numeric literal = maximal run of `[sign] digits [. digits] [e[sign]digits]`; a `.` continues a
  number only when a digit follows it, so `26.2` and `298.15` stay whole and a sentence-final period
  never glues two numbers.
* A `+`/`-` opens a signed literal only when the previous character is not a digit, so the ranges
  `0-10`, `3.2-5.0`, `1.8 - 1.9` and compounds like `checkpoint-300`, `Ni(511)` yield the separate
  stated values `0,10` / `3.2,5.0` / `1.8,1.9` / `300` / `511`. This was decided from the strings
  themselves: in `0-10 ns` the two endpoints are what is asserted; `-10` is not asserted anywhere.
* Limiting expressions are a closed literal list (`at least`, `at most`, `more than`, `less than`,
  `nearly`, `almost`, `around`, `about`, `approximately`, `roughly`, `exactly`, `precisely`, `only`,
  `over`, `under`, `above`, `below`, `within`, `between`, `up to`, `as much as`, `no more than`,
  `no fewer than`), matched case-insensitively with non-letter neighbours on both sides.
* Anchors are verbatim substrings of text_a: the numeral spelling or the adverb that failed the test,
  so an external checker can search for them literally in text_a (and hence in the primary source).
* No pair id, no file, no clock, no random, no import of any kind; builtins only.

## 3. Alternative I considered and rejected

C2 looks like a unit-prefix shift, and a rule that recognised SI prefixes and compared quantities in
base units (`10 ns = 10000 ps`) would flip exactly those three pairs. I deliberately did **not** add
it. Reasons, in order of weight:

1. The prefix equivalence is *not* derivable from the pair alone; it needs outside knowledge about
   unit systems plus an arithmetic rewrite of one string into the other. Rule (a) asks only that a
   stated value be re-stated.
2. Adding it at this point would be tuning the criterion to make a category of cases pass, which the
   job specification forbids (section 7 discipline 6, no iterating until it runs through).
3. `criterion.py` was frozen at T3, and no expected-answer file existed yet when it was frozen, so I
   could not have been steering it toward anything measured later.

If a reader wants the stronger rule, the honest statement is: it exists, it is implementable, and it
would change the answer on the C2 cluster. That is exactly the interpretive latitude I report in the
verdict rather than resolve by re-fitting.

## 4. Disclosure required by section 7 discipline 2

I am both the author of the pairs and the author of the rule, so I do know which edit each pair
received; that knowledge cannot be unstated. Mitigations actually exercised:

* The rule was written and frozen at T3 **before** the expected-answer file was written at T4, and
  its decisions were never fed back into the rule.
* The rule contains no vocabulary of the construction (`copy`, `swap`, `substitute`, `delete`,
  `prefix`, `conversion` do not appear in `criterion.py`), and no pair id.
* The rule is *not* 100% aligned with my recorded construction facts by design; it is a surface rule,
  and the agreement rate is measured afterwards rather than assumed.
* `judgments.json` (T5) is produced by mechanically importing this file and running it over
  `samples_blind.json` in id order — the same thing the委托方's replayer will do.

## 5. Known limits of this criterion (stated, not hidden)

* It treats every numeral as a claim, including reference years, figure numbers and section numbers.
  In this paper that is harmless (both sides carry them) but on another corpus it could produce
  rejections that are really about numbering rather than about physics.
* It is blind to anything a rewording can hide: a paraphrase that keeps the numbers and the adverbs
  intact but changes the noun they attach to is accepted by this rule.
* It is order-insensitive on purpose, so it cannot see a swap of two measure phrases; that is a
  deliberate choice (a swap states the same quantities), not an oversight.
