# Changelog

## 2026-08-29 (3)

- Added a multiband Lomb-Scargle section to `notebooks/04_periods.ipynb`
  (`astropy.timeseries.LombScargleMultiband`, pooling all bands' epochs into one shared-period
  fit instead of picking a single "best" band per object), addressing the "Next" item nb_04
  originally left open.
  - Coverage jumped from ~34% (best single band) to 99.8% (7020/7036) — expected, since
    multiband only needs 10+ points combined across bands rather than in any one band, and
    every object here already has 10+ total by construction (`nDiaSources > 10`).
  - Much more expensive: ~35 ms/object vs. single-band's ~0.6 ms/object (~59x), projecting to a
    naive ~2265-hour ceiling for the full 232M-row collection, vs. single-band's ~36 hours.
  - Compared multiband periods against single-band `best_period_days` for the ~2400 objects with
    both: broad agreement in a band around the 1:1 line from ~0.3-100 days, but a distinct group
    of single-band periods under 0.1 day disagree sharply, landing multiband periods in the 1-4
    day range instead — plausibly the single-band sub-0.1-day periods being spurious (few points,
    no independent band to cross-check), though not independently vetted here.
  - `multiband_period_power` stayed within `[0, 1]` as expected for `standard` normalization,
    unlike single-band's occasional `>1` power (nb_04's original `power=7.93` noise example).
  - Extended the same registered `dia_object_lc_10plus_with_periods` artifact in place rather
    than creating a new one.

## 2026-08-29 (2)

- Added `notebooks/04_periods.ipynb` (nb_04 from the rough plan): per-band Lomb-Scargle
  periods via `astropy.timeseries.LombScargle`, `map_rows(..., append_columns=True)` on
  `diaSource.midpointMjdTai`/`scienceMag`, same style as nb_02/nb_03. Longest findable period
  bounded by nb_02's `duration_days / 2`; shortest left to `autopower`'s own defaults. Works on
  nb_03's `dia_object_lc_10plus_with_mags`, output registered as
  `dia_object_lc_10plus_with_periods`.
  - Real-data finding: per-band point counts are much thinner than `nDiaSources` (the total
    across all 6 bands) suggests — medians of `z`: 7, `i`: 3, `r`: 3, `g`: 2, `u`/`y`: 0 — so
    with `MIN_POINTS_FOR_LS = 10`, only ~34% of objects get a period in any band, and `z`
    dominates (not `r`, which nb_01 used as the depth/cadence proxy for picking these fields).
  - Measured execution time per the spec's explicit ask: ~0.6 ms/object on this subset,
    projecting to a naive ~38 hours (serial, single-machine) for `dia_object_collection`'s full
    232,004,216 rows — flagged as an overestimate ceiling, not a real estimate, since most
    full-collection objects have far fewer `diaSource` points than this `nDiaSources > 10`
    subset and would fail the point threshold almost instantly.
  - Folded the single highest-power object in the subset (`power=7.93`, `standard`
    normalization can exceed 1) as a sanity check: ~0.05 mag of scatter, no visible periodic
    shape — concrete evidence that peak power alone isn't a usable real/bogus signal here,
    logged as an open question (needs a real false-alarm-probability pass).

## 2026-08-29

