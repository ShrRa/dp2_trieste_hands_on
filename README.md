# DP2 Trieste hands-on

Notebooks for an LSST DP2 analysis of variable objects, prepared for the Trieste regional
workshop (August 2026). See `docs/SPEC_V01.md` for the full scope and rough plan.

## Setup

The notebooks are meant to run on the Rubin Science Platform (RSP), whose `lsst-scipipe`
kernel already provides `lsdb`/`hats`/`nested-pandas` etc. **If you're only running
`05_interactive_explorer.ipynb`** (the workshop's actual hands-on notebook — nb_01-04 build the
`dia_object_lc_hq` collection it reads, but you don't need to re-run them or install anything
extra to just read it), skip the rest of this section; nb_05 falls back to that collection's
known shared path on its own.

nb_01-04 (and re-registering artifacts of your own) need one extra package,
[`datapaths`](https://github.com/ShrRa/datapaths), which manages where each notebook's inputs
and outputs live without hardcoding machine-specific paths:

```bash
pip install --user "datapaths[tabular] @ git+https://github.com/ShrRa/datapaths.git@main"
```

`datapaths` resolves paths through two files under `configs/`:

- `artifacts_registry.yaml` — committed, tracks named artifacts (path, hash, notes).
- `roots.local.yaml` — machine-local, **not committed**, maps root names to absolute
  directories on the machine you're running on. Create your own before running any notebook,
  e.g. on RSP:

  ```yaml
  dp2_raw: /rubin/lsdb_data/dp2
  dp2_filtered: /deleted-sundays/<your-user>/dp2
  dp2_subset: /home/<your-user>/share/trieste
  misc: /home/<your-user>/DATA/DP2
  ```

If you're not on RSP, `pip install .` reproduces the full pinned environment (see
`pyproject.toml`) — note it's pinned to Python 3.14, which is newer than the 3.13.9 the RSP
kernel currently ships, so on RSP install `datapaths` directly as above instead.

## Notebooks

