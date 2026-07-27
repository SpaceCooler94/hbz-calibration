# HHBarrelZone calibration

Window **2026-03-26 .. 2026-07-26**, split at **2026-06-06** (first 60% of game dates trains, last 40% reports).

- matchups **28,102** · PA **68,468** · HR **2,212** · base HR/PA **3.23%**
- confident rows (bat in-zone BBE ≥ 80, pitcher in-zone pitches ≥ 150): **11,416**

## 1. Does Zone Fit add anything to barrel rate?

Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured *within* barrel-rate strata and PA-weighted. Units are percentage points of HR/PA.

### k sweep (train only)

|   k |   train_lift |
|----:|-------------:|
|  10 |       -0.346 |
|  25 |       -0.18  |
|  50 |       -0.545 |
| 100 |       -0.601 |
| 200 |       -0.432 |

Chosen **k = 25**.

### Holdout, at the chosen k

|   stratum |   brl_lo |   brl_hi |   pa |   hrpa_zf_low |   hrpa_zf_high |   lift |
|----------:|---------:|---------:|-----:|--------------:|---------------:|-------:|
|         0 |    0.179 |    2.532 | 3644 |         2.558 |          2.975 |  0.417 |
|         1 |    2.534 |    3.659 | 3808 |         2.81  |          3.639 |  0.829 |
|         2 |    3.662 |    4.732 | 3898 |         2.628 |          3.755 |  1.127 |
|         3 |    4.734 |    6.272 | 3882 |         5.093 |          4.173 | -0.919 |
|         4 |    6.275 |   15.044 | 4055 |         4.086 |          5.865 |  1.779 |

Pooled test lift: **+0.659 pp**

Permutation null (200 seeded shuffles within stratum): mean -0.001, 5-95% band **[-0.529, +0.566]** pp.

**Measured lift clears the noise band.** Zone Fit carries marginal information at k=25.

### Observed index distribution

|   p10 |   p25 |   p50 |    p75 |     p90 |
|------:|------:|------:|-------:|--------:|
| 93.91 | 97.13 | 99.95 | 102.67 | 105.579 |

Use these percentiles for the board's colour bands instead of hand-picked 95/105/115 cutpoints.

## 2. Gate thresholds

`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is what survives — a gate that buys 0.1 pp of edge by deleting 70% of the slate is not a good trade.

### Hard-hit%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|          34 |       5.118 |       3.424 |   1.695 |         3.608 |      386 |
|          36 |       5.067 |       3.464 |   1.602 |         1.282 |      136 |
|          38 |       6.25  |       3.474 |   2.776 |         0.383 |       41 |
|          40 |       8.108 |       3.479 |   4.629 |         0.127 |       14 |
|          42 |      33.333 |       3.482 |  29.852 |         0.01  |        1 |
|          44 |     nan     |       3.485 | nan     |         0     |        0 |
|          46 |     nan     |       3.485 | nan     |         0     |        0 |

### Barrel%

|   threshold |   hrpa_pass |   hrpa_fail |    edge |   pa_kept_pct |   n_pass |
|------------:|------------:|------------:|--------:|--------------:|---------:|
|           6 |       4.708 |       3.079 |   1.629 |        24.914 |     2725 |
|           8 |       5.74  |       3.276 |   2.463 |         8.461 |      907 |
|          10 |       6.563 |       3.423 |   3.14  |         1.98  |      211 |
|          12 |       8.387 |       3.459 |   4.928 |         0.53  |       56 |
|          14 |       8.333 |       3.481 |   4.852 |         0.082 |        9 |
|          16 |     nan     |       3.485 | nan     |         0     |        0 |

---

Grids are built strictly from pitches before each game date (`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.

HR/PA against starters only. Reliever PAs are excluded — Zone Fit never claimed to price them.