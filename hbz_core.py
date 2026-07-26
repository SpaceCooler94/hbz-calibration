"""
hbz_core.py — shared math for the HHBarrelZone calibration harness.

Both the backfill and the daily collector import from here. One code path
for the grids and the Zone Fit score means a calibrated number and a live
number are produced by the same function, not by two that drifted apart.

THE ONE RULE THIS FILE EXISTS TO ENFORCE
----------------------------------------
Every grid used to score a game on date D is built from pitches with
game_date STRICTLY BEFORE D. That is done with merge_asof(..., 
allow_exact_matches=False) against a cumulative table, so the exclusion is
structural rather than something a future edit can quietly undo. Score
May 3rd with a grid containing May 3rd's barrels and Zone Fit will look
excellent and be worthless.

DEFINITIONS (stated once, referenced everywhere)
------------------------------------------------
  in-zone      Savant zones 1-9. Zones 11-14 are the shadow/chase ring.
  barrel       launch_speed_angle == 6
  b_z          batter's SHRUNK barrel rate per BBE in zone z, in-zone only
  p0           batter's overall in-zone barrel rate per BBE
  f_z          pitcher's share of in-zone pitches thrown to zone z,
               conditioned on batter stance, normalised so sum_z f_z = 1
  ZoneFit      sum_z (b_z * f_z)          -- absolute, per BBE
  index        ZoneFit / p0 * 100         -- 100 = neutral location mix

Shrinkage is Beta-Binomial with a fixed pseudo-count k:
      b_z = (brl_z + k * p0) / (bbe_z + k)
k is the single tunable knob and it is what calibrate.py sweeps.
"""

from __future__ import annotations

import io
import os
import time
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import requests

# ── constants ────────────────────────────────────────────────────────
IN_ZONE = list(range(1, 10))
BARREL_LSA = 6
SEARCH_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
UA = "Mozilla/5.0 (compatible; HHBarrelZone-calibration/1.0)"

# Columns kept from the raw pitch feed. Everything else is dropped at
# parse time — a season of all 90-odd Savant columns is a needless 2 GB.
KEEP = [
    "game_date", "game_pk", "at_bat_number", "pitch_number",
    "batter", "pitcher", "stand", "p_throws", "zone",
    "launch_speed", "launch_angle", "launch_speed_angle",
    "hc_x", "hc_y", "events", "description", "inning_topbot",
]

DTYPES = {
    "batter": "int32", "pitcher": "int32", "game_pk": "int32",
    "at_bat_number": "int16", "pitch_number": "int16",
    "stand": "category", "p_throws": "category",
}


# ── fetch ────────────────────────────────────────────────────────────
def _day_url(day: str) -> str:
    """Statcast Search, one calendar day, regular season, all pitches.

    Day-sized chunks on purpose: Savant truncates a query at 25,000 rows
    and a full 15-game day is roughly 4,500 pitches, so a day can never
    silently clip. Week-sized chunks can, and a clipped chunk looks
    exactly like a quiet day.
    """
    params = [
        "all=true", "type=details", "player_type=pitcher",
        "hfGT=R%7C",
        f"game_date_gt={day}", f"game_date_lt={day}",
        "min_pitches=0", "min_results=0", "min_pas=0",
        "group_by=name", "sort_col=pitches", "sort_order=desc",
    ]
    return f"{SEARCH_URL}?{'&'.join(params)}"


