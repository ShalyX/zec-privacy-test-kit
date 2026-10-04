# ZEC privacy test kit — first runnable slice

A local CLI that checks a ZIP-321 payment request, verifies a received shielded note in a Zallet wallet, and scans supplied app logs for synthetic leak markers. It writes a redacted JSON report. It does not hold keys, submit payments, or claim to measure every privacy leak.

## Verified run

On 2026-10-04, Zebra 6.4.2 and Zallet 0.1.0-beta.3 ran on an isolated regtest chain with NU6.3 active. A sender shielded coinbase funds, sent **0.01 regtest ZEC** to a separate receiver wallet, and the receiver decrypted a confirmed **Ironwood** note. The txid is `286f97d8e1daaf629d7d766b033f0989c15d987892fc94b71a4d8ab4e9345b93`. The local chain cannot be queried outside this machine; [evidence notes](EVIDENCE.md) record the RPC observations.

The kit produced [a report with a planted leak](examples/sample-report.json) (`pass`, `pass`, `fail`) and [a clean control](examples/clean-report.json) (`pass`, `pass`, `pass`). Both checked the same real regtest payment. Public testnet validation is still pending.

## Run

Python 3.10+ and a running Zallet JSON-RPC endpoint are required for live observation. Keep Zallet bound to loopback. Put the receiver wallet's `user:password` in a private file outside the project; Zallet's RPC cookie file may also be used while it exists. Do not pass credentials, seed phrases, or private memos on the command line.

```sh
python3 ztestkit.py \
  --uri-file /private/payment-request.txt \
  --rpc-url http://127.0.0.1:50233 \
  --rpc-cookie /private/zallet-rpc-credentials.txt \
  --account-uuid YOUR_RECEIVER_ACCOUNT_UUID \
  --txid YOUR_TRANSACTION_ID \
  --canary-file examples/canaries.txt \
  --log examples/leaky-app.log \
  --report /private/report.json
```

For request checks without a wallet, omit the RPC, account, and txid flags. Address capability and receipt will then be `unverified` unless the address is transparently risky by syntax. A literal canary found in a supplied log is a `fail`; a clean file is a `pass` only for that file and those markers.

```sh
python3 -m unittest discover -s tests -v
```

## Report rules

- `pass`: the named observation was made, under the stated scope.
- `fail`: a concrete privacy problem or mismatched receive was detected.
- `unverified`: missing or incomplete evidence. It never counts as a privacy pass.

The exported report hashes request, address, account, and canary identifiers. It omits the request amount, memo, raw canary, keys, and viewing material. A testnet/regtest txid and confirmation count are included as evidence. Input files and Zallet RPC traffic remain local; the tool cannot detect leaks in surfaces it was not given.

This early parser covers ZEC ZIP-321 requests; required `req-` extensions, including custom assets, fail closed. Wallet RPC validation supplies address validity. The current CLI observes an already submitted transaction; transaction orchestration and public testnet proof are subsequent milestones.

Standards and runtime: [ZIP 321](https://zips.z.cash/zip-0321), [ZIP 316](https://zips.z.cash/zip-0316), [Zallet](https://github.com/zcash/zallet), [Zebra](https://github.com/ZcashFoundation/zebra).
