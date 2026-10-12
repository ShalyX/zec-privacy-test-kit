# Requirements

Canonical direction: [project brief](PROJECT_BRIEF.md). Official event rules and authenticated submission form checked 2026-10-05 at [thezecathon.com](https://thezecathon.com/). Rewards and registration additionally confirmed by the user.

## User behavior

| ID | Flow | Observable acceptance criteria | Failure/recovery | Priority | Milestone | Proof |
|---|---|---|---|---|---|---|
| R-01 | Builder supplies a ZIP-321 URI or generated sample request. | Parser identifies network, amount, memo presence and recipient type; rejects malformed or unsupported inputs with a specific reason. | Invalid URI never starts a payment. | Required | M-02 | Valid/invalid standard vectors. |
| R-02 | Builder reviews privacy preflight. | Report flags transparent-only recipient and any payment identifiers exposed in the URI; distinguishes facts from inferred risks. | Unknown receiver format is `unknown`, never a privacy pass. | Required | M-02 | Shielded and transparent fixtures. |
| R-03a | Builder runs a local regtest payment scenario. | Sender submits a transaction to a separate receiver; recipient wallet observes a confirmed Ironwood note; evidence records txid and block confirmation without keys or memo contents. | Timeout/reorg/funding failure yields `unverified`, not `pass`; uncertain broadcast is looked up before retry. | Required | M-01a | [Verified local run](EVIDENCE.md). |
| R-03b | Builder runs a public Testnet payment scenario. | Same sender/receiver observation is repeated on current public Testnet and marked with the active network upgrade. | Regtest evidence and faucet funding alone cannot satisfy this row. | Required | M-01b/M-03 | [Passed Oct 12](PUBLIC_TESTNET_GATE.md): confirmed NU7 Ironwood txid and independent receiver note observation. |
| R-04 | Builder supplies app output/logs with unique synthetic canaries. | Kit finds a planted canary in a leaky log/output and reports the location without copying sensitive values into a public report. | No log supplied means `not tested`. | Required | M-03 | Red/green demo. |
| R-05 | Builder exports a report. | Every check has pass/fail/unverified, evidence source, reproduction steps, and explicit privacy boundary; public export is redacted by default. | Incomplete evidence is visibly marked. | Required | M-03 | Independent rerun and report review. |
| R-06 | Builder runs kit from a clean checkout. | Documented setup and sample work without mainnet money; no seed or spending key is committed or sent to an app server. | Missing tools/dependencies produce useful setup errors. | Required | M-04 | Clean-session QA and secret scan. |
| R-07 | Builder checks public-chain exposure for a Testnet receipt. | For the same canonical transaction, report transparent input/output counts and whether public net value balances span multiple shielded pools without exporting raw addresses or amounts. | Missing, conflicting, or unsupported explorer fields yield `unverified`; observed exposure yields `fail`. | Added | M-04 | [Public report](examples/public-testnet-report.json) and negative fixtures. |

## Competition compliance

| ID | Requirement | Official source | Planned artifact | Verification |
|---|---|---|---|---|
| C-01 | Entry in one track, one submission per account. | Event Rules / FAQ | Core & Tooling submission. | Inspect final entry. |
| C-02 | Code written during build window; libraries allowed, existing products not. | Event Rules / FAQ | New repository with clear dependency attribution and dated history. | Git history/license review. |
| C-03 | Open source at submission; a private repository made public by the deadline is allowed. | Event Rules / FAQ | Public MIT-licensed repository. | Open repository without sign-in and confirm the form checkbox. |
| C-04 | Submit by 2026-10-28 23:59 UTC. | Event schedule | Final entry before deadline. | Platform confirmation/receipt. |

The authenticated submission form requires a project name (64 characters maximum), exactly one track, a description (2,000 characters maximum), code repository URL, working demo URL, and a two-minute demo video URL. It warns that a private repository at the deadline will not be judged. Saving a draft after submission removes the submitted state until `SUBMIT` is used again.

## Judging evidence

| ID | Criterion; no published weights | Claim and required proof | Requirements |
|---|---|---|
| J-01 | Privacy | A real shielded transfer and a leak caught in an instrumented payment flow, with limits stated. | R-02–R-05 |
| J-02 | Usefulness | A builder can reproduce and act on the report. | R-01, R-05, R-06 |
| J-03 | Execution | Clean checkout, actual testnet integration, failure states and recorded result. | R-03, R-06 |
| J-04 | Originality | New event-window code and clear distinction from existing gateways/payout tools. | C-02, R-01–R-05 |

## Unresolved

- Final field values, public URLs, and submitted receipt remain for M-05/M-06. The field list and two-minute video constraint were verified inside the registered account on 2026-10-05.
- Kit adapters: Zallet 0.1.0-beta.3 plus Zebra 6.4.2 on local regtest; saved recipient exports from a patched Zingo build plus an independent public-chain snapshot on NU7 Testnet. The [public sender-to-receiver gate](PUBLIC_TESTNET_GATE.md) and [redacted report](examples/public-testnet-report.json) passed. The Zallet RPC adapter was not run on public Testnet.
- Network-level anonymity and leaks outside supplied surfaces are outside the verified claim.