def fetch_day(day: str, cache_dir: str = "data/raw", sleep: float = 1.0,
              retries: int = 3) -> pd.DataFrame:
    """One day of pitch-level data, cached to parquet.

    Cache is keyed by date and never expires: a completed game day does
    not change. That makes a re-run of the backfill free after the first
    pass, which matters because the first pass is ~180 requests.
    """
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{day}.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)

    last = None
    for attempt in range(retries):
        try:
            r = requests.get(_day_url(day), headers={"User-Agent": UA}, timeout=120)
            r.raise_for_status()
            df = pd.read_csv(io.StringIO(r.text), low_memory=False)
            break
        except Exception as e:                                   # noqa: BLE001
            last = e
            time.sleep(2 ** attempt * 2)
    else:
        raise RuntimeError(f"{day}: fetch failed after {retries} tries: {last}")

    if len(df) >= 24_900:
        raise RuntimeError(
            f"{day} returned {len(df)} rows — at or near Savant's 25k cap. "
            "The day was probably truncated; split the request before trusting it."
        )

    cols = [c for c in KEEP if c in df.columns]
    missing = set(KEEP) - set(cols)
    if {"zone", "batter", "pitcher", "stand"} & missing:
        raise RuntimeError(f"{day}: required columns missing from feed: {missing}")

    df = df[cols].copy()
    for c, t in DTYPES.items():
        if c in df.columns:
            df[c] = df[c].astype(t, errors="ignore")
    df["game_date"] = pd.to_datetime(df["game_date"])
    df.to_parquet(path, index=False)
    time.sleep(sleep)
    return df


def season_dates(start: str, end: str) -> list[str]:
    d0 = datetime.strptime(start, "%Y-%m-%d").date()
    d1 = datetime.strptime(end, "%Y-%m-%d").date()
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


def load_range(start: str, end: str, cache_dir: str = "data/raw",
               verbose: bool = True) -> pd.DataFrame:
    frames = []
    for day in season_dates(start, end):
        try:
            df = fetch_day(day, cache_dir=cache_dir)
        except Exception as e:                                   # noqa: BLE001
            if verbose:
                print(f"  {day}  SKIP  {e}")
            continue
        if len(df):
            frames.append(df)
        if verbose:
            print(f"  {day}  {len(df):>5} pitches")
    if not frames:
        raise RuntimeError("No data loaded in range.")
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["game_date", "game_pk", "at_bat_number", "pitch_number"])


# ── derived flags ────────────────────────────────────────────────────
def annotate(pitches: pd.DataFrame) -> pd.DataFrame:
    """Add the per-pitch booleans everything downstream counts on."""
    p = pitches.copy()
    p["game_date"] = pd.to_datetime(p["game_date"])
    p["zone"] = pd.to_numeric(p["zone"], errors="coerce").astype("float64")
    p["in_zone"] = p["zone"].isin(IN_ZONE)
    p["is_bbe"] = pd.to_numeric(p["launch_angle"], errors="coerce").notna()
    p["is_brl"] = pd.to_numeric(p["launch_speed_angle"], errors="coerce") == BARREL_LSA
    p["is_pa_end"] = p["events"].notna() & (p["events"].astype(str) != "")
    p["is_hr"] = p["events"].astype(str) == "home_run"
    return p


def starters(pitches: pd.DataFrame) -> pd.DataFrame:
    """The starting pitcher for each side of each game.

    Defined as the pitcher who threw the game's first pitch for that
    half-inning side. Derived from the data rather than from a probables
    feed so the backfill never depends on what was *projected* — it uses
    who actually started.
    """
    p = pitches.sort_values(["game_pk", "at_bat_number", "pitch_number"])
    first = (p.groupby(["game_pk", "inning_topbot"], observed=True)
               .head(1)[["game_pk", "inning_topbot", "pitcher", "game_date"]])
    return first.rename(columns={"pitcher": "starter"})


# ── cumulative, leakage-safe grids ───────────────────────────────────
def batter_zone_cum(p: pd.DataFrame) -> pd.DataFrame:
    """Cumulative in-zone BBE and barrels per (batter, zone), by date.

    One row per date on which that batter/zone actually saw contact. The
    as-of merge fills the gaps, so no dense date grid is materialised.
    """
    bbe = p[p["is_bbe"] & p["in_zone"]]
    d = (bbe.groupby(["batter", "zone", "game_date"], observed=True)
            .agg(n=("is_bbe", "sum"), b=("is_brl", "sum"))
            .reset_index()
            .sort_values("game_date"))
    d[["n_cum", "b_cum"]] = d.groupby(["batter", "zone"], observed=True)[["n", "b"]].cumsum()
    d["zone"] = d["zone"].astype("float64")
    return d[["batter", "zone", "game_date", "n_cum", "b_cum"]]


