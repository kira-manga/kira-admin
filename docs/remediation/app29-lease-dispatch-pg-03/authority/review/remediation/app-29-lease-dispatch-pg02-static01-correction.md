# W03 PG02 static01 — factual result and one format correction

2026-09-13, primary. The frozen static-only batch `app-29-lease-dispatch-pg02-static-01` failed exactly one `standard:multiline-if-else` finding at PersistencePgOwnedCutIntegrationTest.kt:1405. Detekt and main/script Ktlint reports are clean; no compilation/tests requested. Raw FAIL is retained unchanged. Both Gradle stop commands exited0; five owned-child barriers returned normal/absent without signals; outputs absent, source/dependency pins preserved.

Correction: add braces to the already reviewed first/null versus distinct/suppressed exception condition, without changing its expressions, ordering, exceptions, timeouts or oracles. The final independent R1/R2 review remains the semantic authority; later binding review must inspect this mechanical delta too. No production/vendor change.

Use the existing `ktlintCheck` task alone for the changed formatting, rather than rerun Detekt or build/tests. Existing runner accepts ktlintCheck; creating a per-file harness for one 45s static batch adds no value. Runtime compile + exactly the two previously failed PG tests remain separate, not approved by a static PASS. Freeze all481 paths including all348 development07 seeds. Preserve prior manifests/results.
