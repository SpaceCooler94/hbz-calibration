"""
backfill.py — reconstruct the season and score every starter matchup as of
its own game date.

    python3 backfill.py --start 2026-03-26 --end 2026-07-24

Writes data/scored.parquet: one row per (date, batter, starting pitcher),
carrying the Zone Fit index at every k, the leakage-safe season-to-date
control metrics, and the realised PA / HR.

First run is ~120 requests at one per second plus parse; expect 10-20
minutes and roughly 1-2 GB of cached parquet. Every day is cached
permanently, so re-runs are seconds. This is the step that does not belong
on a phone — it belongs in Actions, which is where the workflow puts it.
"""

import argparse
import os

import pandas as pd

import hbz_core as C

K_VALUES = [10, 25, 50, 100, 200]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/scored.parquet")
    ap.add_argument("--k", default=",".join(str(k) for k in K_VALUES))
    args = ap.parse_args()

    ks = [int(x) for x in args.k.split(",")]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    print(f"Loading {args.start} .. {args.end}")
    pitches = C.load_range(args.start, args.end, cache_dir=args.raw)
    print(f"{len(pitches):,} pitches, {pitches['game_date'].nunique()} game dates")

    p = C.annotate(pitches)
    print(f"{int(p['is_bbe'].sum()):,} BBE  ·  {int(p['is_hr'].sum()):,} HR  ·  "
          f"{int(p['in_zone'].sum()):,} in-zone pitches")

    scored = C.build_scored(p, ks)

    # Rows before a batter has any prior in-zone contact carry no p0 and so
    # no index. They stay in the file, flagged, rather than being dropped —
    # the share of the season that is unscoreable is itself a finding.
    scored["scoreable"] = scored[f"zf_index_k{ks[0]}"].notna()
    scored.to_parquet(args.out, index=False)

    n, ok = len(scored), int(scored["scoreable"].sum())
    print(f"\nWrote {args.out}")
    print(f"  matchups        {n:,}")
    print(f"  scoreable       {ok:,}  ({ok / n * 100:.1f}%)")
    print(f"  PA              {int(scored['pa'].sum()):,}")
    print(f"  HR              {int(scored['hr'].sum()):,}")
    print(f"  HR/PA           {scored['hr'].sum() / scored['pa'].sum() * 100:.2f}%")
    print(f"  date range      {scored['game_date'].min().date()} .. "
          f"{scored['game_date'].max().date()}")


if __name__ == "__main__":
    main()
