# W03 PG carrier01 — independent literal-binding check

2026-09-13 UTC · `/root/backend20_correction_review` · private0600.

**Concur with the exact three-literal binding only. No new mechanism review or execution
admission.** Actual-delta review `8cbc7d2d04ba7eb1c8b0a73c3a1e87bc2cdc7eb6bb6e0f0ed8f1d4a322b31ed1`
remains unchanged; its genuine freeze/receipt/checkpoint/request/admission prerequisites remain.

Admission directory: `review/working/app-29-ordinary-connected-pg-admission-01/`.
All four `unbound-author/` files rehash to the previously reviewed author bytes. Deriving init
by replacing its single null profile literal, then hashing that actual init and replacing
exactly two controller None literals reproduces the final carrier files byte-for-byte.
Profile and workflow are unchanged; no other byte changed. The generated literal-only diff
exactly matches `literal-binding.diff`:
`c81ce67292957b118f8b52a6455906690c7c81c3f799ba5422ed58adec5c2817`.

| Final carrier-relative file | Actual SHA-256 |
|---|---|
| `ci/app29-gate-b.py` | `30b30d4907f6e5be366b0a0ef527686136b1ddb5fa8acef9d3830cdc8e937d88` |
| `.github/workflows/app29-gate-b.yml` | `20d4f52e799bc291e51333fe45a9f2215d32884692f34578091d6924ee56bb85` |
| `profile/profile.json` | `2cf80540dccd11b5b1088a36244a3c7ab68d8b6050a32008d921862265fa0438` |
| `profile/profile.init.gradle` | `edbe0440d247e66c5a7c8efc17de347e7f077c0eca49b10fbd719ba4b2ce2172` |

`final-tool-pins.json` rehashes to `cf9958107faf682fbf831237d9732f2ae8c8b666a66618c809706121e15a7ba1`
and names exactly these four files. Original carrier handoff/diff/SUMS are unchanged historical
unbound evidence, not current final-byte checksums. No blocker found in this literal derivation.

Passive JSON/text/hash comparison only; this0600 note is the only new write. No import, parser,
checker, freezer, build/test, CI/network, process/service control or Git mutation. No genuine
freeze/local preflight was performed by this reviewer; primary owns those separately.
