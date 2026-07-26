# hbz-calibration

Grades HHBarrelZone's Zone Fit index and gate thresholds against actual
home-run outcomes. Two halves, one shared math module.

| file | role |
|---|---|
| `hbz_core.py` | fetch, cache, leakage-safe as-of grids, Zone Fit scoring, PA/HR extraction |
| `test_leakage.py` | asserts same-day contact never reaches a grid, and that the shrinkage math matches a hand calculation |
| `backfill.py` | reconstructs the season and scores every starter matchup as of its own date |
| `calibrate.py` | within-barrel-decile lift, k sweep, permutation floor, gate sweep → `calibration.json` + `report.md` |
| `collect_daily.py` | updates compact aggregates, snapshots today's slate before first pitch |
| `join_outcomes.py` | grades past snapshots into `ledger.csv` |

## Run order

Everything runs in GitHub Actions. Trigger from the GitHub mobile app;
nothing here belongs on the phone.

First-time standup is a phone-only procedure — see **REPO_SETUP.md**.
GitHub holds code + state; Render runs the schedule (`render.yaml`), two
cron jobs that clone, compute, and commit results back:

1. **`hbz-calibrate`** — manual first run (full-season backfill + grade),
   then weekly. Writes `calibration.json` + `report.md` to the repo root.
2. **`hbz-daily`** — snapshots today's slate before first pitch and grades
   yesterday's into `ledger.csv`. The only evidence with no possible
   hindsight in it.

Render cron jobs are diskless, so state is versioned in git rather than on
Render — which is also what keeps it auditable. `render_run.sh` is the
runner both jobs share.

Locally, same order:

```bash
pip install -r requirements.txt
python3 test_leakage.py
python3 backfill.py --start 2026-03-26 --end 2026-07-24
python3 calibrate.py
```

## What the test actually asks

Not "does Zone Fit correlate with home runs" — good hitters have both, so
that passes even for a metric that is only a repackaged barrel rate. The
statistic reported is **the HR/PA gap between the top and bottom Zone Fit
bin, measured inside a barrel-rate stratum**, PA-weighted, on a
chronological holdout, against a seeded permutation null.

If the measured lift sits inside the null band, Zone Fit adds nothing
that barrel rate did not already say. `report.md` states that in those
words when it happens. That is a real possible outcome and the harness is
built to report it rather than bury it.

The `k` sweep answers the shrinkage question empirically. `k = 50` in the
board is an assumption, not a measurement.

## Leakage

Every grid is built with `merge_asof(..., allow_exact_matches=False)`
against cumulative counts, so a game on date D is scored only from
pitches before D. `test_leakage.py` plants a hitter who barrels
everything on the test day and asserts his index is identical to a hitter
who barrels nothing. The backfill workflow runs it before it grades
anything.

## Known limits

- **HR/PA is ~4-5%.** Half a season of starter matchups is a few thousand
  home runs — enough to detect a moderate effect, not a small one. A null
  result means "not detectable at this sample", not "definitely zero".
- **Starters only.** Reliever PAs are excluded; Zone Fit never claimed to
  price them.
- **No park or weather term.** Both matter for HR and neither is in here,
  so some of what the lift measures may be schedule.
- **Batter grids pool across pitcher hand.** The cells are already thin;
  splitting them would make the prior do nearly all the work. The pitcher
  grid *is* conditioned on stance.
- **Gate curves are descriptive.** They show what each threshold buys in
  HR/PA and what it costs in slate, not an optimum — the right gate
  depends on how many candidates you want to price.

## Feeding it back to the board

`calibration.json` carries `zone_fit.k_star`, `zone_fit.index_percentiles`,
and the gate curves. Point HHBarrelZone's `ZONEFIT_PRIOR_STRENGTH` at
`k_star` and replace the hand-picked 95/105/115 colour bands with the
observed percentiles. Do not wire it in before reading `report.md` — if
`beats_noise` is false, the correct action is to stop showing the index
as a signal, not to recolour it.
