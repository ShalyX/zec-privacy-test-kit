# Browser evidence workbench

Static HTML, CSS, and JavaScript. No package install or build step. Serve the repository root with `python -m http.server 8765 --bind 127.0.0.1` and open `http://127.0.0.1:8765/demo/`.

The four bundled JSON files are exact copies of the corresponding committed CLI evidence in `examples/`. Keep them synchronized when updating examples. Request-only evidence does not establish a wallet receipt; the transparent report uses schema v1 and lacks reproduction metadata, which the interface explicitly marks as absent.

Report upload validates schema version, check names, statuses, evidence objects when present, and limits. Files are limited to 2 MB. Display uses text nodes rather than injected HTML. Uploaded reports are labeled as supplied evidence. The original report can be downloaded; that preserves its contents rather than applying additional redaction.

The canary scan deduplicates trimmed nonempty markers, matches them literally per line, and exports SHA-256 hashes with file index and line number. Use up to 100 synthetic markers and a UTF-8 log under 2 MB. Values stay in page memory; there is no persistence or upload endpoint. SHA-256 needs localhost or HTTPS. Only supplied text is covered; it is not a wallet or network privacy test.

Verified 2026-10-08 in the Codex browser: all four case selections, real schema v2 report upload, planted marker failure at line 2, clean control pass, redacted evidence display, and desktop/narrow visual inspection at 390 px with no horizontal overflow. No browser console errors were observed. Public hosting and a two-minute video remain pending.

For static hosting, publish the repository's public files with `/demo/` as the demo entry. The setup guide link currently points to `../README.md`; preserve that path or replace it with the public repository URL when publishing.
