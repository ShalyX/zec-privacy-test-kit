# M-01 local regtest evidence

Recorded 2026-10-04. This is **local regtest**, not public Testnet. The chain state and disposable wallet data remain under `work/regtest/`, outside this deliverable. No secret or mnemonic is included here.

## Environment

- Zebra `6.4.2` Linux binary and Zallet `0.1.0-beta.3` Linux amd64 binary; release SHA-256 checks matched their official listings before execution.
- Zebra regtest activation heights: Canopy at 1; NU5, NU6, NU6.1, NU6.2, and NU6.3 at 2. Zebra `getblockchaininfo` showed height 2 after the initial generation; Zallet reported matching consensus rules.
- Two independently generated Zallet wallets: sender and receiver. Their private data stays under `work/regtest/`.

## Actual transaction path

1. Zebra mined to a sender wallet transparent receiver. `getaddressutxos` showed coinbase outputs at that address. After block 106, Zallet reported spendable coinbase funds.
2. Sender called `z_shieldcoinbase` for one 6.25 ZEC coinbase output. Operation `opid-6c2ea66b-64e0-43a9-b0dc-b1f242ac4cc0` reported a transport error during commit, but Zebra's mempool contained txid `3b208649c633c42ea4982152e9a799d44d550a96306fce2818eb95d7b805d5e7`. We did not retry the send. After mining, Zebra showed one confirmation and sender `z_viewtransaction` showed a 6.24985 ZEC Ironwood output and a 0.00015 ZEC fee.
3. After ten further blocks, sender called `z_sendmany` for 0.01 ZEC to the receiver's Unified Address. Operation `opid-e55f081f-4fc4-49d5-b6d8-97ae8d7011bd` succeeded and returned txid `286f97d8e1daaf629d7d766b033f0989c15d987892fc94b71a4d8ab4e9345b93`.
4. Zebra mined txid `286f…5b93` in block `5657a5191ca71910dd1321e2e90619ed1a980735c3144b1920abb61782456853` at height 118. The receiver wallet matched node tip 118 and `z_viewtransaction` reported `status: mined`, `confirmations: 1`, one incoming Ironwood output for its account, `valueZat: 1000000` (0.01 ZEC). The receiver wallet's `spends` list for this transaction was empty.
5. `ztestkit.py` checked the same request and txid through receiver RPC. The planted `ORDER-DEMO-7F3C9A` in `examples/leaky-app.log` was detected at line 2; `examples/clean-app.log` had no hit. The [leaky report](examples/sample-report.json) and [clean report](examples/clean-report.json) contain hashes and outcomes without raw marker values.

## Limits and next gate

Zallet's `z_getaddressforaccount` response listed Orchard, Sapling, and transparent receivers, while the confirmed receive was Ironwood. Its `validateaddress` returned `isvalid: false` for that freshly generated regtest Unified Address, although `z_listunifiedreceivers` decoded it and the payment succeeded. The kit therefore validates Unified Addresses with `z_listunifiedreceivers` before falling back to `validateaddress` for other types. This behavior needs additional wallet-version checks.

The local run proves the transaction and receiver observation path and the seeded log leak detection. It does not prove public Testnet compatibility, a clean setup on another machine, or protection against leaks outside supplied logs. Public Testnet is the remaining R-03 gate; NU7 activation on public Testnet is scheduled around 2026-10-06, so that run should use current binaries and record the active upgrade.
