# M-01b public Testnet validation gate

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

A newer [Zingo PC 2.0.26-194 prerelease](https://github.com/zingolabs/zingo-pc/releases/tag/zingo-pc-2.0.26-194) had appeared since the prior run. Its tagged `native/Cargo.lock` pins `zcash_protocol` **0.10.6**. In that published crate's `consensus.rs`, NU7 is behind the `zcash_unstable = "nu7"` compile setting, the public Testnet activation height is `None`, and the NU7 branch ID is still the placeholder `0xffffffff`. The tagged Zingo source does not enable that compile setting. This is a source-based compatibility assessment; the new binary was not run. The latest Zallet release remained 0.1.0-beta.3. No sender-to-receiver payment was submitted. **R-03b remains unverified.**

Two other published Windows wallet lines were checked from their tagged source before attempting to import any seed. [Zkool 6.31.0](https://github.com/hhanh00/zkool2/releases/tag/zkool-v6.31.0) pins a ZSA fork of `zcash_protocol` whose NU7 branch ID is `0x77190ad8`, while public Testnet NU7 activation is `None`. [Vizor 0.0.59](https://github.com/chainapsis/vizor-wallet/releases/tag/release/v0.0.59) publishes a Testnet installer, but its `rust/src/wallet/network.rs` explicitly leaves proposed NU7 inactive on Mainnet and Testnet. Neither tagged build matches the active public branch `0x77190ad9`, so neither was given the funded sender's seed. This is a source-based exclusion, not a runtime result.
