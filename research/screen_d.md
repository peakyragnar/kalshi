# Screen D — maker vs. taker economics (realized, from fills)

Fills analyzed: **46,290,867** (deployment tape, settled markets, horizon >= 1d).

## Maker-taker return gap per fill, by horizon (all buckets)
| period | hbucket | n | n_events | gap_mean | gap_se | ret_maker_mean | ret_maker_se | ret_taker_mean |
|---|---|---|---|---|---|---|---|---|
| confirmation | a 0-7d | 11676419 | 9038 | 0.3133 | 0.0137 | 0.0447 | 0.0109 | -0.2686 |
| confirmation | b 7-30d | 16649565 | 19197 | 0.1679 | 0.0083 | 0.0008 | 0.0064 | -0.1671 |
| confirmation | c 30-90d | 2337468 | 1938 | 0.2676 | 0.0165 | -0.0890 | 0.0271 | -0.3566 |
| confirmation | d 90-180d | 1871174 | 1387 | 0.2660 | 0.0339 | -0.0087 | 0.0400 | -0.2748 |
| confirmation | e 180d+ | 5551596 | 2308 | 0.2458 | 0.0267 | -0.0454 | 0.0260 | -0.2912 |
| discovery | a 0-7d | 1762680 | 6857 | 0.3068 | 0.0148 | 0.1603 | 0.0185 | -0.1465 |
| discovery | b 7-30d | 5006153 | 16455 | 0.0766 | 0.0092 | -0.0007 | 0.0100 | -0.0774 |
| discovery | c 30-90d | 705538 | 1255 | 0.1342 | 0.0380 | -0.0379 | 0.0576 | -0.1721 |
| discovery | d 90-180d | 329516 | 615 | 0.1464 | 0.0412 | -0.0216 | 0.0478 | -0.1680 |
| discovery | e 180d+ | 400758 | 344 | 0.1617 | 0.0403 | -0.1341 | 0.0493 | -0.2958 |

