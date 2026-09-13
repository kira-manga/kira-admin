# App29 PG03 stack witness — independent actual source review 01

2026-09-13T22:56:07.542131+00:00 · NONAUTHOR `/root/w03_static_nonauthor_review`.
**SOURCE-ONLY ACCEPT. No blocking finding or required correction.**
This accepts the finite test-witness correction, not compilation, a passing witness,
MODEL actor/expiry behavior, new source freeze, execution admission or closure.

## Exact actual delta

Backend branch `remediation/app-29-backend-complaints`, HEAD
`f2e58eac0b139dca3a042c724d69c66a3d65278e`, remain unchanged. Git shows exactly one
unstaged file and an empty index; no other tracked or untracked backend change:

`src/test/kotlin/me/manga/kira/backend/common/infrastructure/persistence/PoolLeaseDispatchCreatorIntegrationTest.kt` (T).

| Item | SHA256 |
|---|---|
| T at immutable HEAD / actual PG03 | `f8583ac5daef026d2e691e2c42d14be93573dfbe442bee8c5f5d3188482eca1a` |
| Current T,923→929 lines | `915785fe0ddefa5444ba088792345e9141c129529d518ff3e525658cf9e6132e` |
| Author report `review/remediation/app-29-lease-dispatch-pg03-stack-witness-correction-author-01.md` | `dacf21f59d477438971a672dcfefbe174bb39113a9a6256b920d0807dfa5821b` |
| Author full-index patch, same stem `.patch` | `71903d644d18e2aa7325e3805a804fa8f3b46c8be4db2ee96574c47304eb8964` |
| Unchanged `PersistencePhaseContext.kt` | `2ce0328657f28541b93ba6b568f477070d09d9070ffdf902e29ac42da63b6237` |

All pins/readbacks match. The recorded full-index patch equals the entire actual
Git worktree diff. Independently replacing the unique old T:564 assertion with the
new seven-line block reconstructs the **entire current file byte-for-byte**:
one replacement, seven additions/one deletion, no other source transformation.
All bytes before the site and after it, including every later diagnostic/assertion
and the other tests, are unchanged. Production, build/settings/catalog and baseline
files are not modified. Author report/patch are regular0600 files.

## Predicate assessment

At current T:564–570 the same current-thread stack scan and JUnit assertTrue remain.
The predicate now requires both:

- exact `className == PersistencePhaseContext::class.java.name`;
- exact `methodName == "afterJdbcCall\$kira_backend"` in Kotlin source, whose escaped
  dollar represents the literal JVM name `afterJdbcCall$kira_backend`.

The class literal supplies the real existing declaring-class name, with no method
discovery, invocation, new dependency, alternative build mode or product visibility
change. Exact equality excludes unrelated test/synthetic frames and rejects both
bare unmangled `afterJdbcCall` and longer prefix/substring lookalikes. Neither the
assertion nor its actual call-site obligation was removed or weakened into a marker.

This matches the actual original failure frame
`me.manga.kira.backend.common.infrastructure.persistence.PersistencePhaseContext.afterJdbcCall$kira_backend(PersistencePhaseContext.kt:343)`.
Source342 declares the internal method; unchanged settings name `kira-backend`.
The comment accurately documents normal internal-member module-name mangling. The
Java StackTraceElement className/methodName properties are the two distinct
components; formatted stack prefix `app//` is not part of className.

Original XML remains SHA256
`7b9e31356522d9c22dac2e79839c65f5f5e80d456fa52e855eafdab74e41a943`.
Reused independent actual-result report
`review/remediation/app-29-lease-dispatch-pg03-independent-result-review-01.md`
remains `12823d278830ee5e52c22e935d0949aa62bf59a25f1e6830cf39876d4b60e0ac`;
it already binds this stack to the real normal main/test class-load origins.
No compiler, JVM, lint, synthetic test or result parser was run to manufacture a
passing witness here. This is a source assessment against retained evidence.

## Preserved obligations and next boundary

Exact reconstruction preserves first-failure retention and restoration, all
identity/original-budget/dispatch/count assertions, MODEL-only clock advance,
retirement checks, authentic actor construction/start/termination, final
quiescence/admission/expected-expiry checks, and fixture/database cleanup. They
move by six lines only. No product budget, ticket, phase or diagnostic value is
fabricated, and no selector or runtime outcome is changed by this review.

PG03 stops at CLOCK_ENTERED with its original AssertionFailedError; later tail,
MODEL expiry, retirement and actor outcomes remain **unproven**, not new failures
or implicit successes. PG03 remains1 PASS/1 FAIL with all six sticky failures;
its successful capture/disposal is not aggregate PASS or graceful/zero-kill proof.
PG02, PG18, Native05 UNQUALIFIED and broader W03/full47/consumer/production/recovery
limits remain as recorded. No historical result is rewritten.

This corrected file is still **uncommitted**. The old f2e58eac export/freeze contains
f8583ac5 bytes, not915785fe bytes. Primary must separately accept/checkpoint and bind
any future candidate and approve its exact evidence scope; existing PG03 admission
is consumed and does not authorize a rerun or qualify this changed source.

Reviewer wrote only this new private0600 report. No source/packet/ref/tracker edit,
static/build/test, freeze, collector/controller/helper execution, local heavy work,
resource operation, network, CI, staging, commit or push was performed.
