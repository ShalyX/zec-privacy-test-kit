# M-01b public Testnet validation gate

## NU7 source-build rerun - 2026-10-09

**Result: unverified.** An isolated Zingo CLI source build accepted the active NU7 Testnet branch and completed a full sender-wallet scan, but found no funded note. No payment was proposed or broadcast.

The build used Zingo `zingolib_v6.0.0` at commit `c6381534f802b1022041beda4b01c106ad132329`, with the Testnet NU7 backport from ZECKED commit `b247aaa7797b731a375aa97b7fa0fe9722df586d`. The patched `zcash_protocol` tests passed **36/36**. The CLI was built in the private work directory with Rust 1.97.1 and `clearnet-test-mode`; requests to `https://testnet.zec.rocks:443` exposed this machine's IP to that indexer. The build did not change the product repository or original wallet files.

The sender wallet was copied into a separate data directory. Its derived address matched the address submitted to Fauzec, and the original wallet file's hash stayed unchanged. The first successful sync reached wallet height **4,481,818** but showed no notes, transactions, or balance. To rule out a stale saved scan checkpoint, the copied wallet was backed up, cleared, and scanned again from its recorded birthday **4,465,091** through **4,481,850**. The rescan reported **16,760 blocks**, **226 Sapling**, **20 Orchard**, and **33,594 Ironwood** outputs, with **100%** of reported outputs scanned. All pool balances remained zero.

The faucet's earlier `confirmed` status and txid remain faucet evidence only. This run did not independently retrieve that raw transaction or establish why the wallet found no note. A read-only transaction lookup was being built when the environment changed and blocked WSL access; the lookup did not produce a result. The funded sender is therefore **not** considered spendable. The separately created receiver was not used, and R-03b remains open.

Next gate: retrieve the faucet transaction from a public Testnet node and inspect its height and output pools; reconcile it with the sender address and wallet scan. Only after a confirmed spendable note appears should the small sender-to-receiver payment and separate recipient observation proceed. Private wallet files, seeds, and full addresses remain outside this repository.

## Fresh validation — 2026-10-08, approximately 02:15–02:17 UTC

**Result: unverified.** The existing isolated Zingo PC 2.0.26-194 wallet copy loaded and launched sync against `https://testnet.zec.rocks:443`. The second poll returned `sync_failed`, recovery `server_unavailable`, with reason `server error ← server returned invalid transaction. invalid consensus branch id 0x77190ad9`. The server subsequently reported height **4,476,858**. No spendable balance was established, no sender-to-receiver payment was constructed or broadcast, and no recipient confirmation was observed. Faucet status was not rechecked in this run.

