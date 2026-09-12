# Core C2 getter ownership — primary implementation agreement

2026-09-11 UTC. Source authoring authorized; execution/retry is not authorized.

Primary adopts plan `c273447dd579c4a5164fc0052518e43fa7f81587193755a05bace3076b9b81fe`
and App02's independent GPT-6-Astra/max source-plan CONCUR delivered in the team
mailbox. The reviewer checked investigation `f065bb1b…`, exact getter/helper/retention,
native04's current Fault harness (`da6acff1…`) and the actual failed47 evidence.
No material objection remains. This is not a prediction that the next47 will pass.

Backend03 may change only the private getter and its smallest meaningful existing
native-harness coverage. Own BaseStatement before executeWithFlags; nest ResultSet
ownership so result closes before parent on success and exceptional exits. Keep SHOW,
result/update traversal, NO_DATA, QUERY_SUPPRESS_BEGIN, null/unknown fallback and all
isolation mappings. Transfer warnings before parent closure clears statement warnings.
Use normal Java nested try-with-resources for primary/suppressed failures. Do not
change shared execSQLQuery's returned-result ownership or any retention predicate.

Use genuine PgConnection/PgStatement/PgResultSet and existing Owned/ExecutorFault/delegate
facilities, preserving native04 getRawArguments delegation. Add only three meaningful
coverage groups: repeated success with autocommit=false and IDLE before/after;
pre-result execute failure with original exception and genuine parent first-close;
during-use getEncoding/getString failure with original exception and both acquired
first-closes. Capture actual Life references before compaction and restore the genuine
executor before retention checks. No invented result receipt when none was acquired.
Reuse existing first-close/stickiness tests rather than duplicating their matrix.

Preserve before-images, all47 assertions, native03 FAIL/native04 distinct acceptance,
candidate a415, immutable freeze/bundle and all348 historical source seeds. No private
source may be pushed to public Backend. No production test hook, new framework,
retention relaxation, dependency acquisition, build/checker/test, CI dispatch or commit
is authorized by this agreement. Primary will inspect the sealed actual diff and
obtain nonauthor review before admitting the smallest changed-source validation.

Backend03 reports exact changed paths/hashes, coverage identities, no-execution status
and unresolved concerns. App02 remains nonauthor reviewer. Primary owns architecture,
new candidate identity, private provenance binding, scheduling, cleanup and acceptance.