- Revised `notebooks/03_color_mag_diagram.ipynb`'s plots and added quality cuts, per feedback
  that the original combined 2-panel plot was too crowded and that no quality cuts had been
  applied at all yet:
  - Split the single 2-panel plot into two: 4 panels (one per field) colored by nb_02's r-band
    amplitude, and 3 panels (one per amplitude bin: `<0.2`, `0.2-0.4`, `>=0.4`) colored by
    field. Switched the continuous colormap from `viridis` to `plasma` — under the alpha
    blending needed for ~7000 points, viridis's yellow end washed out and stopped reading as
    "high value".
  - Added two photometric quality cuts to section 1's per-band median: require at least 3
    unflagged forced-photometry points per band (was: any `>0`), and exclude
    `diaObjectForcedSource` rows flagged bad/saturated/cosmic-ray/edge/interpolated/no-data or
    with a failed/invalid PSF flux fit. Removes the implausible `g-r` outliers (beyond ±2) and
    faint stragglers (`r > 24`) the unfiltered median let through.
  - Investigated the requested point-source/extended split (`diaSource.extendedness`):
    confirmed it isn't reachable through this LSDB HATS collection at all — not in `diaObject`'s
    flat columns, nor in the nested `diaSource`/`diaObjectForcedSource` schemas — even though
    DP2's `diaSource` schema does define it, so it looks like it was dropped when this
    particular HATS catalog was built. Proper quality filtering (extendedness among it) needs a
    different data path (direct Butler/PPDB access, or a HATS catalog rebuilt with more columns
    retained) than what these notebooks use.
  - Used `diaSource.reliability` (DP2's per-detection real/bogus ML score) as a substitute
    split instead, but found it's heavily skewed toward zero for this subset (99th percentile
    across ~134k detections is only ~0.09; only ~1.2% of objects ever reach `>0.5` even at
    their best epoch) — not usable as an absolute "> 0.9 = real" cut. Used a relative top-10%
    vs. bottom-90% split by `max_reliability` per object instead, with the calibration caveat
    noted directly in the notebook.
  - Added a color-color diagram (`g-r` vs `r-i` by default, bands swappable) alongside the CMD,
    plus a per-field 4-panel version of it underneath (same layout as the per-field CMD).

## 2026-08-28

- Renamed the `feature/nb02-lc-histograms` branch (which already contained nb_01's history plus
  the nb_02 commit, linearly) to `nb-v01` — this is now the working branch for the rest of the
  notebook series, kept separate from `main` until the whole set is ready to merge.
