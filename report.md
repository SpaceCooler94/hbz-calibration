# HHBarrelZone calibration

Window **2026-03-26 .. 2026-07-25**, split at **2026-06-05** (first 60% of game dates trains, last 40% reports).

- matchups **27,830** · PA **67,836** · HR **2,190** · base HR/PA **3.23%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **11,193**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |       -0.232 |
|  25 |       -0.153 |
|  50 |       -0.565 |
| 100 |       -0.593 |
| 200 |       -0.383 |

Chosen **k = 25**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.179 |    2.529 | 3615 |         2.748 |          2.912 |  0.164 |
|         1 |    2.532 |    3.662 | 3779 |         2.752 |          3.662 |  0.911 |
|         2 |    3.665 |    4.73  | 3875 |         2.791 |          3.849 |  1.058 |
|         3 |    4.732 |    6.28  | 3848 |         5.3   |          4.114 | -1.186 |
|         4 |    6.281 |   15.044 | 4027 |         4.201 |          5.804 |  1.603 |

Pooled test lift: **+0.524 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.003, 5-95% band **[-0.500, +0.534]** pp.

**Measured lift sits inside the noise band.** On this sample Zone Fit is not distinguishable from a shuffled column — it should not move a price.

### Observed index distribution

|    p10 |    p25 |    p50 |     p75 |     p90 |
|-------:|-------:|-------:|--------:|--------:|
| 93.922 | 97.149 | 99.951 | 102.666 | 105.551 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.148 |       3.433 |   1.714 |         3.653 |      384 |
|          36 |       5.067 |       3.475 |   1.591 |         1.306 |      136 |
|          38 |       6.25  |       3.485 |   2.765 |         0.39  |       41 |
|          40 |       8.108 |       3.49  |   4.618 |         0.129 |       14 |
|          42 |      33.333 |       3.493 |  29.84  |         0.01  |        1 |
|          44 |     nan     |       3.496 | nan     |         0     |        0 |
|          46 |     nan     |       3.496 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.737 |       3.083 |   1.654 |        24.995 |     2680 |
|           8 |       5.728 |       3.288 |   2.44  |         8.51  |      894 |
|          10 |       6.412 |       3.436 |   2.976 |         2.009 |      210 |
|          12 |       7.843 |       3.473 |   4.37  |         0.533 |       55 |
|          14 |       8.333 |       3.492 |   4.841 |         0.084 |        9 |
|          16 |     nan     |       3.496 | nan     |         0     |        0 |

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.