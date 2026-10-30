# Review of the proposed V0.1 baseline

The four-page `QIS_Baseline_v0_1.pdf`, supplied for review on 30 October 2026, is specific enough to establish the project's direction. Its core trading rules can be retained. A few operational choices need to be resolved before different team members can implement the same experiment consistently.

This is an English version of the review and its recommendations. It does not record team approval of those recommendations, change the implemented debug configuration, or claim that the proposed weekly experiment has run. The supplied PDF is not included in this repository.

## What is already clear

Page 1 specifies the venue, instruments, direction, matched quantity, entry signal, holding period, cost scenarios, and proposed research dates. Those choices define a useful baseline. Page 3 correctly separates the earlier two-hour debug from the next experiment and does not present zero trades as strategy validation.

The proposed development interval is 19–25 October 2026 UTC, with 18 October for warm-up and an exit buffer through 26 October at 00:40 UTC, subject to coverage verification. The proposed lookback is 24 hours, compared with the implemented debug's 30 minutes.

A 2 bps excess-basis threshold is not inconsistent with approximately 30 bps of illustrative round-trip fees. Excess measures deviation from a trailing reference; fees measure a cost. The baseline can test how much convergence actually follows the anomaly. It need not be profitable by construction, and its threshold should not be changed merely to produce a positive curve.

## Decisions to resolve before freezing the specification

| Topic | Ambiguity in the proposed brief | Recommended clarification |
|---|---|---|
| **24-hour reference** | “Valid 24-hour reference” does not define sampling or missing-data tolerance. | Use a specified one-second basis grid rather than weighting periods with more book messages more heavily. State the missing-data policy and report excluded intervals. The current debug requires every expected preceding grid point; that policy is strict and should be explicitly reviewed for a full day. |
| **Funding** | “Flagged or explicitly restricted” leaves two different studies possible. | Given current missing reference prices, initially identify V0 as a restricted study excluding planned settlement crossings. Add a separately identified version covering those trades when the inputs are available. Do not choose the handling after observing outcomes. |
| **Partial fills** | “Recover unmatched exposure” does not choose between topping up and unwinding. | For the first version, cancel unfilled IOC remainders and reverse all executed exposure if either leg falls short of target size. Include every recovery cost. Keeping a smaller matched pair would be a different rule. |
| **10 USDT loss exit** | Valuation prices and included fees are unspecified. | State the formula. To match current behavior, value known fill cash flows and inventory at received mid-prices, including known fees, then simulate exit orders against the book. The trigger does not cap the final realized loss. |
| **No eligible opportunities** | “Extend a predefined continuous window” does not state its length. | Choose the extension length and stopping condition before looking at results. Do not keep extending until a satisfactory outcome appears. |
| **Acceptance criteria** | “Validation plan” and “fill assumptions” describe categories rather than completed deliverables. | Require a reproducible command, quality report, order/fill ledger, per-trade gross/net reconciliation, and a failure/open-position list. Treat V1 as the next stage after V0 is auditable. |

The recommendations intentionally leave the core entry, quantity, and holding parameters intact. They specify how to implement and evaluate the chosen baseline.

## Implementation gap

The current [configuration](../configs/debug.json) uses a 30-minute reference and a two-hour sample. The [CLI](../src/qis_spot_perp/cli.py) reads one dated book archive per leg. Implementing the proposed week therefore requires multi-day file iteration, continuity and warm-up across midnight, and appropriate tail coverage. Changing dates alone is insufficient.

The current funding path also restricts planned settlement crossings rather than applying complete settlement cash flows. This should be a named scope restriction in the weekly experiment, not an implicit discrepancy between the document and code.

## Writing and structure

The document reads as a careful research brief. Its slightly generic tone comes mainly from repeated statements about research discipline and from comprehensive-sounding phrases that leave the exact action open. The useful revision is to reduce repetition and make responsibilities concrete.

- Merge the “Observe / Decide / Replay / Account / Evaluate” table with the workstream table where they repeat one another. State the module owner, output, and downstream recipient.
- Keep the first-run chart and figures as a progress appendix, separate from rules intended to remain fixed.
- Retain one clear statement that a credible negative result is useful. Repeating it is not a substitute for defining completion.
- Replace “detailed task allocation will follow next week” with a specific delivery date. Owners can remain unassigned temporarily, but deliverables should be explicit.
- Move “supplied outputs” and “not supplied for rerunning here” into a source note. Those phrases describe preparation of the brief rather than the team's work.

## Suggested opening

> We will build an offline backtest of a BTC spot–perpetual spread strategy on OKX. In the first experiment, we will fix direction, quantity, entry threshold, holding period, and cost scenarios, then run the strategy over the specified development week. We will answer three questions: how many eligible opportunities occur; whether the spread narrows while the position is held; and how much remains after simulated execution costs. The shared deliverables are a reproducible program, a per-trade ledger, and a results report. After V0 is complete, we will test whether a single trade-pressure filter adds useful information.

Retain the baseline's core parameters, resolve the operational choices above, and separate fixed rules, current progress, and later research. The team can then assign implementation work without expanding the background material further.
