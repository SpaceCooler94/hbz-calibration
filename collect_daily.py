"""
collect_daily.py — the forward half of the harness.

    python3 collect_daily.py                    # today
    python3 collect_daily.py --date 2026-07-25

Two jobs, in this order:

  1. Bring the compact aggregates up to date. Any completed day not yet
     in agg/ is fetched once, collapsed to a few kilobytes of counts, and
     committed. The season of raw pitches never has to live in the repo.

  2. Score today's slate off those aggregates and write
     snapshots/<date>.csv — every candidate batter facing a probable
     starter, with the Zone Fit index and the season-to-date control
     metrics AS THEY STOOD THIS MORNING.

The snapshot is the point. It is a frozen record of what was knowable
before the games, so join_outcomes.py can grade it later without any
possibility of hindsight creeping in. The backfill can be argued with;
a prospective snapshot cannot.
"""

import argparse
import os
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import requests

import hbz_core as C

STATSAPI = "https://statsapi.mlb.com/api/v1"
K_VALUES = [10, 25, 50, 100, 200]
AGG_KEYS = ["bat_zone", "bat_base", "pit_zone", "bat_rate"]


# ── aggregates ───────────────────────────────────────────────────────
def agg_path(agg_dir: str, day: str, key: str) -> str:
    return os.path.join(agg_dir, key, f"{day}.parquet")


def update_aggregates(agg_dir: str, start: str, through: str,
                      raw_dir: str = "data/raw") -> None:
    """Fetch and collapse every completed day not already aggregated."""
    for key in AGG_KEYS:
        os.makedirs(os.path.join(agg_dir, key), exist_ok=True)
    for day in C.season_dates(start, through):
        if os.path.exists(agg_path(agg_dir, day, "bat_zone")):
            continue
        try:
            raw = C.fetch_day(day, cache_dir=raw_dir)
        except Exception as e:                                   # noqa: BLE001
            print(f"  {day}  skip ({e})")
            continue
        if not len(raw):
            # Write empty markers so an off-day is not re-fetched forever.
            for key in AGG_KEYS:
                pd.DataFrame().to_parquet(agg_path(agg_dir, day, key), index=False)
            continue
        a = C.aggregate_day(C.annotate(raw))
        for key in AGG_KEYS:
            a[key].to_parquet(agg_path(agg_dir, day, key), index=False)
        print(f"  {day}  aggregated")


def load_aggregates(agg_dir: str) -> dict[str, pd.DataFrame]:
    out = {}
    for key in AGG_KEYS:
        d = os.path.join(agg_dir, key)
        files = sorted(f for f in os.listdir(d) if f.endswith(".parquet"))
        frames = [pd.read_parquet(os.path.join(d, f)) for f in files]
        frames = [f for f in frames if len(f)]
        if not frames:
            raise RuntimeError(f"No aggregates under {d} — run the backfill first.")
        df = pd.concat(frames, ignore_index=True)
        df["game_date"] = pd.to_datetime(df["game_date"])
        out[key] = df
    return out


# ── today's slate ────────────────────────────────────────────────────
def slate(day: str) -> list[dict]:
    url = (f"{STATSAPI}/schedule?sportId=1&date={day}"
           "&hydrate=probablePitcher,lineups,team")
    js = requests.get(url, timeout=60).json()
    games = (js.get("dates") or [{}])[0].get("games", []) if js.get("dates") else []
    out = []
    for g in games:
        for side, other in (("home", "away"), ("away", "home")):
            me, opp = g["teams"][side], g["teams"][other]
            sp = opp.get("probablePitcher")
            if not sp:
                continue
            lineup = (g.get("lineups") or {}).get(f"{side}Players") or []
            out.append({
                "team": me["team"].get("abbreviation") or me["team"]["name"],
                "opp": opp["team"].get("abbreviation") or opp["team"]["name"],
                "team_id": me["team"]["id"],
                "starter": sp["id"], "starter_name": sp["fullName"],
                "lineup": [p["id"] for p in lineup],
                "confirmed": len(lineup) >= 8,
            })
    return out


def roster(team_id: int) -> list[int]:
    js = requests.get(f"{STATSAPI}/teams/{team_id}/roster?rosterType=active",
                      timeout=60).json()
    return [p["person"]["id"] for p in js.get("roster", [])
            if p.get("position", {}).get("code") != "1"]


def people(ids: list[int]) -> dict[int, dict]:
    out = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 60):
        chunk = ids[i:i + 60]
        js = requests.get(f"{STATSAPI}/people?personIds={','.join(map(str, chunk))}",
                          timeout=60).json()
        for p in js.get("people", []):
            out[p["id"]] = {"name": p.get("fullName"),
                            "bats": (p.get("batSide") or {}).get("code", "?"),
                            "throws": (p.get("pitchHand") or {}).get("code", "?")}
    return out


# ── main ─────────────────────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--season-start", default=None,
                    help="defaults to March 1 of the target year")
    ap.add_argument("--agg", default="agg")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--snapshots", default="snapshots")
    args = ap.parse_args()

    day = args.date
    start = args.season_start or f"{day[:4]}-03-01"
    yesterday = (datetime.strptime(day, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()

    print(f"Updating aggregates {start} .. {yesterday}")
    update_aggregates(args.agg, start, yesterday, raw_dir=args.raw)
    cum = C.cum_from_agg(load_aggregates(args.agg))

    games = slate(day)
    if not games:
        print(f"No probable-pitcher matchups posted for {day} — nothing to snapshot.")
        return

    rows = []
    for g in games:
        batters = g["lineup"] if g["confirmed"] else roster(g["team_id"])
        for b in batters:
            rows.append({"game_date": pd.Timestamp(day), "batter": b,
                         "starter": g["starter"], "starter_name": g["starter_name"],
                         "team": g["team"], "opp": g["opp"],
                         "confirmed": g["confirmed"]})
    mu = pd.DataFrame(rows).drop_duplicates(["batter", "starter"])

    bio = people(mu["batter"].tolist() + mu["starter"].tolist())
    mu["player"] = mu["batter"].map(lambda i: bio.get(i, {}).get("name"))
    mu["bats"] = mu["batter"].map(lambda i: bio.get(i, {}).get("bats", "?"))
    mu["sp_hand"] = mu["starter"].map(lambda i: bio.get(i, {}).get("throws", "?"))
    # Switch hitters bat opposite the starter's hand.
    mu["stand"] = np.where(mu["bats"] == "S",
                           np.where(mu["sp_hand"] == "R", "L", "R"), mu["bats"])

    # pa/hr are placeholders here; join_outcomes.py fills them tomorrow.
    mu["pa"] = np.nan
    mu["hr"] = np.nan
    mu["bbe"] = np.nan

    scored = C.score_zone_fit(mu, cum["bat_zone"], cum["bat_base"],
                              cum["pit_zone"], K_VALUES)
    scored = C.attach_control(scored, cum["bat_rate"])

    os.makedirs(args.snapshots, exist_ok=True)
    out = os.path.join(args.snapshots, f"{day}.csv")
    scored.to_csv(out, index=False)

    n_ok = int(scored["zf_index_k50"].notna().sum())
    print(f"\nWrote {out}")
    print(f"  matchups   {len(scored)}")
    print(f"  scored     {n_ok}  ({n_ok / len(scored) * 100:.0f}%)")
    print(f"  confirmed  {int(scored['confirmed'].sum())} lineup rows")


if __name__ == "__main__":
    main()
