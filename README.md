# DP2 Trieste hands-on

Notebooks for an LSST DP2 analysis of variable objects, prepared for the Trieste regional
workshop (August 2026). See `docs/SPEC_V01.md` for the full scope and rough plan.

## Setup

The notebooks are meant to run on the Rubin Science Platform (RSP), whose `lsst-scipipe`
kernel already provides `lsdb`/`hats`/`nested-pandas` etc. The only extra package needed is
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

- `notebooks/01_read_diaObj.ipynb` — visualizes the DP2 `diaObject` footprint (coverage map
  via `plot_pixels()`, plus a depth/cadence map built from r-band visit counts), lets you pick
  fields by eye as plain `(ra, dec)` coordinates, pulls each out with `cone_search`, filters to
  `nDiaSources > 10`, and writes/registers a small subset for the rest of the workshop to use.
  Also demonstrates converting a catalog to pandas/numpy and building a long-format
  light-curve table via `explode`.
- `notebooks/02_lc_histograms.ipynb` — `nDiaSources` histograms, plus per-object light-curve
  statistics (duration, cadence gap, per-band robust amplitude) computed from the nested
  `diaSource` column via `lsdb.Catalog.map_rows`. Writes the stats back as new columns on a
  derived HATS collection (`dia_object_lc_10plus_with_stats`), not a separate side table.
- `notebooks/03_color_mag_diagram.ipynb` — color-magnitude and color-color diagrams (`g-r` vs
  `r`, and `g-r` vs `r-i`; bands are plain variables). Per-band magnitudes come from
  `ForcedSourceOnDiaObject` (the nested `diaObjectForcedSource` column), aggregated per band
  via `map_rows` with a quality cut (>=3 unflagged points per band), since `diaObject`'s own
  columns are either difference-image-based or too sparsely populated to use directly, and a
  crossmatch to the `Object` (coadd) table was ruled out (slow, ambiguous in crowded fields).
  Also splits objects by `diaSource.reliability` (DP2's real/bogus score) as a stand-in for
  the point-source/extended split `diaObject.extendedness` would give — that column isn't
  reachable through this LSDB HATS collection. Output registered as
  `dia_object_lc_10plus_with_mags`.

- `notebooks/04_periods.ipynb` — per-band Lomb-Scargle periods (`astropy.timeseries.LombScargle`)
  via `map_rows`, longest findable period bounded by nb_02's light-curve duration. Measures and
  reports execution time (per the spec's ask), and folds the highest-power light curve as a
  sanity check — which turns out to look like noise, not a real signal, underlining that peak
  power alone isn't a usable real/bogus cut. Also runs `LombScargleMultiband` (pooling all
  bands per object) as a second pass: coverage jumps from ~34% to ~99.8% at ~59x the per-object
  cost, and compares the two against each other. Output registered as
  `dia_object_lc_10plus_with_periods`.

More notebooks (period-amplitude diagrams) are being added following the rough plan in
`docs/SPEC_V01.md`.

## Documentation

- `docs/SPEC_V01.md` — goals, non-goals, and the rough plan for the notebook series.
- `docs/changelog.md` — what changed and why.
- `docs/backlog.md` — known gaps and future work.
