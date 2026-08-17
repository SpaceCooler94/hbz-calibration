# HHBarrelZone calibration

Window **2026-03-26 .. 2026-08-16**, split at **2026-06-18** (first 60% of game dates trains, last 40% reports).

- matchups **33,150** · PA **80,810** · HR **2,598** · base HR/PA **3.21%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **15,411**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.341 |
|  25 |        0.413 |
|  50 |        0.137 |
| 100 |        0.079 |
| 200 |        0.019 |

Chosen **k = 25**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.168 |    2.449 | 4774 |         2.65  |          2.816 |  0.166 |
|         1 |    2.45  |    3.598 | 4895 |         2.959 |          3.315 |  0.356 |
|         2 |    3.599 |    4.681 | 5018 |         2.506 |          3.297 |  0.791 |
|         3 |    4.682 |    6.108 | 5040 |         4.401 |          4.811 |  0.41  |
|         4 |    6.111 |   15.044 | 5280 |         3.588 |          4.594 |  1.007 |

Pooled test lift: **+0.555 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.014, 5-95% band **[-0.498, +0.471]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=25.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 93.766 | 97.022 | 99.877 | 102.631 | 105.524 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.276 |       3.335 |   1.941 |         3.195 |      457 |
|          36 |       5.201 |       3.377 |   1.824 |         1.08  |      153 |
|          38 |       6.25  |       3.389 |   2.861 |         0.286 |       41 |
|          40 |       8.108 |       3.392 |   4.716 |         0.095 |       14 |
|          42 |      33.333 |       3.395 |  29.939 |         0.008 |        1 |
|          44 |     nan     |       3.397 | nan     |         0     |        0 |
|          46 |     nan     |       3.397 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.554 |       3.037 |   1.517 |        23.722 |     3486 |
|           8 |       5.312 |       3.244 |   2.068 |         7.404 |     1065 |
|          10 |       6.083 |       3.35  |   2.733 |         1.721 |      246 |
|          12 |       7.558 |       3.379 |   4.18  |         0.439 |       62 |
|          14 |       8.333 |       3.394 |   4.939 |         0.061 |        9 |
|          16 |     nan     |       3.397 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **24,247** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.362 | 5544 |         1.745 |          2.557 |  0.812 |
|         1 |    2.364 |    3.556 | 5719 |         3.148 |          2.901 | -0.247 |
|         2 |    3.557 |    4.659 | 5843 |         2.372 |          3.032 |  0.659 |
|         3 |    4.66  |    6.1   | 5874 |         4.058 |          4.317 |  0.259 |
|         4 |    6.101 |   15.044 | 6148 |         3.878 |          4.741 |  0.863 |

Train lift **+0.404 pp** · pooled test lift **+0.473 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.443, +0.365]** pp.

**Clears the noise band** — SP-target-barrel carries HR signal beyond barrel rate. This is the one that could earn a weight; watch it hold across weekly recalibrations before you trust it.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.