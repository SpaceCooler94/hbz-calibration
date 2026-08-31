# HHBarrelZone calibration

Window **2026-03-26 .. 2026-08-30**, split at **2026-06-26** (first 60% of game dates trains, last 40% reports).

- matchups **36,372** · PA **88,616** · HR **2,837** · base HR/PA **3.20%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **17,905**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.404 |
|  25 |        0.357 |
|  50 |        0.113 |
| 100 |        0.079 |
| 200 |        0.117 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.154 |    2.395 | 5406 |         2.386 |          2.659 |  0.273 |
|         1 |    2.397 |    3.543 | 5508 |         2.889 |          3.071 |  0.182 |
|         2 |    3.545 |    4.664 | 5676 |         2.054 |          3.684 |  1.63  |
|         3 |    4.665 |    6.054 | 5698 |         4.39  |          4.56  |  0.17  |
|         4 |    6.054 |   15.044 | 5971 |         3.543 |          4.502 |  0.96  |

Pooled test lift: **+0.652 pp**

Permutation null (200 seeded shuffles within stratum): mean +0.020, 5-95% band **[-0.382, +0.422]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 89.769 | 94.513 | 98.818 | 103.067 | 107.695 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.199 |       3.309 |   1.89  |         3.097 |      512 |
|          36 |       5.219 |       3.348 |   1.871 |         1.056 |      172 |
|          38 |       6.25  |       3.361 |   2.889 |         0.247 |       41 |
|          40 |       8.108 |       3.364 |   4.744 |         0.082 |       14 |
|          42 |      33.333 |       3.366 |  29.967 |         0.007 |        1 |
|          44 |     nan     |       3.368 | nan     |         0     |        0 |
|          46 |     nan     |       3.368 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.516 |       3.021 |   1.495 |        23.196 |     3959 |
|           8 |       5.21  |       3.233 |   1.977 |         6.815 |     1136 |
|          10 |       5.841 |       3.328 |   2.513 |         1.586 |      261 |
|          12 |       7.558 |       3.352 |   4.206 |         0.379 |       62 |
|          14 |       8.333 |       3.365 |   4.968 |         0.053 |        9 |
|          16 |     nan     |       3.368 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **27,186** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.344 | 6224 |         1.486 |          2.178 |  0.693 |
|         1 |    2.345 |    3.513 | 6346 |         3.011 |          3.048 |  0.037 |
|         2 |    3.514 |    4.651 | 6561 |         2.544 |          2.453 | -0.091 |
|         3 |    4.656 |    6.054 | 6566 |         4.111 |          3.737 | -0.374 |
|         4 |    6.054 |   15.044 | 6861 |         4.233 |          4.475 |  0.242 |

Train lift **+0.544 pp** · pooled test lift **+0.097 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.390, +0.389]** pp.

**Inside the noise band.** On this sample the SP-target read is not distinguishable from a shuffled column — the screener is useful for finding candidates, but the specific number does not beat barrel rate and should not move a price.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.