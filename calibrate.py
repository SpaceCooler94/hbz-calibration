"""
calibrate.py — grade Zone Fit and the gate thresholds against outcomes.

    python3 calibrate.py --scored data/scored.parquet

The question is NOT "does Zone Fit correlate with home runs" — good
hitters have both a high index and a lot of home runs, so that test passes
even if the metric is a repackaged barrel rate. The question is whether it
still separates HR/PA *inside* a barrel-rate decile. If it does not, it
adds nothing to what the board already knows and it should be deleted.

Design choices that keep this honest:

  CHRONOLOGICAL SPLIT, not random CV. k is chosen on the first 60% of game
  dates and reported on the last 40%. Random folds leak: the same hitter's
  hot streak lands on both sides.

  SEEDED PERMUTATION FLOOR. Zone Fit is shuffled within barrel decile 200
  times to build a null distribution of the lift statistic. A measured
  lift inside that band is noise, no matter how good it looks. Seed fixed
  so the number is reproducible.

  PA-WEIGHTED throughout. A matchup with 5 PA is worth more than one with 1.

Outputs:
  calibration.json  — chosen k, band cutpoints, gate curves, provenance
  report.md         — the tables, for reading before trusting any of it
"""

import argparse
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

N_DECILES = 5          # barrel-rate strata. 5 keeps cells populated.
N_ZF_BINS = 3          # Zone Fit bins within each stratum.
N_PERM = 200
SEED = 20260725


# ── helpers ──────────────────────────────────────────────────────────
def hr_per_pa(df: pd.DataFrame) -> float:
    pa = df["pa"].sum()
    return float(df["hr"].sum() / pa * 100) if pa else np.nan


def strata(df: pd.DataFrame, col: str, n: int) -> pd.Series:
    """PA-weighted-ish quantile bins, tolerant of ties."""
    try:
        return pd.qcut(df[col], n, labels=False, duplicates="drop")
    except ValueError:
        return pd.Series(np.zeros(len(df)), index=df.index)


def within_lift(df: pd.DataFrame, zf_col: str) -> tuple[float, pd.DataFrame]:
    """PA-weighted mean of (top ZF bin - bottom ZF bin) HR/PA, within strata.

    This is the whole test in one number: the marginal contribution of
    Zone Fit after barrel rate has already been accounted for.
    """
    d = df.dropna(subset=[zf_col, "brl_pct"]).copy()
    if d.empty:
        return np.nan, pd.DataFrame()
    d["stratum"] = strata(d, "brl_pct", N_DECILES)
    rows, num, den = [], 0.0, 0.0
    for s, g in d.groupby("stratum", observed=True):
        if len(g) < 3 * N_ZF_BINS:
            continue
        g = g.copy()
        g["zfbin"] = strata(g, zf_col, N_ZF_BINS)
        bins = sorted(g["zfbin"].dropna().unique())
        if len(bins) < 2:
            continue
        lo, hi = g[g["zfbin"] == bins[0]], g[g["zfbin"] == bins[-1]]
        d_lift = hr_per_pa(hi) - hr_per_pa(lo)
        w = float(g["pa"].sum())
        rows.append({
            "stratum": int(s),
            "brl_lo": float(g["brl_pct"].min()), "brl_hi": float(g["brl_pct"].max()),
            "pa": int(w),
            "hrpa_zf_low": hr_per_pa(lo), "hrpa_zf_high": hr_per_pa(hi),
            "lift": d_lift,
        })
        if np.isfinite(d_lift):
            num += d_lift * w
            den += w
    return (num / den if den else np.nan), pd.DataFrame(rows)