def batter_base_cum(p: pd.DataFrame) -> pd.DataFrame:
    """Cumulative in-zone BBE and barrels per batter — the p0 denominator."""
    bbe = p[p["is_bbe"] & p["in_zone"]]
    d = (bbe.groupby(["batter", "game_date"], observed=True)
            .agg(n=("is_bbe", "sum"), b=("is_brl", "sum"))
            .reset_index()
            .sort_values("game_date"))
    d[["n0_cum", "b0_cum"]] = d.groupby("batter", observed=True)[["n", "b"]].cumsum()
    return d[["batter", "game_date", "n0_cum", "b0_cum"]]


def pitcher_zone_cum(p: pd.DataFrame) -> pd.DataFrame:
    """Cumulative in-zone pitch counts per (pitcher, batter stance, zone)."""
    iz = p[p["in_zone"]]
    iz = iz.assign(stand=iz["stand"].astype(str))
    d = (iz.groupby(["pitcher", "stand", "zone", "game_date"], observed=True)
           .size().rename("n").reset_index()
           .sort_values("game_date"))
    d["p_cum"] = d.groupby(["pitcher", "stand", "zone"], observed=True)["n"].cumsum()
    d["zone"] = d["zone"].astype("float64")
    return d[["pitcher", "stand", "zone", "game_date", "p_cum"]]