nb_02-05 all read and write **the same collection**, `dia_object_lc_hq` — nb_02, nb_03, and
nb_04 each add their own columns to it in place rather than spinning off a `..._with_X` copy,
so the ~17 GB of nested light curves in it exists on disk once, not four times over. Each
heavy step writes to a fresh temporary path first (`write_catalog(..., resume=True)` — a crash
partway only costs that temporary path's not-yet-written partitions) and only *promotes* it —
delete the old `dia_object_lc_hq`, rename the temporary one into place — once the write
actually finishes; a fast directory swap, not a recompute. `resume=True` can't be used directly
against `dia_object_lc_hq` itself once it already has content (it only checks whether a
pixel's file exists, not whether it has the columns this run would add), which is why every
heavy step goes through a temporary path rather than writing to `dia_object_lc_hq` directly.

nb_01-04 each have a `RUN_HEAVY_CALC` flag (default `False`) around their one expensive step.
Leave it `False` to read the notebook and the columns `dia_object_lc_hq` already has without
waiting on a recompute; set it `True` only if you're deliberately regenerating that step's
output — the *first* person to do so on a fresh `dp2_subset` root needs to run nb_01 through
nb_04 in order with the flag on once, since each adds columns the next one reads. `resume=True`
only knows which pixels already exist in that temporary path, not whether the mapped function
changed, so delete it first (or pass `overwrite=True` for that write instead) after editing one
of these functions, rather than relying on resume for a clean rebuild.

nb_02-05 each start by picking a small slice of the HQ sample (one partition or a cone search,
`select_slice` from `src/dataio/hq_sample.py`) to look at directly — the whole HQ sample is
~399k objects, too large to casually pull into memory or plot point-by-point.

- `notebooks/01_read_diaObj.ipynb` — visualizes the DP2 `diaObject` footprint (coverage map
  via `plot_pixels()`, plus a depth/cadence map built from r-band visit counts), lets you pick
  fields by eye as plain `(ra, dec)` coordinates, pulls each out with `cone_search`, filters to
  `nDiaSources > 10`, and writes/registers a small subset (`dia_object_lc_10plus`) for that
  cone-search demo. Also demonstrates converting a catalog to pandas/numpy and building a
  long-format light-curve table via `explode`. Section 5 additionally selects the full
  high-quality sample (`nDiaSources > 100` across the whole `diaObject` collection, no
  per-field cone search), written and registered as `dia_object_lc_hq` — the collection
  nb_02-05 all build on and add columns to, in place.
- `notebooks/02_lc_histograms.ipynb` — `nDiaSources` histogram (whole HQ sample, one panel),
  plus per-object light-curve statistics (duration, cadence gap, per-band robust amplitude)
  computed from the nested `diaSource` column via `lsdb.Catalog.map_partitions` (vectorized —
  `.explode()` to a long table, then `groupby` aggregations, not a per-object Python loop)
  across the whole HQ sample, merged onto `dia_object_lc_hq` as new columns.
- `notebooks/03_color_mag_diagram.ipynb` — color-magnitude and color-color diagrams (`g-r` vs
  `r`, and `g-r` vs `r-i`; bands are plain variables), plotted as `hexbin` density maps (HQ
  scale saturates per-point scatter). Per-band magnitudes come from `ForcedSourceOnDiaObject`
  (the nested `diaObjectForcedSource` column), aggregated per band via vectorized
  `map_partitions` with a quality cut (`MIN_FORCED_PER_BAND` unflagged points per band), since
  `diaObject`'s own columns are either difference-image-based or too sparsely populated to use
  directly, and a crossmatch to the `Object` (coadd) table was ruled out (slow, ambiguous in
  crowded fields). Also splits objects by `diaSource.reliability` (DP2's real/bogus score) as a
  stand-in for the point-source/extended split `diaObject.extendedness` would give — that
  column isn't reachable through this LSDB HATS collection.

- `notebooks/04_periods.ipynb` — per-band Lomb-Scargle periods (`astropy.timeseries.LombScargle`)
  via `map_partitions`, longest findable period bounded by nb_02's light-curve duration.
  Measures and reports execution time (per the spec's ask), and folds the highest-power light
  curve as a sanity check. Also runs `LombScargleMultiband` (pooling all bands per object) as a
  second pass: much higher coverage at ~59x the per-object cost (both share one
  `RUN_HEAVY_CALC` flag — budget for the multiband pass specifically at HQ scale, projected
  ~3.9 hours). Unlike nb_02/nb_03's functions, astropy's `LombScargle`/`LombScargleMultiband`
  have no batched multi-object API, so both passes still loop per object — that loop is the
  actual computation here, not a shortcut around one. Both passes also save the top-5 local
  maxima of each periodogram (`periodogram_peaks`/`multiband_periodogram_peaks`, new nested
  columns), not just the single best period — raw material for checking candidate periods
  against known daily/yearly aliases, without the cost of saving the whole periodogram grid.

- `notebooks/05_interactive_explorer.ipynb` — demos `interactive_scatter_lc`
  (`src/visualization/lc_explorer.py`): click a point in a scatter plot (a CMD, a
  period-amplitude diagram, anything keyed by an object id) to see that object's light curve on
  the right, with toggles to fold on a period and to show/hide flux errors. Built on
  `holoviews` + `bokeh` + `panel` — all three ship in the RSP `lsst-scipipe` kernel already, no
  extra install needed; needs a live Jupyter kernel to actually click (not verified outside
  JupyterLab on RSP). `lc_df` still has to be materialized up front, so this one uses a slice
  of the HQ sample as its actual working dataset, not just a look-and-discard sample. Doesn't
  need `datapaths` either — it only reads the already-built `dia_object_lc_hq`, falling back to
  its known shared path directly if `datapaths` isn't installed/configured. Also has a
  non-interactive fallback, `plot_lightcurve` (same module): a plain function call that plots
  one object's light curve given its id, for when the click-driven widget itself misbehaves
  (e.g. needs a browser reload) — the widget shows the clicked object's id independently of the
  light-curve panel for exactly this reason.

`src/visualization/` holds reusable plotting code shared across notebooks (currently just
`lc_explorer.py`); `src/dataio/` holds `select_slice` (`hq_sample.py`), used by nb_02-05.
Neither is pip-installed on RSP — the pinned Python 3.14 here is newer than RSP's kernel (see
above) — notebooks add `src/` to `sys.path` directly instead.

## Documentation

- `docs/SPEC_V01.md` — goals, non-goals, and the rough plan for the notebook series.
- `docs/changelog.md` — what changed and why.
- `docs/backlog.md` — known gaps and future work.