## Maker hold return by price bucket x horizon (confirmation)
| hbucket | bucket | n | n_events | ret_maker_mean | ret_maker_se |
|---|---|---|---|---|---|
| a 0-7d | 01-5 | 2074264 | 8700 | 0.0572 | 0.0327 |
| a 0-7d | 05-10 | 1096189 | 7647 | 0.0298 | 0.0191 |
| a 0-7d | 10-20 | 1528317 | 7170 | 0.0269 | 0.0114 |
| a 0-7d | 20-30 | 1127247 | 6609 | 0.0298 | 0.0072 |
| a 0-7d | 30-40 | 999523 | 6209 | 0.0190 | 0.0075 |
| a 0-7d | 40-50 | 898187 | 5911 | 0.0306 | 0.0104 |
| a 0-7d | 50-60 | 873420 | 6046 | 0.0492 | 0.0212 |
| a 0-7d | 60-70 | 767907 | 6210 | 0.0462 | 0.0122 |
| a 0-7d | 70-80 | 659840 | 6481 | 0.0352 | 0.0225 |
| a 0-7d | 80-90 | 576037 | 6969 | 0.0644 | 0.0235 |
| a 0-7d | 90-95 | 361276 | 7222 | 0.0418 | 0.0370 |
| a 0-7d | 95-99 | 714212 | 8187 | 0.1334 | 0.0622 |
| b 7-30d | 01-5 | 2101877 | 17348 | -0.0889 | 0.0246 |
| b 7-30d | 05-10 | 1659724 | 16659 | -0.0620 | 0.0145 |
| b 7-30d | 10-20 | 2431291 | 16814 | -0.0341 | 0.0103 |
| b 7-30d | 20-30 | 2033613 | 16463 | -0.0022 | 0.0104 |
| b 7-30d | 30-40 | 1883060 | 16113 | 0.0059 | 0.0040 |
| b 7-30d | 40-50 | 1645241 | 15931 | 0.0226 | 0.0038 |
| b 7-30d | 50-60 | 1338883 | 15606 | 0.0347 | 0.0074 |
| b 7-30d | 60-70 | 974713 | 13494 | 0.0513 | 0.0134 |
| b 7-30d | 70-80 | 769708 | 12183 | 0.0453 | 0.0188 |
| b 7-30d | 80-90 | 747584 | 11621 | 0.0185 | 0.0232 |
| b 7-30d | 90-95 | 442368 | 10386 | -0.0209 | 0.0328 |
| b 7-30d | 95-99 | 621503 | 11340 | 0.3321 | 0.0510 |
| c 30-90d | 01-5 | 304249 | 1375 | -0.2720 | 0.0379 |
| c 30-90d | 05-10 | 271920 | 1431 | -0.1760 | 0.0360 |
| c 30-90d | 10-20 | 332524 | 1373 | -0.0910 | 0.0374 |
| c 30-90d | 20-30 | 238208 | 1160 | -0.0438 | 0.0306 |
| c 30-90d | 30-40 | 185054 | 1037 | 0.0033 | 0.0184 |
| c 30-90d | 40-50 | 149702 | 968 | 0.0332 | 0.0118 |
| c 30-90d | 50-60 | 144851 | 958 | 0.0918 | 0.0195 |
| c 30-90d | 60-70 | 149933 | 950 | 0.0457 | 0.0515 |
| c 30-90d | 70-80 | 146719 | 946 | -0.0663 | 0.0482 |
| c 30-90d | 80-90 | 158360 | 957 | -0.1507 | 0.0568 |
| c 30-90d | 90-95 | 111355 | 860 | -0.2259 | 0.0750 |
| c 30-90d | 95-99 | 144593 | 886 | -0.0261 | 0.1887 |
| d 90-180d | 01-5 | 206003 | 838 | -0.1611 | 0.0506 |
| d 90-180d | 05-10 | 197734 | 964 | -0.1785 | 0.0447 |
| d 90-180d | 10-20 | 292348 | 995 | -0.1200 | 0.0366 |
| d 90-180d | 20-30 | 196626 | 847 | -0.0600 | 0.0361 |
| d 90-180d | 30-40 | 172595 | 759 | 0.0201 | 0.0505 |
| d 90-180d | 40-50 | 146156 | 708 | 0.0123 | 0.0177 |
| d 90-180d | 50-60 | 134113 | 668 | 0.0127 | 0.0208 |
| d 90-180d | 60-70 | 131038 | 644 | 0.0558 | 0.0576 |
| d 90-180d | 70-80 | 105851 | 600 | 0.2598 | 0.0885 |
| d 90-180d | 80-90 | 106528 | 593 | 0.1843 | 0.1343 |
| d 90-180d | 90-95 | 72512 | 511 | 0.1086 | 0.1901 |
| d 90-180d | 95-99 | 109670 | 552 | 0.2715 | 0.3255 |
| e 180d+ | 01-5 | 583414 | 1605 | -0.2133 | 0.0606 |
| e 180d+ | 05-10 | 428311 | 1656 | -0.0228 | 0.0755 |
| e 180d+ | 10-20 | 703891 | 1722 | -0.0331 | 0.0293 |
| e 180d+ | 20-30 | 629523 | 1611 | 0.0307 | 0.0277 |
| e 180d+ | 30-40 | 511641 | 1448 | 0.0538 | 0.0240 |
| e 180d+ | 40-50 | 488146 | 1331 | 0.1176 | 0.0792 |
| e 180d+ | 50-60 | 478862 | 1342 | -0.1801 | 0.1363 |
| e 180d+ | 60-70 | 413138 | 1372 | -0.1071 | 0.1023 |
| e 180d+ | 70-80 | 366155 | 1438 | 0.0369 | 0.0966 |
| e 180d+ | 80-90 | 337453 | 1539 | -0.0900 | 0.0846 |
| e 180d+ | 90-95 | 218031 | 1515 | -0.1795 | 0.0715 |
| e 180d+ | 95-99 | 393031 | 1698 | -0.0309 | 0.0670 |
## Headline cell: resting-NO fills, YES priced 1-20c, >=30d to settlement

| period | fills | events | hold ret | ann + 3.25% carry | cluster SE | 7% hurdle at 2SE |
|---|---|---|---|---|---|---|
| discovery | 329,074 | 953 | +3.26% | +22.19% | 6.94% | clears |
| confirmation | 2,076,234 | 3,271 | +4.68% | +20.92% | 2.52% | clears |

## Robustness: weighting is the whole question

- Fill-weighted (per dollar of flow absorbed): **+20.9%/yr** with carry, clears the hurdle.
- Equal-weighted by event (typical event): **+5.35%/yr** (SE 3.09%) — below the hurdle
  before SE is even applied.
- Top-10 events hold 18.7% of fills (no single-event domination, but flow is concentrated
  in liquid political/economic events, and that is where the maker return lives).
- Market-level NO win rate in the cell: 90.2%.
- By category (fill-weighted ann+carry): Economics +38%, SciTech +34%, Politics +21%,
  Climate +9%, **Elections +2.9%** (already arbed away).

**Interpretation.** Makers beat takers in every horizon bucket (gap +8 to +31pp per fill,
both periods) — the taker flow is uninformed, so adverse selection does not eat the maker
edge; it IS the maker edge. But the edge scales with flow, not with market count. A real
portfolio sits between the two weightings, positioned by per-market capacity — which is
exactly what the book recorder + Phase 3 map resolve. The provisional 2c maker haircut
from the assumptions sheet is hereby superseded by these fill-based economics (it was
too pessimistic in direction, but the equal-weight view is the binding constraint).
