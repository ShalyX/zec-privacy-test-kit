# Production plan

Locked direction: [project brief](PROJECT_BRIEF.md). Deadline: **2026-10-28 23:59 UTC / 2026-10-29 00:59 Africa/Lagos**. Aim to freeze the submitted build by **2026-10-25 18:00 UTC**, leaving three days for final fixes, uploads and platform issues.

Provisional cap: **80 focused hours**, subject to actual availability; do not assume that registration alone allocated this time. Cut optional UI before cutting verification or submission buffer.

| ID | Deliverable and requirements | Dependencies | Budget | Acceptance checkpoint | Target |
|---|---|---|---|---|---|
| M-01a | Local feasibility: R-03a and R-04 | Zebra/Zallet regtest | 10–14 h | Real Ironwood send and recipient observation; planted leak and clean control. **Passed 2026-10-04.** | Oct 4 |
| M-01b | Public Testnet feasibility: R-03b | NU7-compatible wallet, sync, confirmed test funds | 6–10 h | Public sender-to-receiver txid and separate receiver observation, upgrade/version recorded. [Attempted Oct 4; blocked at wallet sync](PUBLIC_TESTNET_GATE.md). | Oct 7 |
| M-02 | Request preflight: R-01, R-02 | ZIPs 321/316; wallet validation | 12–16 h | Standard vectors and valid/invalid/unknown outcomes work. Parser and outage paths improved; network and receiver edge cases remain. | Oct 13 |
| M-03 | Full run and report: R-03–R-05 | M-01/M-02 | 20–26 h | Guarded regtest runner submitted, recovered an ambiguous broadcast through recipient matching, observed a confirmed Ironwood note, caught the planted canary, and produced a clean idempotent rerun. **Local path passed 2026-10-05; R-03b remains blocked.** | Oct 20 |
| M-04 | QA, clean setup, security check: R-01–R-06, C-02/C-03 | M-03 | 12–16 h | Clean clone passed all 18 tests and documented sample; full history/known-private-value scan clean; MIT license, official rules/form and exact claims reviewed. **Passed 2026-10-05.** | Oct 24 |
| M-05 | Submission assets and demo | Verified M-03/M-04 | 8–12 h | Clear live behavior, evidence, README and concise recorded fallback; format follows official submission fields. | Oct 25 |
| M-06 | Submit and save receipt: C-01–C-04 | M-04/M-05 | 4–6 h | Platform confirmation, URL/ID and submitted version recorded. | Oct 27 |

## Feasibility checkpoint

M-01a used the verified [Zallet release](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.3) with [Zebra](https://github.com/ZcashFoundation/zebra/releases/tag/v6.4.2) on local regtest. [Evidence](EVIDENCE.md) records the Ironwood payment, recipient observation, and planted leak. The CLI now reports those observations without sending keys to the kit. M-01b repeats the critical path on public Testnet; its [first attempt](PUBLIC_TESTNET_GATE.md) confirmed faucet funding but exposed an NU7 wallet compatibility blocker.

If a compatible public Testnet wallet is still unavailable by Oct 7, evaluate one documented alternate wallet/remote chain path, then reassess the evidence claim. A failure to detect the seeded leak blocks continuing on the same claim.

## Scope and finish conditions

Required: a truthful privacy boundary, genuine Zcash integration, reproducible run, open-source code, and timely submission. Optional features are cut in this order: hosted viewer, integrations beyond one wallet, extra leak classes, branding polish. No mainnet funds or user secrets enter the test process. Recheck the official registered submission form and rules before final packaging. Create the QA report against the exact final commit.