- Added `notebooks/03_color_mag_diagram.ipynb` (nb_03 from the rough plan): color-magnitude
  diagram, `g-r` vs `r` by default (bands are plain variables, meant to be changed). Works on
  nb_02's `dia_object_lc_10plus_with_stats`.
  - Resolves the spec's magnitude question: `diaObject`'s own per-band columns are either
    difference-image statistics (`{band}_psfFluxMean`, useless as a brightness) or too sparse
    to rely on (`{band}_scienceFluxMean`, populated for only ~20% of objects in our subset).
    Going through the `Object` (coadd) table would need a spatial crossmatch, ruled out as
    slow and ambiguous in crowded fields. Used `ForcedSourceOnDiaObject` instead — reachable
    through LSDB as the nested `diaObjectForcedSource` column already present in the subset,
    covering ~99.7% of objects — median `psfMag` per band via the same `map_rows` pattern as
    nb_02, this time with `append_columns=True` merging results straight onto the lazy catalog.
  - Found and worked around an environment bug: writing a HATS collection directly from a
    `map_rows(..., append_columns=True)` result (`with_mags_cat.write_catalog(...)`) produces
    an auto-generated margin cache whose spatial index is misnamed (`__index_level_0__` instead
    of `_healpix_29`), which then fails on reopen with a schema-mismatch `ValueError`. Routing
    through `.compute()` + `lsdb.from_dataframe()` first (nb_01/nb_02's pattern) avoids it, so
    `append_columns=True` ends up only removing the manual column-assign step, not the
    materialize step.
  - Found a genuine data-coverage gap, not a bug: `field_4` (14 objects) has zero g-band
    `diaObjectForcedSource` rows at all — only `r`/`i` were observed there — so it drops out of
    the `g-r` CMD via the `dropna`. Logged as an open question for picking fields by eye without
    checking per-band coverage first.
  - Output registered as `dia_object_lc_10plus_with_mags` (inputs: `dia_object_lc_10plus_with_stats`).

## 2026-08-27

- Added `pyproject.toml`, exact-pinned from the `dp2_analysis` conda environment (Python 3.14.7), so the environment can be reproduced elsewhere via `pip install .`. The `datapaths` package is pulled from its repo (`git+https://github.com/ShrRa/datapaths.git@main`) rather than PyPI.
- Added `configs/roots.local.yaml` (gitignored) mapping `datapaths` roots to their locations on the RSP session used for development: `dp2_raw` (`/rubin/lsdb_data/dp2`), `dp2_filtered` (the pre-filtered `nDiaSources > 10` copy at `/deleted-sundays/shrra-ung/dp2`), `dp2_subset` (`~/share/trieste`), `misc` (`~/DATA/DP2`).
- Rewrote `notebooks/01_read_diaObj.ipynb` (nb_01 from the rough plan): surveys all 8393 `diaObject` partitions cheaply via parquet `_metadata` footer stats (row counts + `max(nDiaSources)`, no data read), selects 4 partitions spanning low/high galactic latitude and low/high cadence, filters to `nDiaSources > 10`, writes the ~700 MB / ~5000-object subset to `dp2_subset`, and registers it in `configs/artifacts_registry.yaml` as `dia_object_lc_10plus`. Also demonstrates the pandas/numpy conversion and the `explode`-based long-format light-curve table called for in the spec.
  - Notable finding folded into the notebook: picking partitions by raw object count is a poor proxy for cadence — 110/8393 partitions have `max(nDiaSources) <= 10` and yield zero objects after filtering; selection now uses `max(nDiaSources)` per partition (also free from the `_metadata` footer) instead.
- Added `README.md` and cleaned up `.env.example` (previously copy-pasted from the `datapaths` docs' own example, pointing at an unrelated machine/repo).
- Revised `notebooks/01_read_diaObj.ipynb`'s selection approach: replaced the metadata-driven partition scan with `catalog.plot_pixels()` for a full-footprint coverage map, plus a Butler-free r-band visit-count depth/cadence map built from `/rubin/lsdb_data/dp2/public-files/visit_detector.parquet` (the `lsst.daf.butler`-based survey property maps from the RSP `203_Maps` tutorial aren't usable from this kernel). Fields are now picked by eye as plain `(ra, dec)` coordinates and pulled out with `cone_search` per field, combined via `pd.concat` + `lsdb.from_dataframe`, instead of a systematic 2x2 partition search — closing with a `plot_pixels()` on the written subset so the workflow is see-map → pick-coordinates → get-subset → verify-on-map. Subset is now 5 fields / 7,036 objects / 83 MB.
  - Found and worked around two environment bugs: `hats.inspection.visualize_catalog.plot_healpix_map(..., depth=<scalar int>)` triggers a Rust panic in this environment's `cdshealpix` build (needs an array matching `ipix`'s length instead), and `SkyCoord(ra=pandas_series * u.deg, ...)` silently drops the unit (pandas doesn't propagate astropy units the way numpy arrays do — convert with `.to_numpy()` first).
  - Correction: DP2 uses LSSTCam, not ComCam (that's DP1) — confirmed via `physical_filter` naming in `visit_detector.parquet` (e.g. `r_57`).
  - Correction: `lsst.daf.butler` *is* available on RSP, just not from the bare `python3` kernel — the notebooks' actual declared kernel (`"lsst"`, `setup lsst_distrib` via EUPS) has it alongside `lsdb`/`datapaths`. Doesn't change anything already built (same underlying conda env, just a superset), but the Butler-based survey property maps from the `203_Maps` tutorial are reachable after all if revisited later.
- Added `notebooks/02_lc_histograms.ipynb` (nb_02 from the rough plan): `nDiaSources` histograms (combined + per field), and per-object light-curve statistics (duration, cadence gap — combined bands; robust P90-P10 amplitude — per band, never mixing bands) computed via `lsdb.Catalog.map_rows` on the nested `diaSource` column. Resolves the spec's "diff flux isn't informative" concern directly: `diaSource.scienceMag` is an absolute, calibrated per-epoch magnitude (confirmed empirically, stable across epochs), distinct from the noisier diff-image `psfMag`.
  - New stat columns are merged onto the already-nested subset frame and written as a new HATS collection (`dia_object_lc_10plus_with_stats`, registered via `dp.register`) rather than flattened into a separate `dp.save()` table — a collection with nested columns shouldn't go through `dp.save` (parquet-only, no nested support), only through `write_catalog` + `register`. Written under a new name rather than overwriting nb_01's `dia_object_lc_10plus` output, since nb_01 rewrites that path with `overwrite=True` whenever it's rerun.
