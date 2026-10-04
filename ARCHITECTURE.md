# Architecture

Linked [brief](PROJECT_BRIEF.md), [requirements](REQUIREMENTS.md), and [resource research](RESEARCH_AND_RESOURCES.md). The first local transaction is recorded in [evidence](EVIDENCE.md); public Testnet remains to be verified.

## System

```text
ZIP-321 request ─→ request parser / privacy preflight ─┐
                                                        ├─→ check engine ─→ redacted report
test wallet ─→ Zcash send ─→ recipient wallet scan ─────┤
                                                        │
optional synthetic app logs ─→ local canary scanner ────┘
```

- **CLI-first runner:** Python standard-library CLI accepts a request, recipient wallet RPC observation, and optional log path; it writes a local JSON report. A polished UI is optional after the end-to-end run works.
- **Request parser:** uses standard ZIP-321 handling and Zcash address parsing rather than string prefixes alone. It records requested network, amount, memo presence, and receiver capabilities.
- **Wallet adapter:** read-only Zallet JSON-RPC over loopback. The wallet retains spending authority; the kit consumes validated address information, sync state, and sanitized transaction observations. A separate recipient wallet confirms receipt. This first slice does not submit transactions.
- **Observation adapter:** records txid, block/confirmation state, public transparent outputs when available, and recipient wallet's received-note observation. A txid alone cannot prove a shielded payment's recipient or amount.
- **Canary scanner:** scans only files the builder explicitly supplies for synthetic order IDs, addresses, and memo markers. Report exports include hashes/locations or redacted snippets, never raw seeds, full viewing keys, or private memo values.

Zcash integration is essential: ZIP-321 inputs, Zcash receiver semantics, a real shielded transfer, and wallet scan evidence. The local regtest path is verified; public Testnet remains a separate gate. The kit must not substitute a simulated transaction for that path.

## Data and privacy boundaries

Run states: `configured → preflighted → submitted → observed → confirmed → reported`; `failed` and `unverified` are explicit terminal states. Retry must never blindly resend after uncertain broadcast; look up the wallet's operation/tx state first. Reports record which checks were not run.

Wallet seeds and spend keys remain in a local test wallet under `work/` during development and must be Git-ignored. No keys in source, logs, exported reports, browser storage, or hosted backend. Do not use mainnet funds. A public report can show a testnet txid and check results, with canaries redacted.

## Runtime and deployment

Initial runtime: Python 3.10+ CLI, with the official Zebra and Zallet Linux binaries running under WSL for the local proof. Rust was unavailable on this machine. Final public artifact should run from a clean documented checkout; a hosted read-only sample report may be added only after the core flow works. Judges need a concise quickstart and a recorded public Testnet run.

Unknowns: public Testnet funding and sync, behavior across the coming NU7 Testnet activation, and wallet-version behavior for Unified Address validation. Network privacy, remote RPC metadata exposure, and off-device logs are outside the kit's guarantee unless explicitly tested.

## Technical decisions

| Date | Decision | Reason / impact |
|---|---|
| 2026-10-04 | CLI-first and local-only for core flow. | Keeps secrets out of a web service and makes automated reruns possible; visual polish follows demonstrated behavior. |
| 2026-10-04 | Separate `pass`, `fail`, and `unverified`; no universal privacy score. | Prevents a partial test from claiming comprehensive anonymity. |
| 2026-10-04 | Local regtest proof first; public Testnet receipt remains mandatory. | Verified the core path without pretending the isolated chain is public evidence. |
| 2026-10-04 | Python standard-library CLI with Zallet read-only RPC. | The official Rust host was unreachable; Zallet and Zebra release binaries worked in WSL. |

