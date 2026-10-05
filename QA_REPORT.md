# QA report

Version: M-04 QA gate. Environment and check date: Windows 11 host, WSL Ubuntu 22.04, Zebra 6.4.2, Zallet 0.1.0-beta.3, local NU6.3 regtest, 2026-10-05. Official rules and authenticated form last checked: 2026-10-05. Readiness: **M-04 passed; submission remains pending packaging, public URLs, and the disclosed public Testnet limitation**.

| Check ID | Requirement / claim | Test and environment | Result | Evidence | Severity / fix |
|---|---|---|---|---|---|
| Q-01 | R-03a real separate-wallet shielded payment | Guarded runner submitted 0.001 ZEC; receiver observed confirmed Ironwood note at height 130. | Pass | [M-03 evidence](EVIDENCE.md) | Core local path verified. |
| Q-02 | R-03a uncertain broadcast never blindly retries | Wallet operation returned `-4`; checkpoint blocked retry; recovery required matching recipient note. | Pass | Ten checkpoint and boundary tests plus [evidence](EVIDENCE.md) | Keep recovery contract in regression suite. |
| Q-03 | R-04 planted canary detection | Scan `examples/leaky-app.log`. | Pass | [Leaky report](examples/m03-leaky-report.json) | Finding contains file index, line and marker hash only. |
| Q-04 | R-04 clean control | Rerun from `reported` checkpoint with clean log. | Pass | [Clean report](examples/m03-clean-report.json) | No new send or block on rerun. |
| Q-05 | R-05 redacted report and explicit boundaries | Inspect report v2 fields and raw-value absence. | Pass | [Clean report](examples/m03-clean-report.json) | Full repository secret scan remains M-04. |
| Q-06 | R-03b public Testnet confirmation | Tested current Zingo stable and prerelease against active NU7 branch. | Unverified | [Public gate](PUBLIC_TESTNET_GATE.md) | Upstream wallet support blocks receiver proof; disclose exactly. |
| Q-07 | R-06 clean checkout | Clean export of the staged M-04 candidate; no untracked worktree files or installed dependencies copied. All 18 tests passed and the documented request-only command returned the expected exit 1 with `unverified`, `unverified`, `fail`. | Pass | Clean export `work/m04-final-export-20261005`; generated report kept outside the repository. | Repeat only after a material setup change. |
| Q-08 | Sending boundary cannot escape local regtest | Review found missing sender URL and chain guards plus a pre-checkpoint crash window. Tests were added first; runner now requires plain loopback HTTP, verifies the regtest genesis before wallet access, writes `submission_started` before `z_sendmany`, and polls non-destructively. | Pass | `tests/test_scenario_runner.py`; 18-test full suite; live idempotent replay held height 130 and empty mempool before/after. | Release-blocking findings resolved. |
| Q-09 | Repository hygiene and build-window compliance | Scanned all 13 revisions and tracked files for private keys, credential assignments, seed material, and the known private M-03 values. Checked tracked file sizes, repository object health, commit timestamps, and license. | Pass | No secret findings, no known private-value hits, no tracked files over 1 MiB; history begins 2026-10-04 after the Sep 28 build opening; MIT license added. | Repeat immediately before publication. |
| Q-10 | Official rules, track and claims | Authenticated Rules, Tracks & Prizes, and Submit Project views reviewed read-only. | Pass | Core & Tooling matches wallet/tooling scope. Deadline Oct 28, 2026 23:59 UTC; form requires project name, track, ≤2,000-character description, repository, working demo, two-minute video, and public-repo attestation. | Do not claim public Testnet completion; preserve the R-03b disclosure. |

Coverage: core local behavior, checkpoint persistence, ambiguous submission recovery, recipient observation, planted leak, clean control, report redaction, clean-checkout onboarding, repository history and secret hygiene, license, and official form requirements have direct evidence. Public Testnet remains unverified.

Submission blockers: repository publication, working demo and video links, final package, and submission receipt. R-03b remains a disclosed upstream compatibility limitation unless a compatible wallet ships before freeze.

Optional improvements: hosted read-only report viewer, more wallet adapters, and additional leak classes remain backlog.
