# App29 PG04 preparation — independent actual-delta review 01

2026-09-13T23:41:00Z · NONAUTHOR `/root/w03_static_nonauthor_review`.
**ACCEPT FOR INERT PREPARATION ONLY. No blocking finding or required correction.**
This accepts the finite PG03-to-PG04 selector/source-binding derivative. It does
not accept a final bound candidate, a freeze/preflight receipt, admission, an
execution result, integration or closure. The already accepted PG03 lifecycle
is reused, not requalified by a new harness audit.

## Sealed subject and readbacks

Subject: `review/working/app-29-lease-dispatch-pg04-preparation-01/`.
Exactly15 content members plus `SHA256SUMS` and `SEAL.sha256`; no extra member,
symlink or multiply linked file. All files are0600 and directories0700. Both
seal layers and every content digest verify, including final readback. All30
fixed `readback-pins.sha256` references match actual bytes. Those30 references
were not substituted for the inherited full source/authority inventories.

| Subject-relative item | SHA256 |
|---|---|
| `SHA256SUMS` | `fb92b666dd3cdc9f796514ffbb10084377d738c211d68c738fe10440d889016e` |
| `SEAL.sha256` | `0134cdc27df3e2469d221775313d1397c026f23d7acf76f0d7f0228d814667a8` |
| `ci/app29-gate-b.py` | `50c66e01d520889f005f9fdac1a4c6e2ada21099e74e05e4e5e227f58af4deb0` |
| `profile/profile.json` | `bdde85f1d0b1fa4f94a8995841fbf0608237f3c2c10ba14dd05dc4d537a13233` |
| `profile/profile.init.gradle` | `caf148974ed0d0dc2d54aeaf011bdc0af28ec71ad9569f144f4ee07faf5c5540` |
| `selection.json` | `8278a06b06c397ad5b9d79b5355a7c31de8b0b2d89add34ec122cd6ff056f6a2` |
| `source-delta.patch` | `71903d644d18e2aa7325e3805a804fa8f3b46c8be4db2ee96574c47304eb8964` |
| `tooling-delta.patch` | `89d8c717ca42c8d9bee44eb7e6c710b4117fc47de7ddfb30cbc7d40ff2879cbe` |
| `launch-and-collect-01.py` | `8e71d2421ef10db22b1babaacd9f94a7e2c0569711ae1d9520267081617869a6` |

All four recorded textual deltas were checked against their fixed PG03 baselines:
controller and five-file tooling against `app-29-lease-dispatch-pg03-bound-01`,
selection against `app-29-lease-dispatch-pg03-binding-preparation-01`, collector
against `app-29-lease-dispatch-pg03-admission-01`. Exact base/context and hunk
counts reconstruct every complete candidate file byte-for-byte, with no omitted
change. No patch was applied to a file. The baseline selection also matches its
inherited `04bcb997c228ddc4d2c3df79f52e787e31d8773864560f7266209961d0132916` pin.

## Exact source and one-case selection

Backend remains clean on `remediation/app-29-backend-complaints`:

- HEAD `0582abc737a89a663e770e78a5456961743330f6`;
- tree `d20c606f9d0b34b37696806988c28c05b69453ed`;
- sole parent `f2e58eac0b139dca3a042c724d69c66a3d65278e`.

The entire parent-to-HEAD full-index Git diff equals `source-delta.patch` and the
previously accepted author patch: exactly seven additions/one deletion at the
single stack-witness assertion in `PoolLeaseDispatchCreatorIntegrationTest.kt`.
Its SHA changes only `f8583ac5daef026d2e691e2c42d14be93573dfbe442bee8c5f5d3188482eca1a`
to `915785fe0ddefa5444ba088792345e9141c129529d518ff3e525658cf9e6132e`.
The exact declaring-class/internal-JVM-name predicate remains the reviewed
correction; every later assertion, other case and production file is unchanged.
`PersistencePhaseContext.kt` still hashes to
`2ce0328657f28541b93ba6b568f477070d09d9070ffdf902e29ac42da63b6237`.

The actual lightweight source-only checkpoint hashes to
`a5367797cb6eca5bcf39e35a457e45b2aae0062eddc8033d6581a9ea803784eb`.
New controller checks use its real `head/parent/tree/branch/status/source_path/
source_sha256/independent_review` fields; they do not pretend it is PG03's older
full source/transport checkpoint or invent a preliminary freeze.

The sole current literal selector is:

```text
me.manga.kira.backend.common.infrastructure.persistence.PoolLeaseDispatchCreatorIntegrationTest.MODEL work expiry inside actual afterJdbcCall cannot erase its admitted creator after epoch retirement
```

Selection, profile, controller and init agree: **one filter, three task argv
(`test`, `--tests`, literal), one case, one exact XML class/file**, and the
corresponding display name ending `()`. Required current outcome is1PASS with
zero FAIL/ERROR/SKIP, not a two-case total including reused evidence. There is no
wildcard, prior16, mixed-pool, enum or OwnershipIT replay. The normal complete
main/test compilation path is unchanged; only test execution is narrowed.

