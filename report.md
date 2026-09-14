# HHBarrelZone calibration

Window **2026-03-26 .. 2026-09-13**, split at **2026-07-04** (first 60% of game dates trains, last 40% reports).

- matchups **39,722** · PA **96,576** · HR **3,109** · base HR/PA **3.22%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **20,559**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.369 |
|  25 |        0.366 |
|  50 |        0.21  |
| 100 |        0.268 |
| 200 |        0.188 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.154 |    2.358 | 5976 |         2.266 |          2.376 |  0.11  |
|         1 |    2.359 |    3.493 | 6103 |         2.549 |          3.02  |  0.47  |
|         2 |    3.495 |    4.662 | 6283 |         2.128 |          3.833 |  1.705 |
|         3 |    4.663 |    6.028 | 6301 |         4.575 |          4.615 |  0.039 |
|         4 |    6.031 |   15.044 | 6596 |         2.98  |          4.859 |  1.879 |

Pooled test lift: **+0.860 pp**

Permutation null (200 seeded shuffles within stratum): mean +0.013, 5-95% band **[-0.403, +0.408]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |   p50 |   p75 |     p90 |
|-------:|-------:|------:|------:|--------:|
| 89.907 | 94.561 | 98.85 | 103.1 | 107.715 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.095 |       3.327 |   1.768 |         2.953 |      562 |
|          36 |       5.253 |       3.361 |   1.892 |         0.991 |      184 |
|          38 |       6.25  |       3.373 |   2.877 |         0.216 |       41 |
|          40 |       8.108 |       3.376 |   4.732 |         0.071 |       14 |
|          42 |      33.333 |       3.378 |  29.956 |         0.006 |        1 |
|          44 |     nan     |       3.379 | nan     |         0     |        0 |
|          46 |     nan     |       3.379 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.524 |       3.037 |   1.487 |        23.025 |     4510 |
|           8 |       5.124 |       3.259 |   1.865 |         6.437 |     1229 |
|          10 |       5.68  |       3.345 |   2.335 |         1.46  |      275 |
|          12 |       7.558 |       3.365 |   4.193 |         0.332 |       62 |
|          14 |       8.333 |       3.377 |   4.956 |         0.046 |        9 |
|          16 |     nan     |       3.379 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **30,328** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.322 | 6861 |         1.779 |          2.104 |  0.325 |
|         1 |    2.322 |    3.467 | 6971 |         2.984 |          3.074 |  0.09  |
|         2 |    3.468 |    4.651 | 7232 |         2.691 |          3.143 |  0.453 |
|         3 |    4.656 |    6.017 | 7188 |         4.188 |          4.536 |  0.348 |
|         4 |    6.018 |   15.044 | 7547 |         3.873 |          5.008 |  1.135 |

Train lift **+0.134 pp** · pooled test lift **+0.480 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.431, +0.356]** pp.

**Clears the noise band** — SP-target-barrel carries HR signal beyond barrel rate. This is the one that could earn a weight; watch it hold across weekly recalibrations before you trust it.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.