# Current status

Updated: **2026-10-04, Africa/Lagos**. Lifecycle: **M-01a local feasibility passed / first CLI slice built**. Public Testnet gate M-01b and submission: **pending**.

## Canonical documents

- [Project brief](PROJECT_BRIEF.md)
- [Requirements](REQUIREMENTS.md)
- [Research and resources](RESEARCH_AND_RESOURCES.md)
- [Architecture](ARCHITECTURE.md)
- [Production plan](PRODUCTION_PLAN.md)
- [Local evidence](EVIDENCE.md)
- [Runnable CLI](README.md)
- This status file

## Verified progress

| Item | Evidence | Date |
|---|---|---|
| ZECATHON registration completed and rewards confirmed | User's direct confirmation in this chat; receipt/details not independently inspected. | Oct 4 |
| Concept locked: payment privacy test kit | User's direction in this chat. | Oct 4 |
| Official public schedule, tracks, rules, criteria inspected | [Event site](https://thezecathon.com/) and [public content file](https://thezecathon.com/darkpool/data.js). | Oct 4 |
| Source research completed for initial selection | [Research index](RESEARCH_AND_RESOURCES.md). | Oct 4 |
| Local environment check | Git and Python 3.14 present; `rustc` and `cargo` not on PATH. | Oct 4 |
| Alternative wallet runtime inspected | Official Zallet v0.1.0-beta.3 Linux amd64 tarball SHA-256 matched the release listing; its CLI help ran under WSL. | Oct 4 |
| Zebra runtime inspected | Official Zebra 6.4.2 Linux amd64 SHA-256 matched its release listing; isolated regtest reached height 118 with NU6.3 active. | Oct 4 |
| M-01a local transaction passed | Separate receiver wallet decrypted a confirmed 0.01 ZEC Ironwood note from txid `286f97d8e1daaf629d7d766b033f0989c15d987892fc94b71a4d8ab4e9345b93`; [full local evidence](EVIDENCE.md). | Oct 4 |
| First kit run passed controlled checks | Python CLI wrote [leaky report](examples/sample-report.json) with recipient `pass`, planted canary `fail`; [clean report](examples/clean-report.json) showed `pass` for both. Four ZIP-321/leak-control tests passed. | Oct 4 |
| Real transparent negative case passed | A second mined tx had a public 0.005 ZEC transparent output; recipient wallet labeled it transparent, and [kit report](examples/transparent-fail-report.json) marked preflight and receipt `fail`. | Oct 4 |

## Uncertainty and next action

M-01b is unverified. The local regtest proof is real but isolated; public Testnet funds, sync, and a separate recipient scan are still needed. The cloned `zcash-devtool` currently requires Rust 1.88; Rust is absent and the official toolchain host did not resolve from this machine. Public Testnet is due to activate NU7 around Oct 6, so validate the current wallet/node versions then. Also inspect registered-only submission fields before final package.

**Next action:** perform M-01b on public Testnet, expand ZIP-321 and wallet validation cases, then make one command orchestrate the scenario safely. There is no deployment or public repository yet. Local commit `d37de93` records the first code and evidence slice.

Provisional remaining budget: up to 80 focused hours plus calendar buffer through Oct 28. Actual capacity is unknown. Backlog: hosted report viewer, multi-wallet adapters, additional privacy checks. No pending concept choice.