def perm_floor(df: pd.DataFrame, zf_col: str, n_perm: int = N_PERM) -> dict:
    """Null band for the lift statistic: shuffle Zone Fit inside each stratum."""
    d = df.dropna(subset=[zf_col, "brl_pct"]).copy()
    if d.empty:
        return {}
    d["stratum"] = strata(d, "brl_pct", N_DECILES)
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(n_perm):
        s = d.copy()
        s[zf_col] = (s.groupby("stratum", observed=True)[zf_col]
                       .transform(lambda x: rng.permutation(x.to_numpy())))
        v, _ = within_lift(s, zf_col)
        if np.isfinite(v):
            out.append(v)
    if not out:
        return {}
    a = np.array(out)
    return {"n": len(a), "mean": float(a.mean()), "sd": float(a.std(ddof=1)),
            "p05": float(np.percentile(a, 5)), "p95": float(np.percentile(a, 95))}


def gate_sweep(df: pd.DataFrame, col: str, grid: list[float]) -> pd.DataFrame:
    """For each candidate threshold: HR/PA kept vs cut, and what it costs."""
    d = df.dropna(subset=[col])
    tot_pa = d["pa"].sum()
    rows = []
    for t in grid:
        keep, cut = d[d[col] >= t], d[d[col] < t]
        rows.append({
            "threshold": t,
            "hrpa_pass": hr_per_pa(keep), "hrpa_fail": hr_per_pa(cut),
            "edge": hr_per_pa(keep) - hr_per_pa(cut),
            "pa_kept_pct": float(keep["pa"].sum() / tot_pa * 100) if tot_pa else np.nan,
            "n_pass": int(len(keep)),
        })
    return pd.DataFrame(rows)


def fmt(df: pd.DataFrame, floats: int = 3) -> str:
    if df.empty:
        return "_(no rows)_\n"
    return df.round(floats).to_markdown(index=False) + "\n"


