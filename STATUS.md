# Current status

Updated: **2026-10-09, Africa/Lagos**. Lifecycle: **M-04 QA passed / M-05 demo hosted and source published, video pending**. Public Testnet gate M-01b: **NU7-compatible scan completed; sender balance zero, transaction unverified**. Submission: **pending**.

## Canonical documents

- [Project brief](PROJECT_BRIEF.md)
- [Requirements](REQUIREMENTS.md)
- [Research and resources](RESEARCH_AND_RESOURCES.md)
- [Architecture](ARCHITECTURE.md)
- [Production plan](PRODUCTION_PLAN.md)
- [Local evidence](EVIDENCE.md)
- [Public Testnet gate attempt](PUBLIC_TESTNET_GATE.md)
- [Runnable CLI](README.md)
- This status file

## Verified progress

| Item | Evidence | Date |
|---|---|---|
| Patched NU7 wallet scan completed | Isolated source build accepted Testnet NU7. A full rescan of the copied sender from height 4,465,091 to 4,481,850 found no notes or balance. The faucet tx was not independently retrieved, so no payment was sent and the public gate remains unverified. [Gate record](PUBLIC_TESTNET_GATE.md). | Oct 9 |
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
| Public Testnet funding confirmed by faucet | Fauzec reported confirmed 1 TAZ shielded funding txid `689642767d2b428d15da7a3b7ad87d8f73fb6b67d218443ed2225b1853502494`; [gate record](PUBLIC_TESTNET_GATE.md). | Oct 4 |
| Public Testnet wallet sync blocked | Server tip exceeded NU7 activation height; Zingo PC 2.0.25-180 rejected consensus branch ID `0x77190ad9`. No sender-to-receiver payment or recipient observation is claimed. | Oct 4 |
| Public Testnet rerun unchanged | At tip 4,465,420, the same funded sender loaded, then sync rejected branch ID `0x77190ad9`; [rerun record](PUBLIC_TESTNET_GATE.md). | Oct 4 |
| New releases and alternates assessed; public gate still blocked | Zingo PC 2.0.26-194 lacks the active NU7 branch. Tagged Zkool and Vizor Windows releases also lack matching public Testnet support. The old sender wallet again failed sync at tip 4,466,265; [gate record](PUBLIC_TESTNET_GATE.md). | Oct 5 |
| CLI report v2 and clean checkout example | Wallet RPC outages produce `unverified` checks and a redacted report. Every check includes source, rerun steps, and boundary. A request-only sample catches the planted log leak while marking wallet checks unverified. | Oct 5 |
| Fresh public Testnet gate still blocked | Sender loaded at live server tip 4,468,118; sync rejected NU7 branch ID `0x77190ad9`. No payment was submitted. Published Zingo/Zallet releases were unchanged; [gate record](PUBLIC_TESTNET_GATE.md). | Oct 5 |
| Newest Zingo prerelease tested safely | Zingo PC 2.0.26-194 was checksum-verified and run against copied wallet files. It failed sync on the same NU7 branch at tips 4,468,170–4,468,179; original wallets stayed untouched and no send was attempted. | Oct 5 |
| Guarded M-03 regtest scenario passed | New 0.001 ZEC Ironwood tx `f5ca24f…e23ca` confirmed at height 130. Recipient-side recovery resolved an operation error without retrying; planted leak failed and clean idempotent rerun passed. Sending boundary review fixes passed 18 tests and a live no-send replay. [Evidence](EVIDENCE.md). | Oct 5 |
| M-04 QA gate passed | Fresh clone passed all 18 tests and the documented sample. All 13 revisions passed targeted secret and known-private-value scans; history is inside the build window; MIT license added. Authenticated rules/form confirm Core & Tooling and required submission assets. [QA report](QA_REPORT.md). | Oct 5 |

## Uncertainty and next action

The Oct 9 patched Zingo source build successfully scanned across NU7, eliminating the earlier branch-ID blocker. The copied sender wallet still showed zero balance after a full scan from its birthday through height 4,481,850. The faucet txid needs independent chain lookup and reconciliation before a payment can be attempted. See the latest [gate record](PUBLIC_TESTNET_GATE.md).

Public demo hosting passed on Oct 8: https://zec-privacy-test-kit.vercel.app/demo/. The stable URL loaded without sign-in and the hosted planted canary scan detected its marker. Public source is available at https://github.com/ShalyX/zec-privacy-test-kit. See [hosting notes](HOSTING.md). The two-minute video remains pending.

The browser evidence workbench is built in `demo/`: four recorded cases, schema v1/v2 report upload, evidence and reproduction disclosure, browser-local canary scan and redacted scan export. Desktop and 390 px layouts plus sample cases, report upload and planted/clean scan controls were verified on Oct 8. Public hosting and the repository URL are live; the video remains pending. This browser build did not rerun the public Testnet gate or reassess newer wallet releases.

M-01b is unverified. Fauzec reported funding confirmed, but the NU7-capable sender scan found no spendable note. The local regtest proof remains isolated; the required public sender-to-receiver transaction and recipient scan have not happened. Also inspect registered-only submission fields before final packaging.

**Next action:** reconcile the faucet txid with a public Testnet node and the sender's full scan, then complete [M-01b](PUBLIC_TESTNET_GATE.md) if a spendable note is confirmed. Finish M-05: produce the two-minute demo video and prepare the exact submission copy. The public demo and source repository are live; local Git history records the code and evidence slices.

Provisional remaining budget: up to 80 focused hours plus calendar buffer through Oct 28. Actual capacity is unknown. Backlog: hosted report viewer, multi-wallet adapters, additional privacy checks. No pending concept choice.