The official release API now lists [Zingo PC 2.0.26-195](https://github.com/zingolabs/zingo-pc/releases/tag/zingo-pc-2.0.26-195), published October 6. Its tagged `native/Cargo.lock` still pins `zcash_protocol` 0.10.6. This version was inspected at source level only, not executed; the runtime result above applies to build 194. Zallet's latest published release remains v0.1.0-beta.3.

[Upstream issue #2859](https://github.com/zingolabs/zingolib/issues/2859) remains open. An October 7 contributor comment describes a source patch enabling NU7, setting Testnet activation to 4,465,026 and branch ID to `0x77190ad9`, and reports a mined transaction using that patched build. This is third-party evidence, not validation of this kit. The next concrete route is to review and reproduce that patch in an isolated source build, prove sync and funding observation on wallet copies, then perform the separate-recipient payment gate. No seeds or wallet files were shared with the contributor or added to this repository.

Attempted **2026-10-04, 19:14–19:34 UTC**. Result: **unverified / blocked by wallet compatibility**. This is not a public payment pass.

## Network and funding observations

- The public lightwalletd endpoint `https://testnet.zec.rocks:443` returned a tip at heights **4,465,191–4,465,195** during the run. [ZIP 259](https://zips.z.cash/zip-0259) sets NU7 Testnet activation at height **4,465,026** and its consensus branch ID to **`0x77190AD9`**. The observed tip was therefore already past activation, earlier than the Foundation's approximate October 6 calendar estimate.
- Two independent Testnet wallets were created in an isolated local work directory using the native module from [Zingo PC 2.0.25-180](https://github.com/zingolabs/zingo-pc/releases/tag/zingo-pc-2.0.25-180). Their seed phrases and wallet files are not included in this repository.
- [Fauzec](https://fauzec.com/) accepted a shielded 1 TAZ claim for the sender's Unified Address. Request `01M446323S1E1NXP79GVK2TR7C` subsequently returned `state: confirmed`, `outcome: accepted`, txid **`689642767d2b428d15da7a3b7ad87d8f73fb6b67d218443ed2225b1853502494`**. This is faucet status, not independent recipient-wallet observation. The full receiving address is omitted from this report.

## Blocking observation

The Zingo wallet loaded and reached the public server, but its sync failed with:

```text
sync: server error. server returned invalid transaction. invalid consensus branch id 0x77190ad9
```

The wallet's lockfile uses `zcash_protocol` 0.10.0 and a 0.10.1 development revision. The newer Zingo PC 2.0.26-193 prerelease was inspected from its release source: its lockfile uses `zcash_protocol` 0.10.5, whose [published changelog](https://docs.rs/crate/zcash_protocol/0.10.5/source/CHANGELOG.md) has no NU7 entry. This suggests the prerelease also lacks the active branch ID; it was **not** executed, so this remains an inference. The decisive observation is the actual sync error above. [Zebra's NU7 release note](https://zfnd.org/zebra-7-0-0-rc-0-nu7-arrives-on-testnet/) also calls out a database format change requiring matching Zallet/Zaino builds, so the older local Zebra/Zallet pair is not a valid public Testnet substitute.

## Pass condition and rerun

R-03b stays open. The confirmed faucet transaction only funds the sender. A pass requires an NU7-compatible wallet to scan that note, submit a small shielded payment from this sender to the separately created receiver, then show the receiver's confirmed incoming note and matching txid. Record wallet version, live tip, branch ID, amount, confirmation, and a redacted report. Treat a broadcast without receiver observation as `unverified`; look up an uncertain tx before retrying.

The local wallet files and claim response remain in `work/zingo-pc/` outside the deliverable. Do not add seeds, wallet files, or full addresses to Git. No second faucet claim is needed while this funded sender is recoverable.

## Rerun — 2026-10-04, 21:17 UTC

The faucet still reported the funding txid above as `confirmed`. The public lightwalletd tip had advanced to **4,465,420**. The same sender wallet loaded successfully, but a fresh sync returned the same `invalid consensus branch id 0x77190ad9` error. As of this rerun, the latest published Zingo PC stable release was 2.0.25-180 and the latest Zallet release was 0.1.0-beta.3; no compatible replacement was identified. No new payment was submitted. **R-03b remains unverified.**

## Rerun — 2026-10-05, 01:43 UTC

The faucet still reported the funding txid as `confirmed`. The Testnet server tip advanced from **4,466,000** to **4,466,265** during this check. The funded sender wallet loaded, but sync again rejected consensus branch ID `0x77190ad9`.

A newer [Zingo PC 2.0.26-194 prerelease](https://github.com/zingolabs/zingo-pc/releases/tag/zingo-pc-2.0.26-194) had appeared since the prior run. Its tagged `native/Cargo.lock` pins `zcash_protocol` **0.10.6**. In that published crate's `consensus.rs`, NU7 is behind the `zcash_unstable = "nu7"` compile setting, the public Testnet activation height is `None`, and the NU7 branch ID is still the placeholder `0xffffffff`. The tagged Zingo source does not enable that compile setting. This source-based compatibility assessment was later confirmed by the runtime check below. The latest Zallet release remained 0.1.0-beta.3. No sender-to-receiver payment was submitted. **R-03b remains unverified.**

Two other published Windows wallet lines were checked from their tagged source before attempting to import any seed. [Zkool 6.31.0](https://github.com/hhanh00/zkool2/releases/tag/zkool-v6.31.0) pins a ZSA fork of `zcash_protocol` whose NU7 branch ID is `0x77190ad8`, while public Testnet NU7 activation is `None`. [Vizor 0.0.59](https://github.com/chainapsis/vizor-wallet/releases/tag/release/v0.0.59) publishes a Testnet installer, but its `rust/src/wallet/network.rs` explicitly leaves proposed NU7 inactive on Mainnet and Testnet. Neither tagged build matches the active public branch `0x77190ad9`, so neither was given the funded sender's seed. This is a source-based exclusion, not a runtime result.

## Fresh gate run — 2026-10-05, 17:30–17:32 UTC

The existing funded sender wallet loaded against `https://testnet.zec.rocks:443` after one transient gRPC transport error. The live server tip was **4,468,118**, well past NU7 activation. The wallet launched sync, then returned the same runtime error: `invalid consensus branch id 0x77190ad9`. It did not reach a trustworthy balance or spendable state. No sender-to-receiver transaction was attempted or broadcast, and no recipient observation was made. **R-03b remains unverified.**

The GitHub release API was checked during this run: the newest published Zingo PC release was still [2.0.26-194](https://github.com/zingolabs/zingo-pc/releases/tag/zingo-pc-2.0.26-194), and the newest published Zallet release was still [v0.1.0-beta.3](https://github.com/zcash/zallet/releases/tag/v0.1.0-beta.3). [Zebra v7.0.0-rc.0](https://github.com/ZcashFoundation/zebra/releases/tag/v7.0.0-rc.0) supports NU7 nodes, but it is not a replacement for a compatible wallet. The latest Zingo build's source-based NU7 incompatibility finding above still applies. Do not retry a send with this wallet until it can scan the active branch; then verify the funded note before constructing a payment.

## Zingo 2.0.26-194 isolated runtime check — 2026-10-05

The official Windows x64 portable archive was downloaded from the prerelease and its SHA-256 matched GitHub's published digest: `a168f7e1a6bc6f6c5a325982c1ade4070b6284b8b3fbbb6af2a208a65ddbc6b3`. Its native wallet module was run against copies of `sender.dat` and `receiver.dat` in a separate local directory; the original wallet files were not opened by this build.

The copied sender loaded and started sync while the server tip advanced from **4,468,170 to 4,468,179**. It returned `sync_failed` with `invalid consensus branch id 0x77190ad9`. No trustworthy balance was established and no payment was constructed or broadcast. Upstream [zingolib issue #2859](https://github.com/zingolabs/zingolib/issues/2859) independently records the same post-NU7 failure and remained open during this check. Zallet's upstream [NU7 support issue #890](https://github.com/zcash/zallet/issues/890) and [Testnet support issue #891](https://github.com/zcash/zallet/issues/891) were also open. There is currently no published compatible wallet build in the checked lines. **R-03b remains unverified.**
