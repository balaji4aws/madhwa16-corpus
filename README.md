# madhwa16-corpus

A transcribed corpus of **Mādhva (Dvaita Vedānta) pravachanas** (spiritual discourses),
prepared for grounded, reference-cited Retrieval-Augmented Generation (RAG). Intended for use
by a ChatGPT plugin and other AI assistants.

## What is here

```
manifest.json            — index of all talks (start here)
talks/<slug>.json        — per-talk metadata (source, speaker, language, status)
transcripts/<slug>.md    — the transcript, with timestamps for citation
```

## Trust rules — READ BEFORE USING THIS CORPUS

This corpus exists to answer questions about Mādhva teachings **authentically**. Any bot built on it
MUST inherit these rules:

1. **Answer only from this corpus.** Never fabricate or reach to outside sources at answer time.
2. **Always cite.** Every answer references the talk (`source_url`) and timestamp it came from.
   "I don't have that in the corpus" is a valid, preferred answer over a guess.
3. **Unvalidated Sanskrit is MASKED, never shown.** Where a verse was recited, the transcript shows
   `[unverified Sanskrit verse recited — masked pending human validation]`. The exact verse text is
   deliberately withheld until a human scholar validates it. **Do not attempt to reconstruct, guess,
   or fill in a masked verse.** A wrong sacred verse is worse than no verse.
4. **Kannada discourse is a machine draft** unless a talk's metadata says `kannada_human_reviewed: true`.
   Treat it as the speaker's paraphrased meaning, not a verbatim quotation.

## Status

Early, work in progress. Transcripts are machine drafts; Sanskrit verses await human validation and
will be filled in over time. Content can be corrected or replaced in any future commit.
