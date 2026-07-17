# Corpus audit

Generated: 2026-07-17T22:07:14.362688+00:00

## Integrity verdict

**CONDITIONAL.** Finalized close time provides the historical trading boundary, but actual settlement time is missing for **2,733,070** markets. A decision point is therefore anchored to close time; settlement time is used for carry only where it is present.

Historical order books remain unavailable; calibration and fill-conditioned execution claims are kept separate. Voided/cancelled markets are absent from the settled-only backfill and must be captured prospectively.

## Census

- `markets`: 2,733,070
- `events`: 51,587
- `series`: 3,579
- `trade_rows`: 47,342,026
- `markets_with_tape`: 380,660
- `markets_missing_settled_time`: 2,733,070
- `result_markets_with_future_scheduled_end`: 1
- `early_close_markets_without_resolution_time`: 2,729,858
- `traded_sub_6d_markets`: 332,515
- `traded_sub_6d_markets_with_tape`: 332,515

## Coverage

| category | year | duration | tape | markets | events | series | contracts |
|---|---:|---|---|---:|---:|---:|---:|
| Climate and Weather | 2021 | 1-6d | False | 8 | 7 | 3 | 0 |
| Climate and Weather | 2021 | 1-6d | True | 608 | 497 | 8 | 2321995 |
| Climate and Weather | 2021 | 30-90d | True | 5 | 5 | 5 | 69361 |
| Climate and Weather | 2021 | 6-30d | True | 12 | 9 | 6 | 75214 |
| Climate and Weather | 2021 | <1d | False | 1 | 1 | 1 | 0 |
| Climate and Weather | 2022 | 1-6d | False | 32 | 31 | 5 | 0 |
| Climate and Weather | 2022 | 1-6d | True | 2960 | 1173 | 6 | 8060482 |
| Climate and Weather | 2022 | 30-90d | True | 18 | 11 | 6 | 202960 |
| Climate and Weather | 2022 | 6-30d | False | 4 | 3 | 2 | 0 |
| Climate and Weather | 2022 | 6-30d | True | 37 | 20 | 7 | 151225 |
| Climate and Weather | 2022 | 90d+ | True | 33 | 8 | 8 | 717833 |
| Climate and Weather | 2022 | <1d | False | 1 | 1 | 1 | 0 |
| Climate and Weather | 2022 | <1d | True | 2 | 2 | 2 | 11209 |
| Climate and Weather | 2023 | 1-6d | False | 1420 | 781 | 7 | 0 |
| Climate and Weather | 2023 | 1-6d | True | 5907 | 1220 | 9 | 5678414 |
| Climate and Weather | 2023 | 30-90d | False | 23 | 9 | 4 | 0 |
| Climate and Weather | 2023 | 30-90d | True | 51 | 19 | 10 | 117868 |
| Climate and Weather | 2023 | 6-30d | False | 21 | 6 | 3 | 0 |
| Climate and Weather | 2023 | 6-30d | True | 53 | 21 | 6 | 77294 |
| Climate and Weather | 2023 | 90d+ | False | 24 | 9 | 8 | 0 |
| Climate and Weather | 2023 | 90d+ | True | 73 | 18 | 18 | 516129 |
| Climate and Weather | 2023 | <1d | False | 6 | 1 | 1 | 0 |
| Climate and Weather | 2024 | 1-6d | False | 1015 | 719 | 8 | 0 |
| Climate and Weather | 2024 | 1-6d | True | 8697 | 1574 | 9 | 84817173 |
| Climate and Weather | 2024 | 30-90d | False | 12 | 5 | 4 | 0 |
| Climate and Weather | 2024 | 30-90d | True | 232 | 49 | 11 | 1769281 |
| Climate and Weather | 2024 | 6-30d | False | 5 | 3 | 3 | 0 |
| Climate and Weather | 2024 | 6-30d | True | 108 | 21 | 9 | 775865 |
| Climate and Weather | 2024 | 90d+ | False | 11 | 9 | 5 | 0 |
| Climate and Weather | 2024 | 90d+ | True | 176 | 44 | 29 | 1546791 |
| Climate and Weather | 2024 | <1d | False | 2889 | 1722 | 5 | 0 |
| Climate and Weather | 2024 | <1d | True | 175 | 76 | 5 | 268305 |
| Climate and Weather | 2025 | 1-6d | False | 722 | 650 | 18 | 0 |
| Climate and Weather | 2025 | 1-6d | True | 16193 | 3031 | 21 | 219458364 |
| Climate and Weather | 2025 | 30-90d | False | 6 | 4 | 4 | 0 |
| Climate and Weather | 2025 | 30-90d | True | 289 | 69 | 19 | 7488201 |
| Climate and Weather | 2025 | 6-30d | False | 8 | 5 | 5 | 0 |
| Climate and Weather | 2025 | 6-30d | True | 129 | 48 | 32 | 2572817 |
| Climate and Weather | 2025 | 90d+ | False | 22 | 7 | 2 | 0 |
| Climate and Weather | 2025 | 90d+ | True | 103 | 31 | 16 | 2829983 |
| Climate and Weather | 2025 | <1d | False | 8192 | 2125 | 1 | 0 |
| Climate and Weather | 2025 | <1d | True | 688 | 367 | 6 | 430613 |
| Climate and Weather | 2026 | 1-6d | False | 9 | 5 | 3 | 0 |
| Climate and Weather | 2026 | 1-6d | True | 37956 | 6487 | 42 | 530794899 |
| Climate and Weather | 2026 | 30-90d | False | 6 | 5 | 5 | 0 |
| Climate and Weather | 2026 | 30-90d | True | 672 | 124 | 31 | 23603443 |
| Climate and Weather | 2026 | 6-30d | False | 10 | 2 | 2 | 0 |
| Climate and Weather | 2026 | 6-30d | True | 359 | 50 | 26 | 5506983 |
| Climate and Weather | 2026 | 90d+ | True | 9 | 1 | 1 | 58795 |
| Climate and Weather | 2026 | <1d | False | 27438 | 2983 | 7 | 16 |
| Climate and Weather | 2026 | <1d | True | 29717 | 3022 | 5 | 8642136 |
| Commodities | 2022 | 1-6d | False | 21 | 8 | 2 | 0 |
| Commodities | 2022 | 1-6d | True | 174 | 19 | 2 | 330713 |
| Commodities | 2022 | 6-30d | False | 24 | 8 | 1 | 0 |
| Commodities | 2022 | 6-30d | True | 156 | 12 | 1 | 162621 |
| Commodities | 2022 | <1d | False | 59 | 25 | 1 | 0 |
| Commodities | 2022 | <1d | True | 430 | 49 | 1 | 598857 |
| Commodities | 2023 | 1-6d | False | 180 | 44 | 1 | 0 |
| Commodities | 2023 | 1-6d | True | 275 | 44 | 1 | 198028 |
| Commodities | 2023 | 30-90d | True | 1 | 1 | 1 | 251 |
| Commodities | 2023 | 6-30d | False | 372 | 51 | 1 | 0 |
| Commodities | 2023 | 6-30d | True | 393 | 51 | 1 | 188125 |
| Commodities | 2023 | 90d+ | True | 7 | 2 | 2 | 68087 |
| Commodities | 2023 | <1d | False | 689 | 155 | 1 | 0 |
| Commodities | 2023 | <1d | True | 907 | 156 | 1 | 640113 |
| Commodities | 2024 | 1-6d | False | 444 | 39 | 2 | 0 |
| Commodities | 2024 | 1-6d | True | 262 | 41 | 3 | 106118 |
| Commodities | 2024 | 6-30d | False | 336 | 37 | 2 | 0 |
| Commodities | 2024 | 6-30d | True | 369 | 47 | 2 | 199290 |
| Commodities | 2024 | 90d+ | True | 7 | 2 | 2 | 23061 |
| Commodities | 2024 | <1d | False | 1703 | 145 | 1 | 0 |
| Commodities | 2024 | <1d | True | 704 | 129 | 1 | 269116 |
| Commodities | 2025 | 1-6d | False | 608 | 43 | 2 | 0 |
| Commodities | 2025 | 1-6d | True | 37 | 5 | 2 | 19403 |
| Commodities | 2025 | 6-30d | False | 79 | 8 | 1 | 0 |
| Commodities | 2025 | 6-30d | True | 71 | 10 | 1 | 209675 |
| Commodities | 2025 | 90d+ | True | 9 | 2 | 2 | 1430207 |
| Commodities | 2025 | <1d | False | 2743 | 185 | 1 | 0 |
| Commodities | 2025 | <1d | True | 32 | 15 | 1 | 16032 |
| Commodities | 2026 | 1-6d | False | 2731 | 193 | 24 | 0 |
| Commodities | 2026 | 1-6d | True | 12815 | 432 | 23 | 94854669 |
| Commodities | 2026 | 30-90d | True | 3 | 1 | 1 | 313246 |
| Commodities | 2026 | 6-30d | False | 551 | 72 | 21 | 0 |
| Commodities | 2026 | 6-30d | True | 4180 | 156 | 36 | 30502994 |
| Commodities | 2026 | <1d | False | 6135 | 248 | 14 | 3 |
| Commodities | 2026 | <1d | True | 3629 | 257 | 15 | 8740932 |
| Companies | 2023 | 1-6d | True | 7 | 2 | 2 | 88279 |
| Companies | 2024 | 30-90d | False | 1 | 1 | 1 | 0 |
| Companies | 2024 | 30-90d | True | 12 | 3 | 3 | 25642 |
| Companies | 2024 | 6-30d | True | 4 | 1 | 1 | 19790 |
| Companies | 2024 | 90d+ | True | 1 | 1 | 1 | 28683 |
| Companies | 2025 | 1-6d | True | 3 | 3 | 3 | 15436 |
| Companies | 2025 | 30-90d | False | 1 | 1 | 1 | 0 |
| Companies | 2025 | 30-90d | True | 11 | 11 | 11 | 1824788 |
| Companies | 2025 | 6-30d | False | 6 | 2 | 2 | 0 |
| Companies | 2025 | 6-30d | True | 18 | 7 | 7 | 48023 |
| Companies | 2025 | 90d+ | False | 24 | 5 | 5 | 0 |
| Companies | 2025 | 90d+ | True | 29 | 15 | 12 | 4222901 |
| Companies | 2026 | 30-90d | True | 4 | 2 | 2 | 5547908 |
| Companies | 2026 | 6-30d | True | 18 | 2 | 2 | 27919925 |
| Companies | 2026 | 90d+ | False | 14 | 4 | 4 | 0 |
| Companies | 2026 | 90d+ | True | 47 | 21 | 21 | 39066891 |
| Economics | 2021 | 1-6d | True | 18 | 17 | 5 | 59824 |
| Economics | 2021 | 30-90d | False | 1 | 1 | 1 | 0 |
| Economics | 2021 | 30-90d | True | 8 | 8 | 6 | 58490 |
| Economics | 2021 | 6-30d | True | 102 | 93 | 11 | 656581 |
| Economics | 2021 | 90d+ | True | 1 | 1 | 1 | 33756 |
| Economics | 2022 | 1-6d | False | 13 | 8 | 4 | 0 |
| Economics | 2022 | 1-6d | True | 189 | 63 | 7 | 550341 |
| Economics | 2022 | 30-90d | False | 6 | 2 | 1 | 0 |
| Economics | 2022 | 30-90d | True | 210 | 45 | 17 | 4353125 |
| Economics | 2022 | 6-30d | False | 47 | 24 | 13 | 0 |
| Economics | 2022 | 6-30d | True | 471 | 217 | 26 | 2292140 |
| Economics | 2022 | 90d+ | False | 24 | 4 | 2 | 0 |
| Economics | 2022 | 90d+ | True | 171 | 25 | 9 | 6072331 |
| Economics | 2022 | <1d | False | 3 | 1 | 1 | 0 |
| Economics | 2023 | 1-6d | False | 41 | 18 | 7 | 0 |
| Economics | 2023 | 1-6d | True | 76 | 33 | 7 | 105152 |
| Economics | 2023 | 30-90d | False | 107 | 22 | 14 | 0 |
| Economics | 2023 | 30-90d | True | 250 | 50 | 26 | 2968209 |
| Economics | 2023 | 6-30d | False | 333 | 123 | 8 | 0 |
| Economics | 2023 | 6-30d | True | 561 | 182 | 30 | 1231692 |
| Economics | 2023 | 90d+ | False | 313 | 46 | 7 | 0 |
| Economics | 2023 | 90d+ | True | 629 | 80 | 26 | 12873178 |
| Economics | 2023 | <1d | False | 7 | 7 | 1 | 0 |
| Economics | 2023 | <1d | True | 14 | 14 | 1 | 1474 |
| Economics | 2024 | 1-6d | False | 8 | 4 | 2 | 0 |
| Economics | 2024 | 1-6d | True | 29 | 12 | 5 | 536115 |
| Economics | 2024 | 30-90d | False | 224 | 91 | 18 | 0 |
| Economics | 2024 | 30-90d | True | 1000 | 193 | 28 | 15959551 |
| Economics | 2024 | 6-30d | False | 251 | 56 | 13 | 0 |
| Economics | 2024 | 6-30d | True | 723 | 158 | 21 | 3767112 |
| Economics | 2024 | 90d+ | False | 17 | 8 | 6 | 0 |
| Economics | 2024 | 90d+ | True | 217 | 51 | 27 | 23893243 |
| Economics | 2024 | <1d | False | 2 | 2 | 1 | 0 |
| Economics | 2024 | <1d | True | 3 | 1 | 1 | 3071 |
| Economics | 2025 | 1-6d | False | 5 | 1 | 1 | 0 |
| Economics | 2025 | 1-6d | True | 38 | 10 | 6 | 267873 |
| Economics | 2025 | 30-90d | False | 139 | 53 | 20 | 0 |
| Economics | 2025 | 30-90d | True | 827 | 163 | 42 | 337706283 |
| Economics | 2025 | 6-30d | False | 703 | 71 | 14 | 0 |
| Economics | 2025 | 6-30d | True | 809 | 186 | 40 | 31484066 |
| Economics | 2025 | 90d+ | False | 39 | 14 | 14 | 0 |
| Economics | 2025 | 90d+ | True | 291 | 67 | 49 | 86903388 |
| Economics | 2025 | <1d | False | 1 | 1 | 1 | 0 |
| Economics | 2026 | 1-6d | False | 74 | 17 | 16 | 0 |
| Economics | 2026 | 1-6d | True | 492 | 77 | 38 | 20259518 |
| Economics | 2026 | 30-90d | False | 96 | 31 | 17 | 0 |
| Economics | 2026 | 30-90d | True | 1416 | 183 | 89 | 27858602 |
| Economics | 2026 | 6-30d | False | 393 | 90 | 42 | 1 |
| Economics | 2026 | 6-30d | True | 3319 | 341 | 130 | 45222599 |
| Economics | 2026 | 90d+ | False | 50 | 13 | 7 | 0 |
| Economics | 2026 | 90d+ | True | 801 | 114 | 68 | 194115317 |
| Economics | 2026 | <1d | False | 3069 | 295 | 15 | 4 |
| Economics | 2026 | <1d | True | 3797 | 363 | 22 | 15017740 |
| Elections | 2024 | 1-6d | True | 5 | 2 | 2 | 6673 |
| Elections | 2024 | 6-30d | True | 31 | 17 | 17 | 2349388 |
| Elections | 2024 | <1d | False | 5 | 1 | 1 | 0 |
| Elections | 2025 | 1-6d | False | 2 | 2 | 2 | 0 |
| Elections | 2025 | 1-6d | True | 49 | 11 | 11 | 1402635 |
| Elections | 2025 | 30-90d | False | 78 | 32 | 31 | 0 |
| Elections | 2025 | 30-90d | True | 643 | 189 | 186 | 256604938 |
| Elections | 2025 | 6-30d | False | 37 | 15 | 15 | 0 |
| Elections | 2025 | 6-30d | True | 252 | 59 | 59 | 13430006 |
| Elections | 2025 | 90d+ | False | 138 | 40 | 40 | 0 |
| Elections | 2025 | 90d+ | True | 355 | 87 | 87 | 349233411 |
| Elections | 2025 | <1d | False | 5 | 1 | 1 | 0 |
| Elections | 2025 | <1d | True | 10 | 2 | 2 | 28083 |
| Elections | 2026 | 1-6d | False | 2 | 1 | 1 | 0 |
| Elections | 2026 | 1-6d | True | 108 | 33 | 30 | 6835855 |
| Elections | 2026 | 30-90d | False | 55 | 37 | 13 | 0 |
| Elections | 2026 | 30-90d | True | 2248 | 485 | 189 | 137286349 |
| Elections | 2026 | 6-30d | False | 27 | 16 | 10 | 1 |
| Elections | 2026 | 6-30d | True | 1118 | 260 | 113 | 44941888 |
| Elections | 2026 | 90d+ | False | 5 | 3 | 3 | 0 |
| Elections | 2026 | 90d+ | True | 1100 | 224 | 196 | 285256195 |
| Elections | 2026 | <1d | True | 28 | 11 | 9 | 694030 |
| Financials | 2021 | 6-30d | True | 1 | 1 | 1 | 3391 |
| Financials | 2022 | 1-6d | False | 35 | 17 | 6 | 0 |
| Financials | 2022 | 1-6d | True | 978 | 145 | 9 | 9057868 |
| Financials | 2022 | 30-90d | True | 30 | 2 | 2 | 6253 |
| Financials | 2022 | 6-30d | False | 43 | 20 | 3 | 0 |
| Financials | 2022 | 6-30d | True | 1011 | 89 | 5 | 8210471 |
| Financials | 2022 | 90d+ | True | 31 | 3 | 3 | 771922 |
| Financials | 2022 | <1d | False | 629 | 242 | 6 | 0 |
| Financials | 2022 | <1d | True | 3685 | 548 | 9 | 20565651 |
| Financials | 2023 | 1-6d | False | 3655 | 772 | 10 | 0 |
| Financials | 2023 | 1-6d | True | 5917 | 926 | 12 | 68344840 |
| Financials | 2023 | 30-90d | True | 1 | 1 | 1 | 98 |
| Financials | 2023 | 6-30d | False | 372 | 98 | 3 | 0 |
| Financials | 2023 | 6-30d | True | 1864 | 150 | 4 | 16479811 |
| Financials | 2023 | 90d+ | False | 1 | 1 | 1 | 0 |
| Financials | 2023 | 90d+ | True | 47 | 10 | 10 | 27558361 |
| Financials | 2023 | <1d | False | 3959 | 848 | 14 | 0 |
| Financials | 2023 | <1d | True | 4494 | 984 | 12 | 7280373 |
| Financials | 2024 | 1-6d | False | 275132 | 4262 | 13 | 0 |
| Financials | 2024 | 1-6d | True | 66457 | 3274 | 17 | 125072373 |
| Financials | 2024 | 30-90d | False | 7 | 2 | 2 | 0 |
| Financials | 2024 | 30-90d | True | 50 | 18 | 13 | 250164 |
| Financials | 2024 | 6-30d | False | 597 | 62 | 9 | 0 |
| Financials | 2024 | 6-30d | True | 2353 | 160 | 12 | 34536515 |
| Financials | 2024 | 90d+ | False | 28 | 6 | 6 | 0 |
| Financials | 2024 | 90d+ | True | 122 | 33 | 25 | 39268864 |
| Financials | 2024 | <1d | False | 3079 | 147 | 10 | 0 |
| Financials | 2024 | <1d | True | 2232 | 567 | 12 | 8505944 |
| Financials | 2025 | 1-6d | False | 458623 | 5430 | 10 | 0 |
| Financials | 2025 | 1-6d | True | 6443 | 803 | 16 | 53688915 |
| Financials | 2025 | 30-90d | False | 77 | 27 | 24 | 0 |
| Financials | 2025 | 30-90d | True | 137 | 42 | 27 | 2060550 |
| Financials | 2025 | 6-30d | False | 2451 | 159 | 8 | 0 |
| Financials | 2025 | 6-30d | True | 1396 | 133 | 16 | 5421871 |
| Financials | 2025 | 90d+ | False | 35 | 20 | 20 | 0 |
| Financials | 2025 | 90d+ | True | 246 | 79 | 62 | 22107523 |
| Financials | 2025 | <1d | False | 928390 | 3091 | 8 | 0 |
| Financials | 2025 | <1d | True | 42575 | 2949 | 8 | 121713554 |
| Financials | 2026 | 1-6d | False | 48094 | 947 | 19 | 1 |
| Financials | 2026 | 1-6d | True | 11400 | 745 | 56 | 48320873 |
| Financials | 2026 | 30-90d | False | 2 | 2 | 2 | 0 |
| Financials | 2026 | 30-90d | True | 290 | 57 | 53 | 13872602 |
| Financials | 2026 | 6-30d | False | 364 | 61 | 8 | 1 |
| Financials | 2026 | 6-30d | True | 2137 | 224 | 115 | 11990224 |
| Financials | 2026 | 90d+ | False | 12 | 11 | 11 | 0 |
| Financials | 2026 | 90d+ | True | 333 | 101 | 98 | 22923503 |
| Financials | 2026 | <1d | False | 560572 | 1887 | 12 | 7 |
| Financials | 2026 | <1d | True | 59261 | 1997 | 23 | 92214532 |
| Health | 2021 | 1-6d | True | 99 | 99 | 5 | 445478 |
| Health | 2021 | 30-90d | True | 7 | 6 | 5 | 321096 |
| Health | 2021 | 6-30d | False | 1 | 1 | 1 | 0 |
| Health | 2021 | 6-30d | True | 59 | 46 | 9 | 486163 |
| Health | 2021 | 90d+ | True | 1 | 1 | 1 | 119332 |
| Health | 2021 | <1d | True | 6 | 6 | 1 | 75283 |
| Health | 2022 | 1-6d | False | 2 | 2 | 2 | 0 |
| Health | 2022 | 1-6d | True | 221 | 203 | 7 | 835959 |
| Health | 2022 | 30-90d | True | 25 | 16 | 10 | 1303232 |
| Health | 2022 | 6-30d | False | 1 | 1 | 1 | 0 |
| Health | 2022 | 6-30d | True | 109 | 82 | 15 | 1806860 |
| Health | 2022 | 90d+ | True | 5 | 5 | 4 | 664599 |
| Health | 2022 | <1d | True | 2 | 2 | 1 | 2638 |
| Health | 2023 | 6-30d | True | 8 | 4 | 2 | 16686 |
| Health | 2023 | 90d+ | True | 6 | 6 | 4 | 741447 |
| Health | 2024 | 30-90d | True | 1 | 1 | 1 | 30086 |
| Health | 2024 | 90d+ | True | 9 | 7 | 7 | 359829 |
| Health | 2025 | 30-90d | True | 2 | 2 | 2 | 10720 |
| Health | 2025 | 90d+ | False | 3 | 1 | 1 | 0 |
| Health | 2025 | 90d+ | True | 25 | 9 | 8 | 454880 |
| Health | 2026 | 90d+ | True | 31 | 13 | 13 | 1206768 |
| Politics | 2021 | 1-6d | True | 3 | 3 | 3 | 31122 |
| Politics | 2021 | 30-90d | True | 21 | 14 | 14 | 760912 |
| Politics | 2021 | 6-30d | True | 27 | 17 | 6 | 1099843 |
| Politics | 2021 | 90d+ | True | 1 | 1 | 1 | 38696 |
| Politics | 2022 | 1-6d | False | 5 | 3 | 2 | 0 |
| Politics | 2022 | 1-6d | True | 95 | 11 | 2 | 441173 |
| Politics | 2022 | 30-90d | True | 13 | 9 | 8 | 597663 |
| Politics | 2022 | 6-30d | False | 16 | 9 | 2 | 0 |
| Politics | 2022 | 6-30d | True | 607 | 96 | 16 | 3369976 |
| Politics | 2022 | 90d+ | True | 16 | 15 | 15 | 960525 |
| Politics | 2023 | 1-6d | False | 3 | 3 | 3 | 0 |
| Politics | 2023 | 1-6d | True | 32 | 8 | 5 | 37457 |
| Politics | 2023 | 30-90d | True | 20 | 13 | 9 | 725138 |
| Politics | 2023 | 6-30d | False | 83 | 45 | 4 | 0 |
| Politics | 2023 | 6-30d | True | 877 | 119 | 6 | 2000570 |
| Politics | 2023 | 90d+ | True | 33 | 18 | 18 | 1983890 |
| Politics | 2024 | 1-6d | False | 12 | 4 | 4 | 0 |
| Politics | 2024 | 1-6d | True | 89 | 26 | 20 | 1331728 |
| Politics | 2024 | 30-90d | False | 2 | 2 | 1 | 0 |
| Politics | 2024 | 30-90d | True | 104 | 51 | 26 | 3081057 |
| Politics | 2024 | 6-30d | False | 75 | 40 | 4 | 0 |
| Politics | 2024 | 6-30d | True | 974 | 154 | 33 | 6635267 |
| Politics | 2024 | 90d+ | False | 4 | 2 | 2 | 0 |
| Politics | 2024 | 90d+ | True | 79 | 37 | 34 | 7921038 |
| Politics | 2024 | <1d | False | 16 | 2 | 2 | 0 |
| Politics | 2024 | <1d | True | 13 | 3 | 3 | 13363 |
| Politics | 2025 | 1-6d | False | 72 | 15 | 15 | 0 |
| Politics | 2025 | 1-6d | True | 400 | 113 | 92 | 19679345 |
| Politics | 2025 | 30-90d | False | 186 | 74 | 70 | 0 |
| Politics | 2025 | 30-90d | True | 1333 | 397 | 384 | 241416119 |
| Politics | 2025 | 6-30d | False | 210 | 78 | 64 | 0 |
| Politics | 2025 | 6-30d | True | 1417 | 344 | 252 | 97954244 |
| Politics | 2025 | 90d+ | False | 248 | 66 | 66 | 0 |
| Politics | 2025 | 90d+ | True | 995 | 275 | 270 | 1097036620 |
| Politics | 2025 | <1d | False | 47 | 11 | 11 | 0 |
| Politics | 2025 | <1d | True | 110 | 22 | 21 | 2526038 |
| Politics | 2026 | 1-6d | False | 4 | 3 | 3 | 0 |
| Politics | 2026 | 1-6d | True | 393 | 122 | 81 | 33111188 |
| Politics | 2026 | 30-90d | False | 9 | 3 | 3 | 0 |
| Politics | 2026 | 30-90d | True | 739 | 219 | 183 | 195401904 |
| Politics | 2026 | 6-30d | False | 4 | 2 | 2 | 0 |
| Politics | 2026 | 6-30d | True | 1769 | 397 | 178 | 131525970 |
| Politics | 2026 | 90d+ | False | 21 | 6 | 6 | 0 |
| Politics | 2026 | 90d+ | True | 957 | 335 | 325 | 349593998 |
| Politics | 2026 | <1d | False | 4 | 3 | 3 | 0 |
| Politics | 2026 | <1d | True | 41 | 19 | 17 | 3425629 |
| Science and Technology | 2021 | 30-90d | True | 3 | 2 | 2 | 57883 |
| Science and Technology | 2021 | 6-30d | True | 10 | 7 | 2 | 82351 |
| Science and Technology | 2022 | 1-6d | True | 2 | 2 | 1 | 4689 |
| Science and Technology | 2022 | 30-90d | True | 4 | 4 | 3 | 38611 |
| Science and Technology | 2022 | 6-30d | True | 3 | 3 | 2 | 14347 |
| Science and Technology | 2023 | 30-90d | True | 5 | 1 | 1 | 4757 |
| Science and Technology | 2024 | 1-6d | True | 2 | 2 | 1 | 121054 |
| Science and Technology | 2024 | 30-90d | False | 2 | 1 | 1 | 0 |
| Science and Technology | 2024 | 30-90d | True | 53 | 19 | 12 | 664535 |
| Science and Technology | 2024 | 6-30d | True | 30 | 10 | 6 | 815550 |
| Science and Technology | 2024 | 90d+ | True | 50 | 18 | 16 | 1999289 |
| Science and Technology | 2024 | <1d | True | 1 | 1 | 1 | 363 |
| Science and Technology | 2025 | 1-6d | False | 4 | 1 | 1 | 0 |
| Science and Technology | 2025 | 1-6d | True | 14 | 8 | 6 | 467774 |
| Science and Technology | 2025 | 30-90d | False | 2 | 2 | 2 | 0 |
| Science and Technology | 2025 | 30-90d | True | 128 | 39 | 22 | 7266680 |
| Science and Technology | 2025 | 6-30d | False | 15 | 5 | 5 | 0 |
| Science and Technology | 2025 | 6-30d | True | 122 | 34 | 17 | 4765681 |
| Science and Technology | 2025 | 90d+ | False | 5 | 2 | 2 | 0 |
| Science and Technology | 2025 | 90d+ | True | 176 | 68 | 63 | 27689967 |
| Science and Technology | 2025 | <1d | False | 2 | 2 | 2 | 0 |
| Science and Technology | 2025 | <1d | True | 21 | 7 | 4 | 154726 |
| Science and Technology | 2026 | 1-6d | False | 1 | 1 | 1 | 0 |
| Science and Technology | 2026 | 1-6d | True | 75 | 28 | 19 | 1371725 |
| Science and Technology | 2026 | 30-90d | True | 233 | 40 | 24 | 23946569 |
| Science and Technology | 2026 | 6-30d | False | 36 | 7 | 4 | 0 |
| Science and Technology | 2026 | 6-30d | True | 1441 | 190 | 44 | 40646487 |
| Science and Technology | 2026 | 90d+ | True | 120 | 51 | 48 | 24538068 |
| Science and Technology | 2026 | <1d | False | 40 | 1 | 1 | 0 |
| Science and Technology | 2026 | <1d | True | 1 | 1 | 1 | 6935 |
| World | 2021 | 1-6d | True | 70 | 65 | 8 | 510224 |
| World | 2021 | 30-90d | False | 1 | 1 | 1 | 0 |
| World | 2021 | 30-90d | True | 6 | 6 | 6 | 99193 |
| World | 2021 | 6-30d | True | 11 | 11 | 8 | 169810 |
| World | 2021 | <1d | False | 1 | 1 | 1 | 0 |
| World | 2021 | <1d | True | 2 | 1 | 1 | 3705 |
| World | 2022 | 1-6d | False | 140 | 93 | 3 | 0 |
| World | 2022 | 1-6d | True | 274 | 143 | 4 | 225625 |
| World | 2022 | 30-90d | True | 3 | 3 | 3 | 22992 |
| World | 2022 | 6-30d | True | 7 | 3 | 2 | 62194 |
| World | 2022 | 90d+ | True | 4 | 4 | 4 | 690853 |
| World | 2022 | <1d | False | 6 | 3 | 3 | 0 |
| World | 2022 | <1d | True | 3 | 2 | 2 | 1848 |
| World | 2023 | 90d+ | True | 13 | 5 | 5 | 96652 |
| World | 2024 | 30-90d | True | 1 | 1 | 1 | 17999 |
| World | 2024 | 6-30d | True | 1 | 1 | 1 | 1598 |
| World | 2024 | 90d+ | False | 1 | 1 | 1 | 0 |
| World | 2024 | 90d+ | True | 8 | 4 | 4 | 35631 |
| World | 2025 | 1-6d | False | 12 | 6 | 5 | 0 |
| World | 2025 | 1-6d | True | 68 | 18 | 9 | 269679 |
| World | 2025 | 30-90d | False | 17 | 1 | 1 | 0 |
| World | 2025 | 30-90d | True | 26 | 7 | 7 | 427833 |
| World | 2025 | 6-30d | False | 2 | 1 | 1 | 0 |
| World | 2025 | 6-30d | True | 71 | 18 | 16 | 1840025 |
| World | 2025 | 90d+ | False | 8 | 3 | 3 | 0 |
| World | 2025 | 90d+ | True | 20 | 11 | 11 | 1238875 |
| World | 2025 | <1d | True | 2 | 2 | 2 | 15058 |
| World | 2026 | 30-90d | True | 2 | 2 | 2 | 123176 |
| World | 2026 | 90d+ | False | 4 | 1 | 1 | 0 |
| World | 2026 | 90d+ | True | 23 | 11 | 11 | 349873 |
