# Changelog

## 2026-08-27

- Added `pyproject.toml`, exact-pinned from the `dp2_analysis` conda environment (Python 3.14.7), so the environment can be reproduced elsewhere via `pip install .`. The `datapaths` package is pulled from its repo (`git+https://github.com/ShrRa/datapaths.git@main`) rather than PyPI.
- Added `configs/roots.local.yaml` (gitignored) mapping `datapaths` roots to their locations on the RSP session used for development: `dp2_raw` (`/rubin/lsdb_data/dp2`), `dp2_filtered` (the pre-filtered `nDiaSources > 10` copy at `/deleted-sundays/shrra-ung/dp2`), `dp2_subset` (`~/share/trieste`), `misc` (`~/DATA/DP2`).
- Rewrote `notebooks/01_read_diaObj.ipynb` (nb_01 from the rough plan): surveys all 8393 `diaObject` partitions cheaply via parquet `_metadata` footer stats (row counts + `max(nDiaSources)`, no data read), selects 4 partitions spanning low/high galactic latitude and low/high cadence, filters to `nDiaSources > 10`, writes the ~700 MB / ~5000-object subset to `dp2_subset`, and registers it in `configs/artifacts_registry.yaml` as `dia_object_lc_10plus`. Also demonstrates the pandas/numpy conversion and the `explode`-based long-format light-curve table called for in the spec.
  - Notable finding folded into the notebook: picking partitions by raw object count is a poor proxy for cadence — 110/8393 partitions have `max(nDiaSources) <= 10` and yield zero objects after filtering; selection now uses `max(nDiaSources)` per partition (also free from the `_metadata` footer) instead.
- Added `README.md` and cleaned up `.env.example` (previously copy-pasted from the `datapaths` docs' own example, pointing at an unrelated machine/repo).
