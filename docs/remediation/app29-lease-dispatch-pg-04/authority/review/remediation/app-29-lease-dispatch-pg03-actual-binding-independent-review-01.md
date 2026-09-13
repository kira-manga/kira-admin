# App29 PG03 — independent actual-bound review 01

2026-09-13 UTC. NONAUTHOR: `w03_static_nonauthor_review`.
**ACTUAL-BOUND APPROVE: source/receipt/private staging are consistent with the
accepted preparation.** No material mismatch found. This is not PG03 execution
admission, a committed carrier, compilation, test PASS or product acceptance.

## Exact reviewed inputs

Workspace-relative packet aliases:

- **B**: `review/working/app-29-lease-dispatch-pg03-bound-01/`
- **E**: `review/working/app-29-lease-dispatch-pg03-admission-01/`
- **F**: `review/working/app-29-w03-integrated-driver-lease-dispatch-pg-03/`
- **Payload**: `kira-admin/docs/remediation/app29-lease-dispatch-pg-03/`

| Actual file | SHA-256 |
|---|---|
| B `ci/app29-gate-b.py` | `406b9fd6af8913de5ec5aa9eb1426cd9bc8eb95a0a1717deb818a9d42ec4b382` |
| B `profile/profile.json` | `5f73278a73b86786690d68d2c8f1e62023092e9c89ebc56bb8b4c4babd236e45` |
| B `profile/profile.init.gradle` | `7fb5a7a950aac011017eb99c69e96be595b4e737f8f765b8e6f5c198353584f6` |
| B `.github/workflows/app29-gate-b.yml` | `3f9973b12ce69b07431f7714c8a9e0f9b3cb15051e76ca3570c085d22e149146` |
| B / Admin `ci/app29-gate-b.request.json` | `bfa7771fb1567a046d7551eacd21f065271f6186f5f17f29fc5967b3e6e9cf53` |
| Admin `ci/app29_owned_children.py` (unchanged fifth tool) | `56b66cfe8799123c719eaf048f81c542e5e4129d71c490cae99a38396c2a3385` |
| F `manifest.json` | `0df6165f928d7a752d7a253d18078b099ca81eae9c7d5bc466bc828a74763f1f` |
| F `hosted-local-preflight.json` / E `preflight.stdout` | `7a03859975aeb73898a49bb138bd1312b79aac6bc9952a9f495642a2203a85e7` |
| Payload `checkpoint.json` | `acb405c5acd7dc826e1a17ac27e6daa7c48f12242c1eea1eec28f3a3e90a0eb9` |
| E `transport-prepared.json` | `c9e148002f5dc4aba2f7956bdb0b099dc7a4df87aecc0f98b00f360d32cc5062` |
| E `literal-binding.diff` | `fc882b082bf73b3336432476c90dbc45625636aa405c179795e1b2b38c0494ba` |
| E `approved-inputs.json` | `b50b911c1706798288e21b0d7af42707ee66be536168bddafa64499412d4c9a4` |

Reviewed the actual214-line one-use binder
`review/working/app-29-lease-dispatch-pg03-bind-01.py`, SHA
`ee79f95b00df54c7baab8459c5da88e17f041f875f0de4155c3c3c2cb2d779c5`,
and primary agreement
`review/working/app-29-lease-dispatch-pg03-binding-primary-agreement-01.json`, SHA
`a250ea0e5fe01f105437d89a7d364f0937ab076176b0c6903528a2c85487a5cc`.
They authorize finite binding/freeze/preflight/private staging, not dispatch.

## Findings

### Exact preparation-to-bound changes only

The accepted preparation review remains
`bd11af9b9bfd9a4acc042c6def774bd2b4c92062e14be3b9470ced152b260ea5`.
All22 preparation content files and both seal files remain unchanged.
Independent full-file reconstruction reproduces `literal-binding.diff` exactly.

Only three profile fields change: current scope prefix, PG03 stage to
`BOUND_BY_PRIMARY`, and append-only PG03 provenance. The eleven added pins are
that accepted review, the accepted synthetic review and all nine synthetic packet
files. Existing history, source/selection references and all other profile fields
are unchanged. Init/controller/workflow contain only the permitted bound paths
and actual profile/init hash literals. No executable control-flow change occurs.
The separately completed request differs only in checkpoint and mapped tooling
pins, retaining `authorized=false`, attempts1, source transport and fixed budgets.

Consequently the reviewed cleanup30b9 behavior and four-group synthetic evidence
remain applicable to the unchanged cleanup seam, not a new full-controller test.
The same two literal methods/five task argv, ordinary main/test compilation,
required XML identities/topology, all PASS conjuncts and ownership gates remain.
No previous16 replay or new helper/qualification gate was introduced.

