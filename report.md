# HHBarrelZone calibration

Window **2026-03-26 .. 2026-09-06**, split at **2026-06-30** (first 60% of game dates trains, last 40% reports).

- matchups **38,101** · PA **92,788** · HR **2,972** · base HR/PA **3.20%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **19,250**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.38  |
|  25 |        0.319 |
|  50 |        0.063 |
| 100 |        0.101 |
| 200 |        0.009 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.154 |    2.368 | 5681 |         2.22  |          2.491 |  0.271 |
|         1 |    2.37  |    3.509 | 5803 |         2.584 |          3.183 |  0.599 |
|         2 |    3.511 |    4.665 | 5989 |         2.338 |          3.606 |  1.268 |
|         3 |    4.665 |    6.04  | 6011 |         4.708 |          4.806 |  0.098 |
|         4 |    6.041 |   15.044 | 6279 |         3.178 |          4.526 |  1.348 |

Pooled test lift: **+0.728 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.008, 5-95% band **[-0.420, +0.414]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 89.854 | 94.523 | 98.821 | 103.089 | 107.722 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.27  |       3.299 |   1.972 |         3.04  |      543 |
|          36 |       5.368 |       3.338 |   2.03  |         1.033 |      180 |
|          38 |       6.25  |       3.352 |   2.898 |         0.23  |       41 |
|          40 |       8.108 |       3.355 |   4.753 |         0.076 |       14 |
|          42 |      33.333 |       3.357 |  29.977 |         0.006 |        1 |
|          44 |     nan     |       3.359 | nan     |         0     |        0 |
|          46 |     nan     |       3.359 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.505 |       3.015 |   1.491 |        23.07  |     4233 |
|           8 |       5.166 |       3.232 |   1.934 |         6.561 |     1175 |
|          10 |       5.842 |       3.32  |   2.522 |         1.512 |      268 |
|          12 |       7.558 |       3.344 |   4.214 |         0.353 |       62 |
|          14 |       8.333 |       3.356 |   4.977 |         0.049 |        9 |
|          16 |     nan     |       3.359 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **28,798** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.326 | 6577 |         1.498 |          2.112 |  0.613 |
|         1 |    2.329 |    3.483 | 6621 |         2.85  |          3.008 |  0.159 |
|         2 |    3.485 |    4.651 | 6913 |         2.36  |          3.284 |  0.925 |
|         3 |    4.656 |    6.02  | 6881 |         4.434 |          4.104 | -0.33  |
|         4 |    6.021 |   15.044 | 7214 |         4.153 |          4.572 |  0.419 |

Train lift **+0.581 pp** · pooled test lift **+0.358 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.367, +0.389]** pp.

**Inside the noise band.** On this sample the SP-target read is not distinguishable from a shuffled column — the screener is useful for finding candidates, but the specific number does not beat barrel rate and should not move a price.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.