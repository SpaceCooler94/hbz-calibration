# HHBarrelZone calibration

Window **2026-03-26 .. 2026-08-23**, split at **2026-06-22** (first 60% of game dates trains, last 40% reports).

- matchups **34,847** · PA **84,872** · HR **2,723** · base HR/PA **3.21%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **16,723**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.505 |
|  25 |        0.418 |
|  50 |        0.184 |
| 100 |        0.114 |
| 200 |        0.136 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.159 |    2.415 | 5098 |         2.774 |          2.693 | -0.081 |
|         1 |    2.416 |    3.578 | 5223 |         2.834 |          3.118 |  0.283 |
|         2 |    3.579 |    4.68  | 5357 |         2.115 |          3.672 |  1.558 |
|         3 |    4.68  |    6.087 | 5386 |         4.431 |          4.937 |  0.506 |
|         4 |    6.09  |   15.044 | 5657 |         3.573 |          4.254 |  0.681 |

Pooled test lift: **+0.598 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.001, 5-95% band **[-0.479, +0.439]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 89.686 | 94.468 | 98.804 | 103.089 | 107.695 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.387 |       3.323 |   2.064 |         3.111 |      481 |
|          36 |       5.568 |       3.364 |   2.204 |         1.06  |      162 |
|          38 |       6.25  |       3.379 |   2.871 |         0.264 |       41 |
|          40 |       8.108 |       3.383 |   4.725 |         0.087 |       14 |
|          42 |      33.333 |       3.385 |  29.948 |         0.007 |        1 |
|          44 |     nan     |       3.387 | nan     |         0     |        0 |
|          46 |     nan     |       3.387 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.521 |       3.038 |   1.483 |        23.546 |     3751 |
|           8 |       5.286 |       3.242 |   2.044 |         7.1   |     1107 |
|          10 |       6.017 |       3.343 |   2.674 |         1.647 |      254 |
|          12 |       7.558 |       3.37  |   4.188 |         0.406 |       62 |
|          14 |       8.333 |       3.384 |   4.949 |         0.057 |        9 |
|          16 |     nan     |       3.387 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **25,783** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.353 | 5931 |         2.054 |          2.491 |  0.437 |
|         1 |    2.355 |    3.543 | 6045 |         2.667 |          2.929 |  0.262 |
|         2 |    3.544 |    4.659 | 6212 |         2.519 |          2.79  |  0.27  |
|         3 |    4.66  |    6.087 | 6256 |         3.661 |          4.269 |  0.609 |
|         4 |    6.09  |   15.044 | 6544 |         4.039 |          4.747 |  0.708 |

Train lift **+0.373 pp** · pooled test lift **+0.461 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.355, +0.402]** pp.

**Clears the noise band** — SP-target-barrel carries HR signal beyond barrel rate. This is the one that could earn a weight; watch it hold across weekly recalibrations before you trust it.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.