def _asof(left: pd.DataFrame, right: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """As-of join on game_date, strictly before. This is the leakage guard.

    Normalises the join keys on both sides first. The backfill path carries
    ids as int32 (from the parquet cache's dtype cast) while the daily path's
    matchups arrive as int64 from StatsAPI; merge_asof refuses to join int32
    against int64, so every by-key is coerced to one type before the merge.
    """
    l = left.sort_values("game_date").copy()
    r = right.sort_values("game_date").copy()
    for k in by:
        for d in (l, r):
            if k not in d.columns:
                continue
            if pd.api.types.is_integer_dtype(d[k]):
                d[k] = d[k].astype("int64")
            elif isinstance(d[k].dtype, pd.CategoricalDtype) or d[k].dtype == object:
                d[k] = d[k].astype(str)
    return pd.merge_asof(
        l, r, on="game_date", by=by,
        direction="backward", allow_exact_matches=False,
    )


# ── matchups and outcomes ────────────────────────────────────────────
def matchups(p: pd.DataFrame) -> pd.DataFrame:
    """One row per (date, batter, starting pitcher faced) with outcomes.

    Restricted to PAs against the starter, because that is the matchup
    the board screens. PAs against relievers are real but they are not
    what Zone Fit claimed to predict, and folding them in would grade the
    metric on a question it never asked.
    """
    st = starters(p)
    pa = p[p["is_pa_end"]].merge(
        st[["game_pk", "inning_topbot", "starter"]],
        on=["game_pk", "inning_topbot"], how="left")
    pa = pa[pa["pitcher"] == pa["starter"]]

    g = (pa.groupby(["game_date", "batter", "starter"], observed=True)
           .agg(pa=("is_pa_end", "sum"),
                hr=("is_hr", "sum"),
                bbe=("is_bbe", "sum"),
                stand=("stand", lambda s: s.mode().iat[0] if len(s.mode()) else np.nan))
           .reset_index())
    g["stand"] = g["stand"].astype(str)
    return g


# ── Zone Fit ─────────────────────────────────────────────────────────
def score_zone_fit(mu: pd.DataFrame, bz: pd.DataFrame, bb: pd.DataFrame,
                   pz: pd.DataFrame, k_values: list[int]) -> pd.DataFrame:
    """Attach Zone Fit to each matchup, for every k in k_values.

    Returns mu plus: p0, bat_n (in-zone BBE prior to the game), pit_n
    (in-zone pitches vs that stance prior to the game), and one
    zf_index_k{K} / zf_abs_k{K} column pair per k.

    Everything joined here is as-of-strictly-before the game date, so a
    row's inputs could all have been known the morning of the game.
    """
    mu = mu.copy().reset_index(drop=True)
    mu["game_date"] = pd.to_datetime(mu["game_date"])
    mu["stand"] = mu["stand"].astype(str)

    # batter baseline (p0) as of the date
    mu = _asof(mu, bb, by=["batter"])
    mu["n0_cum"] = mu["n0_cum"].fillna(0)
    mu["b0_cum"] = mu["b0_cum"].fillna(0)
    mu["p0"] = np.where(mu["n0_cum"] > 0, mu["b0_cum"] / mu["n0_cum"], np.nan)
    mu = mu.rename(columns={"n0_cum": "bat_n"})

    # explode to the nine strike-zone cells
    cells = mu.loc[:, ["game_date", "batter", "starter", "stand"]].copy()
    cells["_row"] = np.arange(len(cells))
    cells = cells.loc[cells.index.repeat(9)].copy()
    cells["zone"] = np.tile(IN_ZONE, len(mu)).astype(float)

    cells = _asof(cells, bz, by=["batter", "zone"])
    cells[["n_cum", "b_cum"]] = cells[["n_cum", "b_cum"]].fillna(0)

    cells = _asof(cells, pz.rename(columns={"pitcher": "starter"}),
                  by=["starter", "stand", "zone"])
    cells["p_cum"] = cells["p_cum"].fillna(0)

    # pitcher location share, normalised over the strike zone
    tot = cells.groupby("_row", observed=True)["p_cum"].transform("sum")
    cells["f"] = np.where(tot > 0, cells["p_cum"] / tot, np.nan)

    p0_by_row = mu["p0"].to_numpy()
    cells["p0"] = p0_by_row[cells["_row"].to_numpy()]

    out = mu.copy()
    out["pit_n"] = (cells.groupby("_row", observed=True)["p_cum"].sum()
                    .reindex(np.arange(len(mu)), fill_value=0).to_numpy())

    for k in k_values:
        b_z = (cells["b_cum"] + k * cells["p0"]) / (cells["n_cum"] + k)
        contrib = (b_z * cells["f"]).groupby(cells["_row"], observed=True).sum(min_count=1)
        absv = contrib.reindex(np.arange(len(mu))).to_numpy()
        out[f"zf_abs_k{k}"] = absv
        out[f"zf_index_k{k}"] = np.where(out["p0"] > 0, absv / out["p0"] * 100, np.nan)

    # season-to-date barrel rate per BBE (all BBE, not just in-zone) —
    # the control variable calibration conditions on, so Zone Fit has to
    # beat "this hitter barrels a lot" rather than restate it.
    return out


def batter_rate_cum(p: pd.DataFrame) -> pd.DataFrame:
    """Cumulative all-BBE totals per batter: the leakage-safe control."""
    bbe = p[p["is_bbe"]]
    d = (bbe.groupby(["batter", "game_date"], observed=True)
           .agg(n=("is_bbe", "sum"), b=("is_brl", "sum"),
                hh=("launch_speed", lambda s: (pd.to_numeric(s, errors="coerce") >= 95).sum()))
           .reset_index()
           .sort_values("game_date"))
    d[["bbe_cum", "brl_cum", "hh_cum"]] = (
        d.groupby("batter", observed=True)[["n", "b", "hh"]].cumsum())
    return d[["batter", "game_date", "bbe_cum", "brl_cum", "hh_cum"]]


def attach_control(mu: pd.DataFrame, rc: pd.DataFrame) -> pd.DataFrame:
    """Season-to-date barrel% and hard-hit% as of the game date."""
    out = _asof(mu.sort_values("game_date"), rc, by=["batter"])
    out[["bbe_cum", "brl_cum", "hh_cum"]] = out[["bbe_cum", "brl_cum", "hh_cum"]].fillna(0)
    out["brl_pct"] = np.where(out["bbe_cum"] > 0, out["brl_cum"] / out["bbe_cum"] * 100, np.nan)
    out["hh_pct"] = np.where(out["bbe_cum"] > 0, out["hh_cum"] / out["bbe_cum"] * 100, np.nan)
    return out


def build_scored(p: pd.DataFrame, k_values: list[int]) -> pd.DataFrame:
    """Full pipeline: annotated pitches -> scored, outcome-bearing matchups."""
    mu = matchups(p)
    scored = score_zone_fit(mu, batter_zone_cum(p), batter_base_cum(p),
                            pitcher_zone_cum(p), k_values)
    return attach_control(scored, batter_rate_cum(p))


# ── compact daily aggregates (for the forward collector) ─────────────
# The backfill can afford to hold a season of pitches in memory. The
# daily job cannot re-download 700k rows every morning, and committing
# them to a repo is absurd. So the collector persists these four small
# frames per day — a few kilobytes each — and rebuilds the grids from
# them. Same cumsum + as-of logic, so the numbers are identical.

def aggregate_day(p: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Collapse one day of annotated pitches into the four count tables."""
    bbe = p[p["is_bbe"]]
    bbe_iz = bbe[bbe["in_zone"]]
    iz = p[p["in_zone"]].assign(stand=lambda d: d["stand"].astype(str))
    ev = pd.to_numeric(bbe["launch_speed"], errors="coerce")
    return {
        "bat_zone": (bbe_iz.groupby(["batter", "zone", "game_date"], observed=True)
                     .agg(n=("is_bbe", "sum"), b=("is_brl", "sum")).reset_index()),
        "bat_base": (bbe_iz.groupby(["batter", "game_date"], observed=True)
                     .agg(n=("is_bbe", "sum"), b=("is_brl", "sum")).reset_index()),
        "pit_zone": (iz.groupby(["pitcher", "stand", "zone", "game_date"], observed=True)
                     .size().rename("n").reset_index()),
        "bat_rate": (bbe.assign(_hh=(ev >= 95))
                     .groupby(["batter", "game_date"], observed=True)
                     .agg(n=("is_bbe", "sum"), b=("is_brl", "sum"),
                          hh=("_hh", "sum")).reset_index()),
    }


def cum_from_agg(a: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Cumulative grids from stacked daily aggregates."""
    bz = a["bat_zone"].sort_values("game_date").copy()
    bz[["n_cum", "b_cum"]] = bz.groupby(["batter", "zone"], observed=True)[["n", "b"]].cumsum()
    bz["zone"] = bz["zone"].astype("float64")

    bb = a["bat_base"].sort_values("game_date").copy()
    bb[["n0_cum", "b0_cum"]] = bb.groupby("batter", observed=True)[["n", "b"]].cumsum()

    pz = a["pit_zone"].sort_values("game_date").copy()
    pz["p_cum"] = pz.groupby(["pitcher", "stand", "zone"], observed=True)["n"].cumsum()
    pz["zone"] = pz["zone"].astype("float64")

    rc = a["bat_rate"].sort_values("game_date").copy()
    rc[["bbe_cum", "brl_cum", "hh_cum"]] = (
        rc.groupby("batter", observed=True)[["n", "b", "hh"]].cumsum())

    return {
        "bat_zone": bz[["batter", "zone", "game_date", "n_cum", "b_cum"]],
        "bat_base": bb[["batter", "game_date", "n0_cum", "b0_cum"]],
        "pit_zone": pz[["pitcher", "stand", "zone", "game_date", "p_cum"]],
        "bat_rate": rc[["batter", "game_date", "bbe_cum", "brl_cum", "hh_cum"]],
    }
