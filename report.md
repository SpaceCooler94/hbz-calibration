# HHBarrelZone calibration

Window **2026-03-26 .. 2026-08-02**, split at **2026-06-10** (first 60% of game dates trains, last 40% reports).

- matchups **29,822** · PA **72,636** · HR **2,338** · base HR/PA **3.22%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **12,767**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |       -0.062 |
|  25 |       -0.018 |
|  50 |       -0.263 |
| 100 |       -0.285 |
| 200 |       -0.241 |

Chosen **k = 25**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.179 |    2.516 | 4036 |         2.528 |          3.06  |  0.532 |
|         1 |    2.521 |    3.642 | 4181 |         2.843 |          3.613 |  0.77  |
|         2 |    3.643 |    4.732 | 4299 |         2.568 |          3.556 |  0.989 |
|         3 |    4.734 |    6.218 | 4280 |         4.596 |          4.066 | -0.53  |
|         4 |    6.219 |   15.044 | 4479 |         3.957 |          5.76  |  1.803 |

Pooled test lift: **+0.725 pp**

Permutation null (200 seeded shuffles within stratum): mean +0.002, 5-95% band **[-0.518, +0.475]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=25.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 93.888 | 97.078 | 99.927 | 102.663 | 105.556 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.083 |       3.38  |   1.704 |         3.501 |      418 |
|          36 |       5.013 |       3.42  |   1.593 |         1.224 |      144 |
|          38 |       6.25  |       3.43  |   2.82  |         0.344 |       41 |
|          40 |       8.108 |       3.434 |   4.674 |         0.114 |       14 |
|          42 |      33.333 |       3.437 |  29.897 |         0.009 |        1 |
|          44 |     nan     |       3.439 | nan     |         0     |        0 |
|          46 |     nan     |       3.439 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.683 |       3.036 |   1.647 |        24.505 |     2994 |
|           8 |       5.576 |       3.25  |   2.327 |         8.143 |      974 |
|          10 |       6.2   |       3.385 |   2.815 |         1.93  |      228 |
|          12 |       7.558 |       3.417 |   4.141 |         0.528 |       62 |
|          14 |       8.333 |       3.436 |   4.898 |         0.074 |        9 |
|          16 |     nan     |       3.439 | nan     |         0     |        0 |

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.