# Architecture

Linked [brief](PROJECT_BRIEF.md), [requirements](REQUIREMENTS.md), and [resource research](RESEARCH_AND_RESOURCES.md). The first local transaction is recorded in [evidence](EVIDENCE.md); the confirmed public NU7 Testnet run is recorded in the [gate](PUBLIC_TESTNET_GATE.md) and [redacted report](examples/public-testnet-report.json).

## System

```text
ZIP-321 request ─→ request parser / privacy preflight ─┐
                                                        ├─→ check engine ─→ redacted report
test wallet ─→ Zcash send ─→ recipient wallet scan ─────┤
                                                        │
optional synthetic app logs ─→ local canary scanner ────┘
```

- **CLI-first runner:** Python standard-library CLI accepts a request, recipient wallet RPC or saved Zingo evidence, and optional log path; it writes a local JSON report. The browser workbench displays supplied reports.
- **Request parser:** uses standard ZIP-321 handling and Zcash address parsing rather than string prefixes alone. It records requested network, amount, memo presence, and receiver capabilities.
- **Wallet adapters:** `ztestkit.py` uses read-only Zallet JSON-RPC over loopback or saved Zingo addresses, notes, and height JSON exports. The Zingo path also checks an operator-supplied public-chain snapshot. The wallet retains spending authority; the kit writes only sanitized observations. A separate recipient wallet confirms receipt.
- **Regtest scenario runner:** `scenario_runner.py` is the explicit sending boundary. It accepts private values through files, rejects non-loopback RPC, verifies the regtest genesis block before touching the sender wallet, requires a wallet-validated shielded recipient, submits with `FullPrivacy`, mines one local block, and feeds the resulting txid into the read-only report engine.
- **Submission checkpoint:** records only request hash, state, operation ID and txid. It writes the pre-call `submission_started` state atomically, reuses saved txids, polls saved operations without consuming their result, and blocks retries after ambiguous transport or operation outcomes. Recovery requires the separate recipient wallet to decrypt a matching shielded output before the checkpoint can bind to a txid.
- **Observation adapter:** records txid, block/confirmation state, public transparent outputs when available, and recipient wallet's received-note observation. A txid alone cannot prove a shielded payment's recipient or amount.
- **Canary scanner:** scans only files the builder explicitly supplies for synthetic order IDs, addresses, and memo markers. Report exports include hashes/locations or redacted snippets, never raw seeds, full viewing keys, or private memo values.

Zcash integration is essential: ZIP-321 inputs, Zcash receiver semantics, a real shielded transfer, and wallet scan evidence. The local regtest path and separate public NU7 Testnet gate have both passed. The kit does not substitute a simulated transaction for either path.

## Data and privacy boundaries

Run states: `configured → preflighted → submitted → observed → confirmed → reported`; `failed` and `unverified` are explicit terminal states. Retry must never blindly resend after uncertain broadcast; look up the wallet's operation/tx state first. Reports record which checks were not run.

Wallet seeds and spend keys remain in a local test wallet under `work/` during development and must be Git-ignored. No keys in source, logs, exported reports, browser storage, or hosted backend. Do not use mainnet funds. A public report can show a testnet txid and check results, with canaries redacted.

## Runtime and deployment

Runtime: Python 3.10+ CLI. Official Zebra and Zallet Linux binaries under WSL supplied the local regtest proof. An isolated patched Zingo build supplied the public NU7 Testnet proof. The read-only browser demo and source are public; the CLI runs from a clean documented checkout.

Unknowns: compatibility of unpatched wallet releases with active NU7 Testnet, and wallet-version behavior for Unified Address validation. Network privacy, remote RPC metadata exposure, and off-device logs are outside the kit's guarantee unless explicitly tested.

## Technical decisions

| Date | Decision | Reason / impact |
|---|---|
| 2026-10-04 | CLI-first and local-only for core flow. | Keeps secrets out of a web service and makes automated reruns possible; visual polish follows demonstrated behavior. |
| 2026-10-04 | Separate `pass`, `fail`, and `unverified`; no universal privacy score. | Prevents a partial test from claiming comprehensive anonymity. |
| 2026-10-04 | Local regtest proof first; public Testnet receipt remains mandatory. | Verified the core path without pretending the isolated chain is public evidence. |
| 2026-10-04 | Python standard-library CLI with Zallet read-only RPC. | The official Rust host was unreachable; Zallet and Zebra release binaries worked in WSL. |
| 2026-10-05 | Separate guarded regtest sender from the read-only report engine. | Keeps the default command non-spending while enabling a reproducible full scenario. Checkpoints and recipient-side recovery prevent blind duplicate sends. |
