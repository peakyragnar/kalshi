# Rulebook sweep — top series in both qualifying cells

36 series reviewed (22 Politics-cell, 14 Financials-cell ex-ticket), rules text
read in full, settlement sources checked. Verdicts: GREEN = deploy without
reservation; YELLOW = deployable, position-level care; RED = exclude.

**Headline: Kalshi's drafting has matured.** No discretionary-settlement
language found in any reviewed series. Travel markets use "physically travelled
to and been present within the geographic boundaries" — excellent. Legislative
markets settle on Library of Congress records.

## Politics 30d cell (22 series): 12 GREEN · 8 YELLOW · 2 RED

| Verdict | Series | Note |
|---|---|---|
| GREEN | KXVISITVENEZUELA, KXVISITIRAN, KXVISITNYC, KXTRUMPIRAN | geographic-boundary language; precise |
| GREEN | KXEXPELSWALWELLVOTES, KXSAVEAMERICACLOTURE, KXBILLSCOUNT | Library of Congress vote/bill counts |
| GREEN | KXAPRPOTUSEOY | RCP number at exact timestamp |
| GREEN | KXFTACOUNTRIES | legal mechanism spelled out |
| GREEN | KXTRUMPPARDON | official act; "reprieve" slightly broadens |
| GREEN | KXLEAVEPOWELL | explicitly excludes mere announcement |
| GREEN | KXLEAVEHOUSE | precise; note NO-seller is short mortality/scandal |
| YELLOW | KXPRESVISIT | "visits" undefined (siblings use geographic language) |
| YELLOW | KXWHVISIT | "visits the White House" — scope of grounds unclear |
| YELLOW | KXTARIFFRATECAN, KXTARIFFRATEPRC | "general import tariff rate" undefined vs carve-outs |
| YELLOW | KXLAGODAYS | trip-counting edges |
| YELLOW | KXGOLDCARDS | novel program, news-counted quantity |
| YELLOW | KXLEAVEADMIN | "or it is announced" — widens YES surface for NO-sellers |
| YELLOW | KXRECESSAPPT | role-scope judgment |
| **RED** | **KXCRYPTOSTRUCTURE** | "a crypto market structure bill" — categorical judgment call |
| **RED** | **KXTARIFFCHECKS** | "directly attributable to tariff revenue" — attribution judgment |

## Financials 90d cell ex-ticket (14 series): 10 GREEN · 4 YELLOW · 0 RED

| Verdict | Series | Note |
|---|---|---|
| GREEN | KXNASDAQ100Y, KXINXY | index value at explicit timestamp |
| GREEN | KXTESLA, KXTESLAPROD, KXBOEING, KXMETAHEADCOUNT, KXSPOTIFYMAU, KXCBVOLUME, KXDASHORDERS, KXUBERTRIPS | company-reported metrics, official reports |
| YELLOW | KXIPO, KXIPOANDURIL, KXIPOSTARLINK | "confirms an IPO" — confirm vs file vs list undefined |
| YELLOW | KXNEWROLEX | "confirmed as CEO" — verb loose but workable |

## Systematic pattern for position selection

Conditions divide into **physical/official acts** (travel with geographic
language, recorded votes, index closes, company reports) and
**announcement/attribution triggers** ("announces," "confirms," "directly
attributable," "a bill of type X"). The first kind settles mechanically; the
second adds a path for YES to trigger on words rather than events — which, for
a NO-seller, means a wider tail than the base rate suggests. **Selection rule:
prefer act-conditions; treat announcement-triggers as YELLOW by default; skip
attribution/categorical conditions entirely.**

Settlement-source note: politics series settle off named-outlet panels
(Guardian/Fox/WSJ etc.) or official bodies; the panel structure means no single
outlet decides. Acceptable; official-body sources remain preferable.

## Sweep 2 — 2026-07-17 (today's candidate backlog, 34 series)

- **GREEN (8):** KXSENATECONFIRM (Senate floor vote = act; keyword flag overridden
  on read), KXHORMUZNORM (IMF PortWatch, quantitative), and six company-metric
  templates: KXBULL, KXKLAR, KXMETA, KXTOL, KXURBN, KXWMT.
- **YELLOW (26):** 18-series IPO family ("confirms an IPO" — word trigger; EDGAR
  watcher is the control), index add/remove quartet (official but
  announcement-triggered, committee upstream), KXCOMPANYACTIONMERGER
  ("officially announces a definitive, binding agreement"), and three NVIDIA
  compute-price series (quantitative but pricing source unverified — upgrade
  candidates after source check).
- **RED (0).** Drafting quality consistent with sweep 1.

Process note: candidate-backlog sweeps are the rolling daily chore; verdicts
land in candidates.py sets and flow to the dashboard same-day.
