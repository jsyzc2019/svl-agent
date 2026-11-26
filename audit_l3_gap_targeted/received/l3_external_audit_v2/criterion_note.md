# Criterion Note — Assertion Preservation (`judge(text_a, text_b)`)

## Semantic basis

The function treats an *assertion* as the truth-bearing content of a sentence:
the claim it makes about the world and the polarity of that claim. Two texts are
considered equivalent for our purposes when `text_a` **fully preserves the
assertion** of `text_b`. Preservation requires three things simultaneously:

1. **Polarity match** — both texts must be affirmative or both negated.
2. **Predicate completeness** — the tail predicate/complement of the claim must
   not be dropped, which would weaken or materially truncate the assertion.
3. **Coherent discourse relation** — logical connectors
   (despite/however/although/finally/while/...) must express the same relation;
   a swapped connector can invert the rhetorical meaning even when surface words
   are similar.

The comparison is done after a lossless normalization: lowercasing, whitespace
collapse, and punctuation stripping (apostrophes retained so contractions like
*can't* remain detectable negations). This makes formatting/case/punctuation-only
differences automatically pass.

## Checks in order

1. **Negation-polarity flip (bidirectional).** Count negation markers from
   `NEGATION_TOKENS` plus multi-word `NEGATION_PHRASES`. If one text carries a
   negation and the other does not → **fail**.

2. **Assertion-tail deletion (directional).** If one text is a strict
   token-prefix of the longer one, or is significantly shorter (≥60% prefix
   overlap), the dropped tail is flagged → **fail**.

3. **Connector change.** Compare connector sets. A single swap between a known
   *equivalent* pair (e.g. `Despite ↔ Although`) is allowed; any other
   addition/removal/swap → **fail**.

4. Otherwise → **pass** (meaning-preserving rewording).

## Concrete examples (from own samples)

### (a) Negation-polarity flip — FAIL
- `text_a`: "The drug reduces pain."
- `text_b`: "The drug does not reduce pain."
- `neg_a = 0`, `neg_b = 1` ("does not") → polarity mismatch.
- Result: `(False, ["negation-polarity: ..."], ["does not"])`.

### (b) Assertion-tail deletion — FAIL
- `text_a`: "She opened the door and walked into the garden."
- `text_b`: "She opened the door."
- `text_b` is a strict token-prefix of `text_a`, tail `and walked into the
  garden` dropped.
- Result: `(False, ["assertion-tail-deletion: ..."], ["and","walked","into","the","garden"])`.

### (c) Connector change — FAIL vs. allowed
- `text_a`: "Despite the rain, the team won."
- `text_b`: "However the rain, the team won."
- `{despite}` ≠ `{however}`, and `despite/however` is **not** a known-equivalent
  pair → **fail** (`connector-change`), anchors `["despite","however"]`.
- Contrast: "Despite the rain..." vs. "Although the rain..." →
  `despite ↔ although` is a known-equivalent swap → **pass**.
- Formatting-only: "The cat is on the mat." vs. "The cat is on the mat" →
  **pass**.

## Limitations

- **Lexical-only negation.** Absence of an explicit marker (e.g. "fails to",
  "unaware", implicit negation) is not detected; only the curated token/phrase
  lists are used.
- **Prefix heuristic.** Tail-deletion detection relies on token-prefix ordering;
  a legitimate paraphrase that reorders clauses ("Because X, Y" → "Y because X")
  could be misjudged as short/longer without a clean prefix and thus may pass or,
  in edge cases with high partial overlap, be flagged.
- **Connector equivalence list is finite and hand-curated.** Novel equivalents
  or subtle contrast relations (`while` temporal vs. concessive) are not
  disambiguated by part-of-speech or semantics.
- **No syntactic or semantic parsing.** Contradictions expressed with different
  negation scope (double negation, "not uncommon") are counted as mere presence,
  not logical polarity.
- **No external knowledge.** Cannot verify entailment beyond surface structure;
  synonym-based meaning changes with identical length/structure pass.
