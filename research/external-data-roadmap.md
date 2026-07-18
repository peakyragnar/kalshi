# External data roadmap after structural discovery

External data is a probability input, not a new excuse to search arbitrary
features. Every adapter must write `effective_at`, `available_at`,
`retrieved_at`, and a source revision into the existing append-only feature
store. Backtests join on `available_at <= decision_time`.

## Priority order

| Priority | Market use | Source | Decision-time feature | Historical/as-of issue | Status |
|---:|---|---|---|---|---|
| 1 | Weather daily high/low thresholds | [NOAA/NCEI archived GFS forecasts](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast), [Open-Meteo Previous Runs API](https://open-meteo.com/en/docs/previous-runs-api) | Fixed-lead forecast distribution at the exact settlement station; probability above, below, or inside the rulebook threshold | Preserve fixed lead and conservative publication availability; calibrate only from observations already published | **Implemented and scheduled.** 133,798 forecast features, 19,254 observations, 268 registered cells; zero historical qualifier |
| 2 | IPO and company-event contracts | [SEC EDGAR submissions and XBRL APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Filing type, acceptance timestamp, issuer identity, and filing-state transition | Filing acceptance time controls availability; absence of an exact-name search is `NO_MATCH`, never `CLEAR` | Implemented for S-1/F-1 observations |
| 3 | Nominations, bills, votes, and government acts | [Congress.gov API](https://api.congress.gov/), [Senate XML feeds](https://www.senate.gov/general/common/generic/XML_Availability.htm), [GovInfo developer hub](https://www.govinfo.gov/developers) | Calendar placement, scheduled vote, latest official action, roll-call result, publication or signing event | Preserve the first observed feed timestamp; later status pages overwrite history unless captured | Senate nomination signal implemented; broader official-action adapter pending a supported market family |
| 4 | CPI, payroll, GDP, rates, housing, and other releases | [ALFRED/FRED vintages](https://fred.stlouisfed.org/docs/api/fred/overview.html), [BLS public API](https://www.bls.gov/developers/), [Census economic indicators API](https://www.census.gov/data/developers/data-sets/economic-indicators.html) | Release-calendar timestamp, first print, contemporaneous vintage, and consensus error where legally sourced | Revised values are leakage; use the first available vintage and exact release timestamp | Do not build until an Economics family survives structural and capacity gates |
| 5 | Election finance and candidate activity | [OpenFEC API](https://api.open.fec.gov/developers/) | Filing receipts, disbursements, committee status, and electronic filing arrival | Filing/retrieval latency and amendments must remain separate revisions | Do not build until a politics/election residual survives the suite |

## Promotion contract

An external model produces an estimated probability. It is actionable only
after subtracting the executable Kalshi probability, fees, spread, and an
uncertainty reserve. It first annotates the shadow book. No adapter places or
changes an order.

The weather source was first because it combines a large liquid contract family
with free point-in-time forecasts and a direct probability mapping. Its sealed
registry tests five mechanism families against matched market-only returns.
The first completed run produced no survivor: the market price had lower Brier
error than the calibrated GFS model at both feasible horizons, and no cell
passed all three historical folds. The adapter remains scheduled so newly
settled data extends the same test without changing its gates.
