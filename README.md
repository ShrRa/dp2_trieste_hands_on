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

More notebooks (light-curve statistics, color-magnitude diagrams, period finding) are being
added following the rough plan in `docs/SPEC_V01.md`.

## Documentation

- `docs/SPEC_V01.md` — goals, non-goals, and the rough plan for the notebook series.
- `docs/changelog.md` — what changed and why.
- `docs/backlog.md` — known gaps and future work.