# ── main ─────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", default="data/scored.parquet")
    ap.add_argument("--out-json", default="calibration.json")
    ap.add_argument("--out-report", default="report.md")
    ap.add_argument("--min-bat-bbe", type=int, default=80)
    ap.add_argument("--min-pit", type=int, default=150)
    args = ap.parse_args()

    df = pd.read_parquet(args.scored)
    df["game_date"] = pd.to_datetime(df["game_date"])
    ks = sorted(int(c.split("_k")[1]) for c in df.columns if c.startswith("zf_index_k"))

    total_pa, total_hr = int(df["pa"].sum()), int(df["hr"].sum())
    base = hr_per_pa(df)

    # Confidence floors: the same ones the board uses to dash a Zone Fit row.
    conf = df[(df["bat_n"] >= args.min_bat_bbe) & (df["pit_n"] >= args.min_pit)].copy()

    dates = np.sort(df["game_date"].unique())
    cut = dates[int(len(dates) * 0.60)]
    train, test = conf[conf["game_date"] < cut], conf[conf["game_date"] >= cut]

    # k sweep on train only
    sweep = []
    for k in ks:
        v, _ = within_lift(train, f"zf_index_k{k}")
        sweep.append({"k": k, "train_lift": v})
    sweep_df = pd.DataFrame(sweep)
    finite = sweep_df.dropna(subset=["train_lift"])
    k_star = int(finite.loc[finite["train_lift"].idxmax(), "k"]) if len(finite) else ks[0]

    zf = f"zf_index_k{k_star}"
    test_lift, test_tbl = within_lift(test, zf)
    train_lift, train_tbl = within_lift(train, zf)
    null = perm_floor(test, zf)

    passes = bool(null and np.isfinite(test_lift) and test_lift > null.get("p95", np.inf))

    # Observed index distribution -> band cutpoints, so the board's colour
    # bands are percentiles of what actually occurs rather than 95/105/115
    # picked out of the air.
    q = conf[zf].dropna()
    bands = {f"p{p}": float(np.percentile(q, p)) for p in (10, 25, 50, 75, 90)} if len(q) else {}

    gates = {
        "hh_pct": gate_sweep(conf, "hh_pct", [34, 36, 38, 40, 42, 44, 46]),
        "brl_pct": gate_sweep(conf, "brl_pct", [6, 8, 10, 12, 14, 16]),
    }

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": args.scored,
        "window": {"start": str(df["game_date"].min().date()),
                   "end": str(df["game_date"].max().date()),
                   "split_date": str(pd.Timestamp(cut).date())},
        "sample": {"matchups": int(len(df)), "pa": total_pa, "hr": total_hr,
                   "hr_per_pa_pct": base,
                   "confident_matchups": int(len(conf)),
                   "min_bat_bbe": args.min_bat_bbe, "min_pit": args.min_pit},
        "zone_fit": {
            "k_grid": ks, "k_star": k_star,
            "train_lift_hrpa_pp": train_lift,
            "test_lift_hrpa_pp": test_lift,
            "null_band": null,
            "beats_noise": passes,
            "index_percentiles": bands,
            "verdict": ("keep as tie-breaker" if passes else
                        "no measurable marginal edge — do not weight it"),
        },
        "gates": {k: v.to_dict(orient="records") for k, v in gates.items()},
    }
    with open(args.out_json, "w") as f:
        json.dump(payload, f, indent=2, default=float)

    lines = [
        "# HHBarrelZone calibration",
        "",
        f"Window **{payload['window']['start']} .. {payload['window']['end']}**, "
        f"split at **{payload['window']['split_date']}** "
        f"(first 60% of game dates trains, last 40% reports).",
        "",
        f"- matchups **{len(df):,}** · PA **{total_pa:,}** · HR **{total_hr:,}** · "
        f"base HR/PA **{base:.2f}%**",
        f"- confident rows (bat in-zone BBE ≥ {args.min_bat_bbe}, "
        f"pitcher in-zone pitches ≥ {args.min_pit}): **{len(conf):,}**",
        "",
        "## 1. Does Zone Fit add anything to barrel rate?",
        "",
        "Lift = (HR/PA in the top Zone Fit bin) − (bottom bin), measured "
        "*within* barrel-rate strata and PA-weighted. Units are percentage "
        "points of HR/PA.",
        "",
        "### k sweep (train only)",
        "",
        fmt(sweep_df),
        f"Chosen **k = {k_star}**.",
        "",
        "### Holdout, at the chosen k",
        "",
        fmt(test_tbl),
        f"Pooled test lift: **{test_lift:+.3f} pp**",
        "",
    ]
    if null:
        lines += [
            f"Permutation null ({null['n']} seeded shuffles within stratum): "
            f"mean {null['mean']:+.3f}, 5-95% band "
            f"**[{null['p05']:+.3f}, {null['p95']:+.3f}]** pp.",
            "",
            (f"**Measured lift clears the noise band.** Zone Fit carries "
             f"marginal information at k={k_star}."
             if passes else
             "**Measured lift sits inside the noise band.** On this sample "
             "Zone Fit is not distinguishable from a shuffled column — it "
             "should not move a price."),
            "",
        ]
    lines += [
        "### Observed index distribution",
        "",
        fmt(pd.DataFrame([bands])) if bands else "_(none)_\n",
        "Use these percentiles for the board's colour bands instead of "
        "hand-picked 95/105/115 cutpoints.",
        "",
        "## 2. Gate thresholds",
        "",
        "`edge` is HR/PA above the threshold minus below. `pa_kept_pct` is "
        "what survives — a gate that buys 0.1 pp of edge by deleting 70% of "
        "the slate is not a good trade.",
        "",
        "### Hard-hit%",
        "",
        fmt(gates["hh_pct"]),
        "### Barrel%",
        "",
        fmt(gates["brl_pct"]),
        "---",
        "",
        "Grids are built strictly from pitches before each game date "
        "(`merge_asof(allow_exact_matches=False)`); `test_leakage.py` asserts it.",
        "",
        "HR/PA against starters only. Reliever PAs are excluded — Zone Fit "
        "never claimed to price them.",
    ]
    with open(args.out_report, "w") as f:
        f.write("\n".join(lines))

    print(f"k* = {k_star}   train {train_lift:+.3f} pp   test {test_lift:+.3f} pp")
    if null:
        print(f"null 5-95%: [{null['p05']:+.3f}, {null['p95']:+.3f}]  "
              f"-> {'BEATS NOISE' if passes else 'inside noise'}")
    print(f"wrote {args.out_json}, {args.out_report}")


if __name__ == "__main__":
    main()