The source confirms MODEL still touches the existing lazy PER_CLASS database.
The numeric/image/session topology remains unchanged: one PostgreSQL17.6-alpine
plus one Ryuk0.12.0, not one total container. Only its explanatory basis changed.
One worker/maxParallelForks1/forkEvery0/JUnit-parallel=false remain; no negative
enum child JVM is selected. PG14 diagnostic records remain NOT_APPLICABLE/zero.

## Historical authority and inherited lifecycle

The old profile has95 keys; the candidate has106, removes none and changes only
10 current identity/selection/report/scope/basis/limits fields. All16 old
`pg02_*`/`pg03_*` fields are identical. Historical PG03 source inventory and limits
are exact copies of the old fields; the historical named-ref source bundle is
exactly the old request's bundle, distinct from the preserved HEAD-advertised
source-checkpoint bundle. Older result/authority fields are not overwritten.

The newly pinned actual PG03 manifest is
`0df6165f928d7a752d7a253d18078b099ca81eae9c7d5bc466bc828a74763f1f`.
It records481 source paths,214 review subjects/snapshots,348 preserved development07
seed keys and102 historical pins. New binding checks first require that complete
PG03 map/history, then permit exactly the reviewed f858→915 replacement. They
retain the full nonconflicting inherited approved/tooling union, now including
actual PG03, and the five original plus five explicit deployed tooling inputs.
This is a requirement on the future genuine freeze, not a claim that a PG04 freeze
or snapshot set has been generated or verified by this review.

PG03's pinned real result remains1PASS/1FAIL on run34786407104/attempt1. The new
checks require the actual MODEL failure and unchanged mixed-pool PASS separately;
that PASS is historical reuse, never fresh PG04 credit. Original CLOCK_ENTERED
failure, six sticky failures, raw stack/events and later unproven assertions are
retained. No inference of actor/expiry/retirement success, prior causation,
graceful shutdown or zero kills is introduced.

Textual comparison confirms the inherited `remove_owned`, bundle header/read,
local extraction, failure/attempt handling, output cleanup/absence, drain,
command ownership, source materialization, census/container lifecycle,
`capture_reports`, `required_capture_inventory` and main entry are unchanged.
The shared owner stays pinned at
`56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385`.
The finite controller additions concern current pins/ancestry, historical
selection/result/source checks and one-case XML/count handling. The one extra
owned PG03-parent commit read fits the unchanged before/after source verification
path. The final conjunctive PASS gate and cleanup sequence are unchanged:
missing required topology/XML, forced/nonzero commands, capture errors,
cancellation, budget failure or unknown custody cannot become PASS. Existing
25min/1200s/120s/900s/180s budgets and11 scoped output-absence obligations remain.

## Inert boundary and remaining primary work

Request remains `authorized=false`, attempts1, with current source0582abc and
parent f2, the unchanged singleton public prerequisite and exact private branch
ref. Current transport hash/size, final profile/init/controller/workflow and
deployment-checkpoint pins remain intentionally unbound. The new source-stage
marker is UNBOUND_PENDING_PRIMARY_ADOPTION. Existing early profile/source guards
remain fail-closed before target emission/helper/resource acquisition.

The collector starts with an unconditional SystemExit before imports, writes,
locks or network, and its actual Admin parent is zero. Apart from that inert stop
and finite namespace/parent/selection/commit-message changes, its accepted scoped
one-push/run/collection lifecycle is unchanged. No admission is implicit in a
later bound copy, and uncertain outcomes still do not authorize automatic retry.

`COMMANDS-REMAINING.md` correctly separates the immutable source-only checkpoint,
real named-ref bundle, final full v3 freeze, genuine validator stdout receipt,
later deployment checkpoint, still-false request and separately admitted
collector. Its freezer/validator argv match the actual unchanged tool's parser,
including the same three task argv. Passive source reading confirms the hard
348-seed-preservation guard and full issue-baseline-diff/snapshot checks. The
small source patch or30 readback refs cannot replace those obligations; copied
or fabricated preflight JSON is explicitly prohibited. The old PG03 binder is
correctly marked unsafe to run unchanged against this different source schema.

Primary may proceed only under its separately authorized binding scope, preserving
this packet and producing a distinct actual-bound successor for independent
review. No transport/freeze/binder/preflight/emit-target/controller/collector was
run or imported here; no syntax/AST/compiler/JVM/Gradle/test/CI/admission/resource
operation occurred. Reviewer wrote only this new exclusive private0600 report.
PG02/PG18 and broader historical limits remain; Native05 is UNQUALIFIED and
W03/full47/consumer/production/new-data/recovery closure remain open; W06 excluded.
