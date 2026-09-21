# HHBarrelZone calibration

Window **2026-03-26 .. 2026-09-20**, split at **2026-07-09** (first 60% of game dates trains, last 40% reports).

- matchups **41,369** · PA **100,444** · HR **3,225** · base HR/PA **3.21%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **21,914**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.401 |
|  25 |        0.362 |
|  50 |        0.252 |
| 100 |        0.27  |
| 200 |        0.244 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.154 |    2.346 | 6170 |         2.142 |          2.397 |  0.255 |
|         1 |    2.347 |    3.468 | 6272 |         2.403 |          2.967 |  0.564 |
|         2 |    3.469 |    4.657 | 6512 |         2.28  |          3.657 |  1.377 |
|         3 |    4.657 |    6.005 | 6515 |         4.527 |          4.267 | -0.26  |
|         4 |    6.006 |   15.044 | 6805 |         3.064 |          4.429 |  1.365 |

Pooled test lift: **+0.671 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.006, 5-95% band **[-0.424, +0.394]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 89.974 | 94.575 | 98.856 | 103.077 | 107.705 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.082 |       3.298 |   1.784 |         2.894 |      588 |
|          36 |       5.66  |       3.327 |   2.333 |         0.962 |      190 |
|          38 |       6.25  |       3.343 |   2.907 |         0.203 |       41 |
|          40 |       8.108 |       3.346 |   4.762 |         0.067 |       14 |
|          42 |      33.333 |       3.348 |  29.986 |         0.005 |        1 |
|          44 |     nan     |       3.349 | nan     |         0     |        0 |
|          46 |     nan     |       3.349 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.459 |       3.02  |   1.438 |        22.883 |     4776 |
|           8 |       5.118 |       3.232 |   1.886 |         6.243 |     1270 |
|          10 |       5.621 |       3.317 |   2.304 |         1.389 |      278 |
|          12 |       7.558 |       3.336 |   4.222 |         0.312 |       62 |
|          14 |       8.333 |       3.347 |   4.986 |         0.044 |        9 |
|          16 |     nan     |       3.349 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **31,885** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.312 | 7051 |         1.617 |          2.233 |  0.616 |
|         1 |    2.314 |    3.448 | 7200 |         2.881 |          2.676 | -0.205 |
|         2 |    3.453 |    4.646 | 7342 |         2.742 |          3.018 |  0.276 |
|         3 |    4.647 |    6     | 7439 |         3.826 |          4.1   |  0.274 |
|         4 |    6.003 |   15.044 | 7747 |         3.73  |          5.071 |  1.341 |

Train lift **+0.207 pp** · pooled test lift **+0.471 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.397, +0.419]** pp.

**Clears the noise band** — SP-target-barrel carries HR signal beyond barrel rate. This is the one that could earn a weight; watch it hold across weekly recalibrations before you trust it.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.