# HHBarrelZone calibration

Window **2026-03-26 .. 2026-08-09**, split at **2026-06-14** (first 60% of game dates trains, last 40% reports).

- matchups **31,490** · PA **76,678** · HR **2,462** · base HR/PA **3.21%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **14,061**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.239 |
|  25 |        0.251 |
|  50 |        0.079 |
| 100 |        0.085 |
| 200 |        0.041 |

Chosen **k = 25**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.179 |    2.488 | 4384 |         2.612 |          3.003 |  0.392 |
|         1 |    2.489 |    3.627 | 4502 |         2.785 |          3.571 |  0.786 |
|         2 |    3.628 |    4.703 | 4654 |         2.382 |          3.284 |  0.901 |
|         3 |    4.703 |    6.154 | 4643 |         4.592 |          4.852 |  0.261 |
|         4 |    6.156 |   15.044 | 4870 |         3.772 |          4.856 |  1.083 |

Pooled test lift: **+0.691 pp**

Permutation null (200 seeded shuffles within stratum): mean +0.002, 5-95% band **[-0.441, +0.447]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=25.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 93.847 | 97.035 | 99.891 | 102.655 | 105.584 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.272 |       3.35  |   1.922 |         3.341 |      438 |
|          36 |       5.314 |       3.392 |   1.922 |         1.158 |      150 |
|          38 |       6.25  |       3.405 |   2.845 |         0.313 |       41 |
|          40 |       8.108 |       3.409 |   4.699 |         0.103 |       14 |
|          42 |      33.333 |       3.411 |  29.922 |         0.008 |        1 |
|          44 |     nan     |       3.414 | nan     |         0     |        0 |
|          46 |     nan     |       3.414 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.617 |       3.033 |   1.584 |        24.04  |     3227 |
|           8 |       5.506 |       3.238 |   2.268 |         7.77  |     1022 |
|          10 |       6.279 |       3.361 |   2.918 |         1.826 |      238 |
|          12 |       7.558 |       3.394 |   4.164 |         0.481 |       62 |
|          14 |       8.333 |       3.411 |   4.923 |         0.067 |        9 |
|          16 |     nan     |       3.414 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **22,726** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.4   | 5176 |         2.111 |          2.358 |  0.248 |
|         1 |    2.402 |    3.599 | 5362 |         3.289 |          2.535 | -0.754 |
|         2 |    3.6   |    4.696 | 5502 |         2.31  |          2.761 |  0.451 |
|         3 |    4.697 |    6.144 | 5494 |         3.998 |          4.284 |  0.286 |
|         4 |    6.145 |   15.044 | 5761 |         4.063 |          4.881 |  0.817 |

Train lift **+0.286 pp** · pooled test lift **+0.220 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.468, +0.483]** pp.

**Inside the noise band.** On this sample the SP-target read is not distinguishable from a shuffled column — the screener is useful for finding candidates, but the specific number does not beat barrel rate and should not move a price.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.