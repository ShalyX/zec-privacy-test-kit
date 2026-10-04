# ZECATHON project brief: Zcash payment privacy test kit

Idea status: **locked by the user on 2026-10-04**. Working name only; public identity is undecided.

Target: [ZECATHON](https://thezecathon.com/), **Core & Tooling** track. The public schedule lists a $15,000 track award and a $20,000 overall award on top; the user has confirmed the rewards and completed registration. The submission deadline is **2026-10-28 23:59 UTC** (2026-10-29 00:59 Africa/Lagos).

## Locked direction

- **User and problem:** Zcash app and wallet builders need to know whether an intended private payment flow leaks addresses, amounts, identifiers, or sensitive metadata through the request, transaction path, application output, or logs. Zcash wallet guidance documents linkability risks from transparent inputs; a recent wallet issue shows that even a displayed unified address can misrepresent the transparent receiver actually paid. See [research](RESEARCH_AND_RESOURCES.md).
- **Mechanism:** A local, open-source test kit runs a scripted Zcash payment scenario, checks a ZIP-321 request and observable transaction path, searches developer-supplied outputs for unique canary data, and produces an evidence-backed report with the privacy boundary stated for each check.
- **Core workflow:** Builder supplies a test payment request and optional app log bundle → kit checks the request and runs/observes a testnet payment → kit reports pass/fail/unknown with reproducible evidence → builder fixes a leak and reruns.
- **Differentiation:** This diagnoses leaks in payment integrations. It does not process payments, hold funds, or sell a general checkout service. The demo must show a genuine shielded testnet payment and a deliberately leaky variant caught by the kit.
- **Success:** Another builder can run the documented sample from a clean environment, reproduce at least one real shielded transfer and one caught leak, understand exactly which surfaces were checked, and avoid putting wallet secrets into the report.
- **Distribution:** Open-source repository and documentation aimed at Zcash wallet/app developers; submit to the hackathon. Any broader outreach requires a separate content/distribution decision.

## Scope boundaries

Required: R-01 through R-06 in [requirements](REQUIREMENTS.md). Excluded: a new wallet, custody, payment processing, Tor/network anonymity claims, a universal privacy score, mainnet funds, and support for every wallet or address variant.

The first gate is a real testnet transaction with trustworthy observation of shielded receipt and detection of one seeded leak. If the required tooling cannot run or the evidence cannot distinguish a private path from a leaky one by **2026-10-07**, revise the architecture before building a polished UI. Reserve the final three days for QA and submission. Available effort is not yet known; the provisional planning cap is 80 focused hours, reviewed against actual capacity.

## Scope decision log

| Date | Decision | Reason and impact |
|---|---|---|
| 2026-10-04 | User locked the payment privacy test kit. | Chosen over a generic checkout and a sealed-bid market because it targets a documented privacy failure mode and offers a narrower, reproducible build. |
| 2026-10-04 | Target Core & Tooling; build new code during the event window. | Aligns with the event's tooling track and existing-product restriction. |

