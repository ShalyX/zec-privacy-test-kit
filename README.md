# ZEC privacy test kit

[![Tests](https://github.com/ShalyX/zec-privacy-test-kit/actions/workflows/test.yml/badge.svg)](https://github.com/ShalyX/zec-privacy-test-kit/actions/workflows/test.yml)

A local CLI that checks a ZIP-321 payment request, verifies a received shielded note in a Zallet wallet, and scans supplied app logs for synthetic leak markers. It writes a redacted JSON report. The read-only report command does not hold keys or submit payments, and the kit does not claim to measure every privacy leak.

[Live evidence workbench](https://zec-privacy-test-kit.vercel.app/demo/) · [Source repository](https://github.com/ShalyX/zec-privacy-test-kit)

`scenario_runner.py` adds a regtest-only payment path for builders who already run separate sender and receiver Zallet wallets plus Zebra. It submits with `FullPrivacy`, mines one local block, waits for recipient observation, and invokes the same report engine. A private checkpoint makes reruns idempotent.

## Verified run

On 2026-10-04, Zebra 6.4.2 and Zallet 0.1.0-beta.3 ran on an isolated regtest chain with NU6.3 active. A sender shielded coinbase funds, sent **0.01 regtest ZEC** to a separate receiver wallet, and the receiver decrypted a confirmed **Ironwood** note. The txid is `286f97d8e1daaf629d7d766b033f0989c15d987892fc94b71a4d8ab4e9345b93`. The local chain cannot be queried outside this machine; [evidence notes](EVIDENCE.md) record the RPC observations.

The kit produced [a report with a planted leak](examples/sample-report.json) (`pass`, `pass`, `fail`) and [a clean control](examples/clean-report.json) (`pass`, `pass`, `pass`). Both checked the same real regtest payment. A second real transaction to a transparent receiver produced [a transparent failure report](examples/transparent-fail-report.json) (`fail`, `fail`, `pass`); Zebra exposed the 0.005 ZEC output amount and receiver address in `getrawtransaction`. [Public Testnet validation](PUBLIC_TESTNET_GATE.md) was attempted and remains unverified because the available wallet could not scan the active NU7 chain.

## Run

### Browser demo

Open the [public evidence workbench](https://zec-privacy-test-kit.vercel.app/demo/). [Hosting notes](HOSTING.md) record the deployed version and verification.

From the repository root, run `python -m http.server 8765 --bind 127.0.0.1`, then open [the local workbench](http://127.0.0.1:8765/demo/). The static demo displays the recorded shielded, planted-leak, transparent, and request-only CLI reports. It accepts schema v1/v2 JSON reports and scans pasted or uploaded UTF-8 logs for synthetic canaries in the browser. The scan export contains marker hashes and line numbers, without the raw log or markers. It uses no external assets, analytics, wallet connection, or upload API. Serve over localhost or HTTPS for SHA-256 support.

The demo displays supplied wallet evidence; it does not independently repeat wallet observations. Browser scans test only supplied text. Public Testnet remains unverified. See [demo notes](demo/README.md) for packaging and verification.

Python 3.10+ and a running Zallet JSON-RPC endpoint are required for live observation. Keep Zallet bound to loopback. Put the receiver wallet's `user:password` in a private file outside the project; Zallet's RPC cookie file may also be used while it exists. Do not pass credentials, seed phrases, or private memos on the command line.

From a clean checkout, run the request and log checks without a wallet:

```sh
python3 ztestkit.py --uri-file examples/sample-request.txt \
  --canary-file examples/canaries.txt --log examples/leaky-app.log \
  --network testnet --report request-only-report.json
```

This writes a report with a detected synthetic leak. The sample address is a ZIP-321 test vector, so receiver capability and payment receipt remain `unverified`. The command neither sends a payment nor proves public Testnet operation. An [example output](examples/request-only-report.json) is included.

### Complete local scenario

The scenario runner is deliberately limited to regtest and plain loopback HTTP RPC. Before it touches the sender wallet, it verifies Zebra's regtest genesis block and rejects remote, credential-bearing, or malformed RPC URLs. Put the sender Unified Address and recipient account UUID in private files outside the repository. Keep the payment request private when it contains real metadata.

```sh
python3 scenario_runner.py \
  --uri-file /private/payment-request.txt \
  --source-address-file /private/source-address.txt \
  --sender-rpc-url http://127.0.0.1:50232 \
  --sender-rpc-cookie /private/sender-rpc-cookie \
  --recipient-rpc-url http://127.0.0.1:50233 \
  --recipient-rpc-cookie /private/receiver-rpc-cookie \
  --recipient-account-file /private/recipient-account.txt \
  --node-rpc-url http://127.0.0.1:29232 \
  --checkpoint /private/scenario-checkpoint.json \
  --canary-file examples/canaries.txt \
  --log examples/leaky-app.log \
  --report /private/scenario-report.json
```

Keep the same checkpoint when resuming. The runner writes a `submission_started` checkpoint before the wallet call. A saved txid is observed without another wallet call; a saved operation ID is polled without another send. An interrupted or ambiguous submission cannot retry automatically. If submission returns an error but a transaction appears in the mempool, first prove that the recipient wallet decrypted the expected shielded note, then rerun with `--recover-txid TXID`. The runner rejects recovery when the recipient and amount do not match.

The verified M-03 run produced [a planted-leak report](examples/m03-leaky-report.json) and [a clean rerun](examples/m03-clean-report.json) from transaction `f5ca24f4c2fff2d9fe67c7f547a3b57c2e6013a748393e6ada99fa32f39e23ca`. These are local regtest artifacts.

```sh
python3 ztestkit.py \
  --uri-file /private/payment-request.txt \
  --rpc-url http://127.0.0.1:50233 \
  --rpc-cookie /private/zallet-rpc-credentials.txt \
  --account-uuid YOUR_RECEIVER_ACCOUNT_UUID \
  --txid YOUR_TRANSACTION_ID \
  --network regtest \
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

Exit codes: `0` all checks pass, `1` at least one check fails, `3` no failures but at least one check is unverified, `2` invalid input or an operational error. Reports are still written for `1` and `3` so CI can preserve evidence. Wallet RPC observation errors are reported as `unverified`; invalid local inputs remain exit `2`.

The exported report hashes request, address, account, and canary identifiers. It omits the request amount, memo, raw canary, raw log filename, keys, and viewing material. A testnet/regtest txid and confirmation count are included as evidence. Each check states its evidence source, rerun steps, and privacy boundary. `--network` is recorded as an operator assertion. Input files and Zallet RPC traffic remain local; the tool cannot detect leaks in surfaces it was not given. Existing regtest reports in `examples/` use schema version 1; new runs use version 2.

This parser covers ZEC ZIP-321 requests; required `req-` extensions, including custom assets, fail closed. Wallet RPC validation supplies address validity. The core `ztestkit.py` command remains read-only; `scenario_runner.py` is the explicit regtest-only sender. Public Testnet proof remains blocked by wallet NU7 support.

Standards and runtime: [ZIP 321](https://zips.z.cash/zip-0321), [ZIP 316](https://zips.z.cash/zip-0316), [Zallet](https://github.com/zcash/zallet), [Zebra](https://github.com/ZcashFoundation/zebra).

## License

[MIT](LICENSE) © 2026 ElseMade.