### Genuine recorded freeze/validator result, not manufactured receipt

The recorded freeze command at21:48:13.765960Z uses the unchanged real v3 freezer,
SHA `e8c6a48fc26c634fbccbb081651631fb5c767099b1143ab4dbe8439f6060d0fe`,
exact389 approved-input arguments, five tooling arguments and the same five task
argv. The validator command at21:48:17.555146Z binds the actual new manifest SHA
above and the identical task argv. Both recorded exits are0; both stderr files
are empty. Command hashes are respectively
`6a3135f244ecf65223ced94079f393902c78e4acdc0c573942e7ba4c24ccab76` and
`abc1fba25c10eb6dd17f4e94baff732306f92bf8f20fce60525cc66778ae8b19`.

The binder's measured path records subprocess argv/stdout/stderr/exit with120s
bounds and no retry. Its receipt write copies the validator stdout bytes directly.
The retained65-byte stdout and hosted receipt are byte-identical:
`READ_ONLY_V3_PREFLIGHT_PASSED`, `source_paths=481`. The deployment checkpoint binds
that exact receipt, manifest and verifier. This review inspected those actual
records and binder source; it did not rerun the freezer, validator or binder.

### Complete source and nonconflicting authority

The final manifest preserves the approved preliminary source manifest
`9a13d2299b7c58e23a6aaf67e1140c0a5d0c906ec7f574bcac8f3c877f0ff786`:
all481 current source hashes,214 fresh snapshot mappings,102 historical pins,
all348 seed paths, subject/removal maps, repository identity and task selection.
Backend remains clean at `f2e58eac0b139dca3a042c724d69c66a3d65278e`.
The whole issue-baseline diff remains
`075443cf4c24f1a7e95e30915ce6043d238a65095712aa2b045d09ef2ab91a61`.

The389 approved entries are exactly the prior355 plus34 distinct accepted inputs:
the remaining sealed preparation files, final profile, both reviews and nine
synthetic files. No old pin is overwritten; all inherited approved/tooling
provenance remains. Tooling is exactly the unchanged five base tools plus five
bound deployment tools.

Recomputed authority is exactly **708 files / 39,468,396 bytes**. Every original
and staged copy matches its declared digest, with no missing/extra file or
contradictory overlap. The current manifest, genuine receipt, later checkpoint
and actual request are excluded from their own earlier frozen input maps; the
manifest/receipt are added only to the later transport authority.

The original, authority and deployed current source bundle match
`b606cb5ed40814dc23c5c8c61a564de07d917d4a05b6fbca4c4b73841bea63fe`,
287442 bytes. Its header retains the exact public prerequisite and singleton
`refs/heads/remediation/app-29-backend-complaints` at f2e58eac; private parent stays
c67ddcd. The old HEAD-advertised04a50353 bundle and full source checkpoint remain
separate immutable history. No bundle import or verification command was rerun.

### Staged deployment and authority state

All five staged tooling files exactly match their bound originals/owner pin,
the request's tool map and frozen tooling. Both false-request copies are identical.
All new bound/admission/freeze/payload files are0600 and directories0700, without
links or nonregular entries; staged tooling is0600.

Admin HEAD is still `bc17ad0e1dd1db509aa6d4e67a54975deef626bd`. Recorded prior
tool/request hashes match that parent's Git objects. Only the expected controller,
workflow and request are modified tracked files; the index is unchanged, and the
new payload/profile paths are uncommitted. This is private worktree staging, not
a PG03 carrier commit. `source_accepted=true` has the checkpoint's explicit
source/transport/preflight-only meaning, never runtime or fix acceptance.

## Remaining admission and limits

Primary must accept this actual-bound review and separately authorize any final
carrier/request transition and single execution attempt. The current false request
remains a hard stop. No commit, push, CI/PG dispatch, automatic retry or integration
closure is authorized by this report. Primary's supplied Apple05 completion context
was not re-audited here and supplies no PG03 correctness credit.

Historical PG02 remains its original compile failure with no test XML, incomplete
capture/disposal and all seven sticky failures. PG18 and Native05 limitations are
unchanged. There is no PG03 compilation/test result yet and no W03/full47/consumer/
production or public private-ancestry authority.

Only passive source/Git/JSON/hash/stat reads, in-memory comparisons and this new
private0600 report were used. No target/controller/helper execution, syntax check,
v3 rerun, build/CI/PG, new harness, resource control, source/tracker/old-review edit
or mutation of the staged packets was performed by this reviewer.
