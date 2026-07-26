"""
test_leakage.py — the two tests that matter, on fabricated pitches.

1. LEAKAGE. A batter who barrels nothing until date D and barrels
   everything on D must score identically on D to a batter who barrels
   nothing at all. If same-day contact reaches the grid, this fails.

2. MATH. Zone Fit on a hand-built two-zone case must equal the value
   worked out by hand from the shrinkage formula.

Run: python3 test_leakage.py     (no network, no cache, no Savant)
"""
import numpy as np
import pandas as pd

import hbz_core as C


def pitch(dt, gpk, ab, pn, bat, pit, stand, zone, la=None, lsa=None,
          ev=None, events=None, topbot="Top"):
    return dict(game_date=dt, game_pk=gpk, at_bat_number=ab, pitch_number=pn,
                batter=bat, pitcher=pit, stand=stand, p_throws="R", zone=zone,
                launch_speed=ev, launch_angle=la, launch_speed_angle=lsa,
                hc_x=None, hc_y=None, events=events, description="x",
                inning_topbot=topbot)


def build(rows):
    return C.annotate(pd.DataFrame(rows))


def test_leakage():
    rows, ab = [], 0
    # Batters 1 and 2: IDENTICAL prior history — 60 in-zone BBE, 6 barrels,
    # so p0 is well defined and equal for both.
    for bat in (1, 2):
        for d in ["2026-04-01", "2026-04-02", "2026-04-03"]:
            for i in range(20):
                ab += 1
                rows.append(pitch(d, 100, ab, 1, bat, 900, "R", 5,
                                  la=25 if i < 2 else 12,
                                  lsa=6 if i < 2 else 1,
                                  ev=104 if i < 2 else 88,
                                  events="double" if i < 2 else "single"))
    for i in range(20):
        ab += 1
        rows.append(pitch("2026-04-10", 200, ab, 1, 2, 900, "R", 5, la=28,
                          lsa=6, ev=105, events="home_run"))
    # Batter 1 also plays the test day, no barrels.
    for i in range(20):
        ab += 1
        rows.append(pitch("2026-04-10", 200, ab, 1, 1, 900, "R", 5, la=12,
                          lsa=1, ev=88, events="single"))
    # Pitcher location history so f_z exists.
    for d in ["2026-04-01", "2026-04-02", "2026-04-03"]:
        for i in range(50):
            ab += 1
            rows.append(pitch(d, 100, ab, 1, 3, 900, "R", 5))

    p = build(rows)
    sc = C.build_scored(p, [50])
    day = sc[sc["game_date"] == pd.Timestamp("2026-04-10")]
    a = day[day["batter"] == 1]["zf_index_k50"].iat[0]
    b = day[day["batter"] == 2]["zf_index_k50"].iat[0]
    assert np.isclose(a, b), f"LEAKAGE: same-day barrels changed the score ({a} vs {b})"
    n1 = day[day["batter"] == 2]["bat_n"].iat[0]
    assert n1 == 60, f"prior in-zone BBE should be 60, got {n1}"
    print(f"  leakage    OK   both batters index {a:.2f}, prior BBE {n1:.0f}")


def test_math():
    rows, ab = [], 0
    # Batter 7: zone 1 -> 10 BBE / 5 barrels. zone 9 -> 10 BBE / 0 barrels.
    for i in range(10):
        ab += 1
        rows.append(pitch("2026-05-01", 300, ab, 1, 7, 901, "R", 1, la=25,
                          lsa=6 if i < 5 else 1, ev=104, events="double"))
    for i in range(10):
        ab += 1
        rows.append(pitch("2026-05-01", 300, ab, 1, 7, 901, "R", 9, la=12,
                          lsa=1, ev=88, events="single"))
    # Pitcher 901: 75 pitches to zone 1, 25 to zone 9, vs RHB.
    for i in range(75):
        ab += 1
        rows.append(pitch("2026-05-01", 300, ab, 1, 8, 901, "R", 1))
    for i in range(25):
        ab += 1
        rows.append(pitch("2026-05-01", 300, ab, 1, 8, 901, "R", 9))
    # The graded game, next day.
    ab += 1
    rows.append(pitch("2026-05-02", 301, ab, 1, 7, 901, "R", 1, la=20, lsa=2,
                      ev=95, events="flyout"))

    p = build(rows)
    sc = C.build_scored(p, [10])
    r = sc[(sc["game_date"] == pd.Timestamp("2026-05-02")) & (sc["batter"] == 7)].iloc[0]

    k, p0 = 10, 5 / 20
    b1 = (5 + k * p0) / (10 + k)          # zone 1, shrunk
    b9 = (0 + k * p0) / (10 + k)          # zone 9, shrunk
    rest = (0 + k * p0) / (0 + k)         # untouched zones == p0
    # Pitcher 901's in-zone totals include the pitches he threw to batter 7:
    # zone 1 -> 75 + 10 = 85, zone 9 -> 25 + 10 = 35, total 120.
    f = {1: 85 / 120, 9: 35 / 120}
    want_abs = b1 * f[1] + b9 * f[9] + rest * 0.0
    want_idx = want_abs / p0 * 100

    assert np.isclose(r["p0"], p0), f"p0 {r['p0']} != {p0}"
    assert np.isclose(r["zf_abs_k10"], want_abs), f"abs {r['zf_abs_k10']} != {want_abs}"
    assert np.isclose(r["zf_index_k10"], want_idx), f"idx {r['zf_index_k10']} != {want_idx}"
    print(f"  math       OK   p0 {p0:.3f}  abs {want_abs:.5f}  index {want_idx:.2f}")


def test_outcomes():
    rows, ab = [], 0
    for i in range(4):
        ab += 1
        rows.append(pitch("2026-06-01", 400, ab, 1, 11, 902, "L", 5, la=30,
                          lsa=6, ev=106,
                          events="home_run" if i < 2 else "flyout"))
    p = build(rows)
    mu = C.matchups(p)
    r = mu.iloc[0]
    assert r["pa"] == 4 and r["hr"] == 2, f"pa/hr wrong: {r['pa']}/{r['hr']}"
    assert r["starter"] == 902, "starter not derived from first pitch"
    print(f"  outcomes   OK   pa {r['pa']}  hr {r['hr']}  starter {r['starter']}")


if __name__ == "__main__":
    print("hbz_core smoke tests")
    test_leakage()
    test_math()
    test_outcomes()
    print("all passed")
