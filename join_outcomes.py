"""
join_outcomes.py — grade the frozen snapshots.

    python3 join_outcomes.py            # every ungraded snapshot before today

For each snapshot older than today, pulls that day's completed pitch data,
computes PA and HR against the pitcher who actually started, and joins it
onto the pre-game rows. Output is appended to ledger.csv.

The ledger is the honest scoreboard. Nothing in it was computed with
knowledge of the outcome: the Zone Fit index was written to disk before
first pitch, and this script only ever adds the result column. When the
ledger is large enough it replaces the backfill as the primary evidence —
calibrate.py reads either.

A snapshot row that never turned into a PA (scratched, pinch-hit only,
rained out) is kept with pa = 0. Dropping them would quietly select on
playing time, which correlates with the very metrics being graded.
"""

import argparse
import os
from datetime import date

import pandas as pd

import hbz_core as C


def graded_dates(ledger: str) -> set[str]:
    if not os.path.exists(ledger):
        return set()
    d = pd.read_csv(ledger, usecols=["game_date"])
    return set(pd.to_datetime(d["game_date"]).dt.date.astype(str))


def grade_day(day: str, snap_path: str, raw_dir: str) -> pd.DataFrame | None:
    snap = pd.read_csv(snap_path)
    if not len(snap):
        return None
    snap["game_date"] = pd.to_datetime(snap["game_date"])

    raw = C.fetch_day(day, cache_dir=raw_dir)
    if not len(raw):
        print(f"  {day}  no pitch data (postponed?) — skipped")
        return None

    p = C.annotate(raw)
    actual = C.matchups(p)[["batter", "starter", "pa", "hr", "bbe"]]

    out = snap.drop(columns=[c for c in ("pa", "hr", "bbe") if c in snap.columns])
    out = out.merge(actual, on=["batter", "starter"], how="left")

    # Projected-roster rows that never batted against the starter.
    out[["pa", "hr", "bbe"]] = out[["pa", "hr", "bbe"]].fillna(0)
    out["played"] = out["pa"] > 0
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", default="snapshots")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--ledger", default="ledger.csv")
    args = ap.parse_args()

    if not os.path.isdir(args.snapshots):
        print(f"No {args.snapshots}/ yet — run collect_daily.py first.")
        return

    done = graded_dates(args.ledger)
    today = date.today().isoformat()
    pending = sorted(f[:-4] for f in os.listdir(args.snapshots)
                     if f.endswith(".csv") and f[:-4] < today and f[:-4] not in done)

    if not pending:
        print("Nothing to grade.")
        return

    frames = []
    for day in pending:
        g = grade_day(day, os.path.join(args.snapshots, f"{day}.csv"), args.raw)
        if g is None:
            continue
        frames.append(g)
        print(f"  {day}  {len(g):>4} rows  ·  PA {int(g['pa'].sum()):>4}  ·  "
              f"HR {int(g['hr'].sum()):>3}  ·  played {int(g['played'].sum()):>4}")

    if not frames:
        print("No gradeable days.")
        return

    new = pd.concat(frames, ignore_index=True)
    if os.path.exists(args.ledger):
        new = pd.concat([pd.read_csv(args.ledger), new], ignore_index=True)
    new.to_csv(args.ledger, index=False)

    pa, hr = new["pa"].sum(), new["hr"].sum()
    print(f"\nLedger: {len(new):,} rows · PA {int(pa):,} · HR {int(hr):,} · "
          f"HR/PA {hr / pa * 100:.2f}%" if pa else "\nLedger written (no PA yet).")
    print(f"Wrote {args.ledger}")


if __name__ == "__main__":
    main()
