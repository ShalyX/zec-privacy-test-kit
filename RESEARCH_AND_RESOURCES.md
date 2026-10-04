# Research and builder resources

Last updated: 2026-10-04. Selection research was timeboxed to official Zcash specifications, live project evidence, and direct problem reports; it is not exhaustive market validation.

## User problems and alternatives

| ID | Observation and source | Evidence quality | Existing response and gap |
|---|---|---|---|
| P-01 | [ZIP 315 wallet guidance](https://github.com/zcash/zips/blob/main/zips/zip-0315.rst) warns that transparent-source shielding can link addresses and reveal a link to a recipient/viewing-key holder. | **Verified** protocol guidance; not a count of affected users. | Wallet policy can reduce the risk, but a builder still needs a reproducible integration check. |
| P-02 | [librustzcash issue #2845](https://github.com/zcash/librustzcash/issues/2845), opened July 2026, documented a transparent output whose displayed destination was a unified address; the issue is closed. | **Verified** specific software bug; not evidence it persists. | Upstream fix addresses that case. It demonstrates why checking displayed address alone is inadequate. |
| P-03 | A [60-person Zcash wallet usability study](https://arxiv.org/abs/2105.02793) found that only one quarter completed its real-world purchase task in the tested environment. | **Verified** historical study; current wallets may differ. | It supports testing the whole user flow, not a claim about present-day completion rates. |
| P-04 | A [merchant POS grant proposal](https://github.com/ZcashCommunityGrants/zcashcommunitygrants/issues/336) reports merchants unsure whether a wallet's apparent payment had reached them. | **Verified** first-hand account from the proposal authors; limited sample. | Payment processors focus on acceptance/settlement. This kit focuses on privacy leakage evidence, with transaction detection and confirmation kept distinct. |

**Product opening (inferred):** a small, local test kit that joins Zcash's protocol rules to app-level evidence. We have not established the number of teams who would adopt it. The reachable first audience is builders making Zcash payment requests, wallets, and checkout flows.

**Counterevidence:** [CipherPay](https://github.com/atmospherelabs-dev/cipherpay-api) covers shielded checkout, [ZPayroll](https://github.com/MageDee/ZPayroll/) covers payroll, [Glasspane](https://github.com/dolepee/glasspane) covers selective payout proof, and a [Unified Address Policy Engine proposal](https://github.com/ZcashCommunityGrants/zcashcommunitygrants/issues/197) addresses wallet policy. We must inspect overlap before final positioning; a generic gateway, payout proof, or address parser would not be differentiated.

## Official resource index

| Resource | Role | State on 2026-10-04 | Use / limitation |
|---|---|---|---|
| [ZECATHON site](https://thezecathon.com/) and [content file](https://thezecathon.com/darkpool/data.js) | Rules, tracks, schedule, criteria | Inspected | Privacy, usefulness, execution, originality; Core & Tooling target; original code and open-source submission. User confirmed registration/rewards. |
| [ZIP 321](https://zips.z.cash/zip-0321) | Payment request standard | Inspected | URI syntax, amount, memo, addresses and invalid cases; wallet compatibility can vary. |
| [ZIP 315](https://github.com/zcash/zips/blob/main/zips/zip-0315.rst) | Wallet privacy guidance | Inspected | Defines specific linkability checks and caution around transparent funds. |
| [ZIP 316](https://zips.z.cash/zip-0316) | Unified addresses | Inspected; wallet RPC exercised | `z_listunifiedreceivers` decoded the regtest UA; the actual receive chose Ironwood on the upgraded chain. |
| [zcash-devtool walkthrough](https://github.com/zcash/zcash-devtool/blob/main/doc/walkthrough.md) | Testnet wallet and PCZT example | Inspected, not run | Documents wallet setup, view-only scan, transaction construction and send. Rust is missing locally. |
| [lightwalletd](https://github.com/zcash/lightwalletd/blob/master/README.md) | Wallet chain interface | Inspected, not run | Can support testnet scanning; public endpoint availability must be verified. |
| [Zallet v0.1.0-beta.3 release](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.3) | Prebuilt Zcash wallet alternative | Linux amd64 artifact downloaded; published SHA-256 verified; two wallets ran in WSL | Completed local Ironwood receive. Public Testnet sync and funding remain unverified. |
| [Zebra v6.4.2 release](https://github.com/ZcashFoundation/zebra/releases/tag/v6.4.2) and [Z3 regtest guide](https://github.com/ZcashFoundation/z3/blob/main/docs/regtest.md) | Full node and local test setup | Binary SHA-256 verified; regtest mined and served RPC | Local chain made the real send/receive experiment possible without public Testnet sync. |
| [Zebra NU6.3 release note](https://zfnd.org/zebra-6-0-0-release/) | Current network protocol | Inspected | Ironwood is the active shielded pool and v6 format after the 2026 Testnet/Mainnet activations; proof targets this path. |

Uninspected: organizer-linked workshops, any registered-only submission brief, faucet limits, precise SDK versions/licenses, and current Zcash testnet service reliability. No credentials have been collected or stored.

## Assumptions and feasibility risks

| Assumption | Status | Smallest test | Consequence if false |
|---|---|---|---|
| We can fund and send one genuine shielded payment. | **Verified on local regtest** with a separate receiver and confirmed Ironwood note. Public Testnet remains unverified. | M-01b repeats this on public Testnet. | Revise external claim before submission if public path cannot be proven. |
| We can distinguish the actual transparent/shielded path from a UI label. | **Verified for the local transaction:** wallet reported transparent coinbase spend and later Ironwood receive. Transparent-recipient bad flow remains unrun. | Compare actual transaction/recipient evidence in a seeded transparent recipient case. | Narrow claim or change concept. |
| Local canary scanning can catch app-level leaks without storing secrets. | **Verified for a literal synthetic marker** in a supplied log, with clean control and redacted report. | Expand to realistic app output and review false positives. | Narrow claim to literal supplied-file checks. |
