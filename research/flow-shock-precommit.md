# Flow-shock overshoot — pre-commitment

Committed before the first outcome-bearing run. The threshold was calibrated
only against the distribution of hourly trade counts; no settlement outcomes or
post-shock returns were inspected while choosing it.

## Hypothesis

An unusually concentrated burst of aggressive YES buying in a longshot market
temporarily pushes YES too high. If true, the price should subsequently fall and
the NO-side settlement return after the burst should exceed a matched ordinary
longshot baseline.

## Fixed signal definition

- Universe: settled deployment-tier markets only; sports, crypto instrumentation
  and `KXMVE*` parlays are absent from this corpus by construction.
- Ignore block trades. Restrict signal-forming trades to YES prices 1–19¢ (the
  pre-committed 1–20¢ bucket is upper-bound exclusive) and
  7–180 days remaining.
- Aggregate one-hour UTC bars. A bar is a shock when:
  - YES-aggressor volume is at least 250 contracts;
  - YES-aggressor volume is at least 10× the median of the prior 20 active
    hourly bars (minimum 10 prior active bars);
  - YES aggressors are at least 80% of bar volume;
  - the last YES-aggressor price is at least 2¢ above the preceding active
    bar's close; and
  - the preceding active bar ended no more than 24 hours earlier.
- Keep only the first qualifying shock per market. The signal becomes observable
  at the end of the shock hour. Anchor price is the last YES-aggressor price in
  that hour.

## Outcomes and controls

- Primary reaction outcome: YES price change seven days after the signal. Use
  the latest trade strictly after the signal and at or before T+7d. Markets with
  no follow-up print are conservatively assigned zero change for the gate;
  follow-up-only results and coverage are also reported.
- T+24h price change is descriptive.
- Settlement economics: NO-side maker return at the anchor price, exact
  per-series maker fee, 3.25% carry, annualized over the remaining hold.
  This is conditional economics, not proof that an order placed after detection
  would have filled.
- Matched baseline: ordinary pre-committed snapshots in the same period,
  category, price bucket and nearest horizon anchor (7/30/90/180d), excluding
  shock-market tickers. A cell needs at least 50 control snapshots or its shocks
  are unmatched. Uplift = shock annualized NO return minus that cell mean. Its
  SE combines event-clustered shock residual variation with the weighted cell
  baseline uncertainty in quadrature.
- Discovery/confirmation split: settlement before/after 2025-07-01. Standard
  errors clustered by event.

## Pass/fail gate

The screen is GREEN only if every condition holds in both periods:

1. at least 100 shock markets and 50 event clusters;
2. zero-imputed seven-day price change is below zero at two clustered SE;
3. annualized NO return clears 7% at two clustered SE; and
4. matched-baseline uplift is above zero at two clustered SE.

Anything else is RED. Category tables are exploratory and cannot rescue a RED
pooled verdict. A GREEN result still enters forward validation before changing
deployment rules.
