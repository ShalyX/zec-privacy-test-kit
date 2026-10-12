# Public browser demo

Published 2026-10-08; updated 2026-10-12: https://zec-privacy-test-kit.vercel.app/demo/

Vercel project: `zec-privacy-test-kit`, ID `prj_P3jDWCNxLIKhNLzuwkucqvePt0gQ`, team `shalyxs-projects`. Current production deployment ID: `dpl_2mF8UG5mw3jQsUFfQAjXmbYnKjd3`. Vercel reported `READY` and assigned the stable alias `zec-privacy-test-kit.vercel.app`.

Published payload: the `demo/` static files and `vercel.json` root redirect to `/demo/`. The setup guide links to the public GitHub README. Wallet files, credentials, private working data and Git metadata were excluded.

Public source: https://github.com/ShalyX/zec-privacy-test-kit

Browser verification: the stable public URL loaded without sign-in; the shielded report displayed three passes; the browser-local planted canary scan found one marker location and displayed a failure. No wallet connection or transaction was attempted in the browser. The separate [public Testnet payment gate](PUBLIC_TESTNET_GATE.md) passed on October 12 with a patched wallet build.

Pre-recording review on October 12 found stale Testnet copy and a setup-guide 404. The current deployment labels the public NU7 payment as separate wallet evidence and links to its gate record. The setup guide goes to GitHub. The root URL returns a 307 redirect to `/demo/`; `/demo/` returns 200. All 18 CLI tests passed with normal Windows temporary-file access. The browser's recorded leak case and planted local scan both produced the expected failure.

Next submission assets: two-minute video, final description and receipt.
