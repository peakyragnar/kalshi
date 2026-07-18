# External data roadmap after structural discovery

External data is a probability input, not a new excuse to search arbitrary
features. Every adapter must write `effective_at`, `available_at`,
`retrieved_at`, and a source revision into the existing append-only feature
store. Backtests join on `available_at <= decision_time`.

## Priority order

| Priority | Market use | Source | Decision-time feature | Historical/as-of issue | Status |
|---:|---|---|---|---|---|
| 1 | Weather temperature and precipitation thresholds | [NOAA/NCEI archived GFS forecasts](https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast), [NWS current forecast API](https://www.weather.gov/documentation/services-web-api) | Forecast distribution at the contract station/location; probability above, below, or inside the settlement threshold | Store the model initialization and publication time, not a later reanalysis; NWS current forecasts must be captured prospectively | Next adapter: 63.9% of historically matched maker contracts in the suite survivor are Climate and Weather |
| 2 | IPO and company-event contracts | [SEC EDGAR submissions and XBRL APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Filing type, acceptance timestamp, issuer identity, and filing-state transition | Filing acceptance time controls availability; absence of an exact-name search is `NO_MATCH`, never `CLEAR` | Implemented for S-1/F-1 observations |
| 3 | Nominations, bills, votes, and government acts | [Congress.gov API](https://api.congress.gov/), [Senate XML feeds](https://www.senate.gov/general/common/generic/XML_Availability.htm), [GovInfo developer hub](https://www.govinfo.gov/developers) | Calendar placement, scheduled vote, latest official action, roll-call result, publication or signing event | Preserve the first observed feed timestamp; later status pages overwrite history unless captured | Senate nomination signal implemented; broader official-action adapter pending a supported market family |
| 4 | CPI, payroll, GDP, rates, housing, and other releases | [ALFRED/FRED vintages](https://fred.stlouisfed.org/docs/api/fred/overview.html), [BLS public API](https://www.bls.gov/developers/), [Census economic indicators API](https://www.census.gov/data/developers/data-sets/economic-indicators.html) | Release-calendar timestamp, first print, contemporaneous vintage, and consensus error where legally sourced | Revised values are leakage; use the first available vintage and exact release timestamp | Do not build until an Economics family survives structural and capacity gates |
| 5 | Election finance and candidate activity | [OpenFEC API](https://api.open.fec.gov/developers/) | Filing receipts, disbursements, committee status, and electronic filing arrival | Filing/retrieval latency and amendments must remain separate revisions | Do not build until a politics/election residual survives the suite |

## Promotion contract

An external model produces an estimated probability. It is actionable only
after subtracting the executable Kalshi probability, fees, spread, and an
uncertainty reserve. It first annotates the shadow book. No adapter places or
changes an order.

The weather source is first in line because the historically qualified structural
survivor is dominated by short-horizon Climate and Weather contracts. This is a
post-selection diagnostic, not a separately qualified weather cell. The adapter
must therefore be pre-registered as a forward probability comparison and must
not tune itself against the already selected path cell.
