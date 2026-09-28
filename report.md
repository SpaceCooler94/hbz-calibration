# HHBarrelZone calibration

Window **2026-03-26 .. 2026-09-27**, split at **2026-07-16** (first 60% of game dates trains, last 40% reports).

- matchups **42,954** · PA **103,864** · HR **3,334** · base HR/PA **3.21%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **23,141**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |        0.47  |
|  25 |        0.387 |
|  50 |        0.269 |
| 100 |        0.321 |
| 200 |        0.257 |

Chosen **k = 10**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.154 |    2.337 | 6346 |         2.235 |          2.1   | -0.135 |
|         1 |    2.339 |    3.442 | 6443 |         2.441 |          2.936 |  0.494 |
|         2 |    3.443 |    4.643 | 6695 |         2.361 |          3.712 |  1.351 |
|         3 |    4.644 |    5.991 | 6697 |         4.381 |          4.29  | -0.091 |
|         4 |    5.991 |   14.53  | 7002 |         2.71  |          4.284 |  1.574 |

Pooled test lift: **+0.657 pp**

Permutation null (200 seeded shuffles within stratum): mean +0.002, 5-95% band **[-0.356, +0.407]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=10.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |   p90 |
|-------:|-------:|-------:|--------:|------:|
| 90.008 | 94.571 | 98.845 | 103.062 | 107.7 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.043 |       3.287 |   1.756 |         2.846 |      609 |
|          36 |       5.535 |       3.316 |   2.219 |         0.937 |      195 |
|          38 |       6.25  |       3.331 |   2.919 |         0.194 |       41 |
|          40 |       8.108 |       3.334 |   4.774 |         0.064 |       14 |
|          42 |      33.333 |       3.335 |  29.998 |         0.005 |        1 |
|          44 |     nan     |       3.337 | nan     |         0     |        0 |
|          46 |     nan     |       3.337 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.383 |       3.028 |   1.355 |        22.8   |     5018 |
|           8 |       5.129 |       3.22  |   1.909 |         6.101 |     1307 |
|          10 |       5.563 |       3.307 |   2.256 |         1.336 |      281 |
|          12 |       7.558 |       3.324 |   4.234 |         0.297 |       62 |
|          14 |       8.333 |       3.335 |   4.999 |         0.041 |        9 |
|          16 |     nan     |       3.337 | nan     |         0     |        0 |

## 1b. Does SP-target-barrel add anything to barrel rate?

Same test as Zone Fit: lift of the top vs bottom SP-target bin, within barrel strata, PA-weighted. The feature is the hitter's barrel rate on this starter's vulnerable pitches (usage × barrel-allowed), as a tilt off his own barrel base.

Confident rows (batter arsenal BBE ≥ 80, coverage ≥ 40%): **33,350** · shrink batter k=60, pitcher k=40.

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0     |    2.301 | 7234 |         1.532 |          2.086 |  0.554 |
|         1 |    2.301 |    3.419 | 7340 |         2.893 |          2.536 | -0.357 |
|         2 |    3.42  |    4.627 | 7578 |         2.61  |          3.219 |  0.609 |
|         3 |    4.628 |    5.983 | 7617 |         4.116 |          4.399 |  0.284 |
|         4 |    5.985 |   14.53  | 7966 |         3.678 |          4.173 |  0.495 |

Train lift **+0.506 pp** · pooled test lift **+0.321 pp**.

Permutation null (200 seeded shuffles): 5-95% band **[-0.323, +0.333]** pp.

**Inside the noise band.** On this sample the SP-target read is not distinguishable from a shuffled column — the screener is useful for finding candidates, but the specific number does not beat barrel rate and should not move a price.

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.