# Changelog

## 2026-09-03 (4)

- Suppressed the `BokehUserWarning: out of range integer may result in loss of precision`
  spam nb_05's interactive plots print (one per plotted object) — the user's question about
  whether it needed attention. Root cause: `diaObjectId` (~1e17-1e18) is passed to the scatter
  plot as a hover-tooltip field, and Bokeh's `int64` arrays can't be binary-encoded at all
  (`bokeh/util/serialization.py`'s `BINARY_ARRAY_TYPES` doesn't include `int64` — a documented
  Bokeh limitation, not specific to this data), so every `int64` array always falls back to
  encoding each element as a scalar Python `int`, warning per element once its value exceeds
  JavaScript's exact-integer range (`2**53`) — genuinely lossy for the copy of the id rendered
  client-side (e.g. in a hover tooltip), but harmless here: the click handler always looks up
  the exact `int64` id server-side from the clicked point's *index*, never from the
  BokehJS-rendered value (already noted when the user first asked about this).
  - Fix: one `warnings.filterwarnings("ignore", message=..., category=BokehUserWarning)` in
    `src/visualization/lc_explorer.py`, filtered on the exact message text so other, actionable
    `BokehUserWarning`s (a different message) still show.
  - Verified against the real Bokeh install: `hv.renderer("bokeh").get_plot(...)` alone doesn't
    trigger the warning (it only fires at serialization, e.g. `bokeh.embed.json_item`, which is
    what actually runs when a plot is displayed in Jupyter) — reproduced 2 warnings for a
    2-point `int64` id column via `json_item` before the fix, 0 after; confirmed an unrelated
    `BokehUserWarning` with different text still surfaces normally.

## 2026-09-03 (3)

- Made `datapaths` optional for `notebooks/05_interactive_explorer.ipynb`, per the user's plan
  that the workshop will only run nb_05 itself, not nb_01-04 — so attendees won't be running the
  notebooks that write/register artifacts, and installing `datapaths` just to *read* the
  already-built `dia_object_lc_hq` collection has no payoff for them.
  - The setup cell now tries `datapaths` first (so it still works unchanged for anyone who has
    it configured), and falls back to `dia_object_lc_hq`'s well-known shared path
    (`Path.home() / "share" / "trieste" / "dia_object_lc_hq"`) on any exception — not just
    `ImportError`, since an uninstalled `roots.local.yaml` (which nb_05 attendees also won't
    have) fails inside `Datapaths()` itself, not at import time. That path matches what
    `datapaths` itself resolves `dp2_subset` to (confirmed against this session's own
    `configs/roots.local.yaml` and `configs/artifacts_registry.yaml`), and works for any RSP
    user's home without per-user configuration, so no separate path needs to be documented.
  - Verified directly: `lsdb.open_catalog(Path.home() / "share" / "trieste" /
    "dia_object_lc_hq")` opens the real 4,445-partition collection with no `datapaths` import at
    all.
  - Updated the notebook's intro markdown and README's Setup section (nb_05 no longer needs its
    own subsection there) to say installing `datapaths` is only needed for nb_01-04.

## 2026-09-03 (2)

- Found and fixed a second, worse instance of the same NdOverlay-type-mismatch bug class from
  the entry below, plus added a click-independent failsafe, per the user's report that the
  click no longer errors but the light curve still doesn't show (suspected stale `bokeh`/`panel`
  browser comm needing a reload — can't be confirmed without a live RSP session).
  - **Second instance**: `render_lc`'s "no selection yet" placeholder (`_empty_lc_overlay`)
    always built plain `hv.Scatter` per band, while a real selection with `show_err=True` builds
    `hv.Overlay`. Both are frames of the *same* `hv.DynamicMap`, and holoviews requires
    homogeneous element types across a `DynamicMap`'s successive frames just as it does across
    one `NdOverlay`'s keys — so the very first click (transitioning from the empty frame to a
    real one), or clicking blank space to deselect (transitioning back), hit the same class of
    crash the prior entry's fix didn't cover. Reproduced directly: simulating a deselect click
    right after a real one raised `AttributeError: 'Scatter' object has no attribute 'items'` in
    holoviews' stream-triggered frame update, against the real RSP `holoviews` install.
  - **Fix, structural this time rather than another one-off patch**: every band's element is now
    unconditionally `hv.ErrorBars(...) * hv.Scatter(...)` (an `hv.Overlay`) in every state — a
    band with no data, `show_err` on or off, and the empty-selection placeholder all build the
    identical type now. `show_err` only toggles the `ErrorBars` layer's `visible` option instead
    of whether it's present at all, so no code path can reintroduce a type mismatch by
    construction. Applied identically in the new `plot_lightcurve` (below) and
    `_empty_lc_overlay`.
  - **Added `plot_lightcurve(lc_df, obj_id, ..., period=None, fold=False, show_err=True)`**
    (`src/visualization/lc_explorer.py`, exported from `src/visualization/__init__.py`): the
    same per-object light-curve plot as `interactive_scatter_lc`'s click handler, as a plain
    function call — no click, stream, or `panel` widget involved — so it works standalone in its
    own notebook cell regardless of whatever state the interactive widget's `bokeh`/`panel` comm
    is in. `fold` is an explicit parameter here (not a toggle), since there's no widget to bind
    one to. `render_lc` now calls this function internally too, rather than duplicating the
    curve-building logic, so the interactive and manual paths can't drift apart.
  - **Added an independent "selected id" panel** to `interactive_scatter_lc`'s right column,
    bound straight to the click stream's index and displayed above the light-curve panel —
    deliberately *not* wired through `render_lc`/`lc_dmap`, so it keeps showing which
    `diaObjectId` was clicked even if the light-curve panel itself stops refreshing. The intended
    workflow when that happens: read the id off this panel, call `plot_lightcurve` with it in a
    separate cell.
  - Updated nb_05 to import `plot_lightcurve` and added a demo cell after the CMD example showing
    the manual-fallback workflow (paste an id, call `plot_lightcurve` with `fold=False`/`True`).
  - **Verified** against the real RSP `holoviews`/`bokeh`/`panel` install (not a synthetic
    substitute): built `interactive_scatter_lc` against synthetic objects with deliberately
    partial band coverage and both a period and no period, then drove it entirely
    programmatically — simulated clicks (including click → click → deselect, the exact sequence
    that reproduced the second bug above), and both the fold and show-flux-errors toggles after a
    selection was already showing — all rendered through `hv.renderer("bokeh").get_plot(...)`
    without error. Also called `plot_lightcurve` standalone (folded, unfolded, object with data,
    object with none) and confirmed it plots correctly. Did not `nbconvert --execute` nb_05
    itself, since it reads the same `dia_object_lc_hq` collection nb_04 was actively writing to
    at the time — avoided the concurrent read against that collection rather than risk
    interfering with nb_04's in-progress run. nb_05's own live-click behavior in JupyterLab still
    needs the user's confirmation, same standing caveat as always.

## 2026-09-03

- Diagnosed and fixed the user's real `AttributeError: 'Overlay' object has no attribute
  'extents'` on clicking a scatter point in nb_05's `interactive_scatter_lc`
  (`src/visualization/lc_explorer.py`). Root cause: `render_lc`'s per-band `curves` dict, fed
  into one `hv.NdOverlay(curves, kdims="band")`, mixed `hv.Scatter` (bands with zero data points
  for the clicked object) and `hv.Overlay` (`ErrorBars * Scatter`, bands with data) whenever
  "show flux errors" was on — `curves[b]` only became an `Overlay` under `if show_err and
  len(band_df)`, so any object with data in some but not all of `bands` (the normal case, e.g.
  no `u`-band detections) produced a heterogeneous `NdOverlay`. `holoviews` requires all values
  under one `NdOverlay` key dimension to share a type; reproduced directly against the RSP
  kernel's actual `holoviews` install as `AssertionError: NdOverlay must only contain one type
  of object, not both Overlay and Scatter` when constructed directly — the live-click path
  apparently reaches a different internal code branch (range/extents computation across
  `DynamicMap` frames) that surfaces the same underlying type mismatch as the `AttributeError`
  the user hit instead of that assertion, but the defect and fix are the same either way.
  - Fix: drop the `len(band_df)` condition so every band gets the same `Overlay` type
    (`ErrorBars * Scatter`) whenever `show_err` is on, regardless of whether that particular
    band has data for the clicked object — an empty `ErrorBars` just draws nothing.
  - Verified against the real RSP `holoviews`/`bokeh` install (not a synthetic substitute): the
    pre-fix code reproducibly hit the type-mismatch assertion for an object with partial band
    coverage plus `show_err=True`; the post-fix code builds a homogeneous `NdOverlay` and
    compiles through `hv.renderer("bokeh").get_plot(...)` without error for the same case.
    Live-click confirmation in JupyterLab still needed from the user, per this repo's standing
    caveat that `interactive_scatter_lc`'s click behavior can't be verified non-interactively.

## 2026-09-02 (2)

- Fixed a real failure the user hit running nb_04 for real: `write_catalog(tmp_path,
  resume=True, ...)` crashed with `RuntimeError: ... AppendRowGroups requires equal schemas.
  This schema has 115 columns, other has 111`, leaving `dia_object_lc_hq_nb04_singleband_tmp`
  (17 GB) half-written. Root cause: an earlier, interrupted attempt had already written some
  pixels to that temporary path under an older, narrower-schema version of
  `band_periods_partition` (before the previous entry added `periodogram_peaks`); resuming
  after the function changed meant the still-missing pixels got computed with the new,
  wider schema, and HATS's final metadata-assembly step can't combine row groups with
  different schemas — exactly the `resume=True` caveat already documented in every heavy-flag
  markdown, now actually encountered.
  - Added `write_catalog_resumable` (`src/dataio/hats_write.py`): wraps `Catalog.write_catalog`,
    catches specifically this `AppendRowGroups requires equal schemas` `RuntimeError`, deletes
    the target path, and retries the write once from scratch — so a schema mismatch now costs
    a full redo of that pass instead of a manual `rm -rf` and a cryptic pyarrow traceback.
    Verified the retry logic against a mock that raises the exact error message once then
    succeeds (control flow only — the real pyarrow failure mode wasn't cleanly reproducible in
    a quick synthetic test, but the fix targets the literal error string from the user's real
    traceback), and confirmed the happy path still works normally against a real `lsdb.Catalog`
    write.
  - Wired into all four heavy-write call sites (nb_02, nb_03, nb_04 single-band and multiband)
    in place of calling `.write_catalog()` directly.
  - Deleted the stale, half-written `dia_object_lc_hq_nb04_singleband_tmp` (17 GB) to unblock
    the user — one small `.nfs*` fragment inside it couldn't be removed (`Device or resource
    busy`, an NFS silly-rename file still held open by some process, likely the user's own
    live kernel from the failed attempt); harmless, and left alone to clear on its own rather
    than chasing down and killing whatever holds it (see the AGENTS.md note from the last time
    this session got that wrong).

## 2026-09-02

- nb_04's single-band and multiband Lomb-Scargle passes now also save the top-5 local maxima
  of each periodogram (`periodogram_peaks`/`multiband_periodogram_peaks`, new nested columns
  with `band`/`rank`/`period_days`/`power` sub-columns — no `band` for the multiband one,
  since that periodogram already pools all bands), per the user's point that only keeping the
  single best period per periodogram throws away exactly what aliasing checks need (the
  runner-up peaks, e.g. near known daily/yearly aliases).
  - Checked the actual periodogram grid size on real data before deciding how to store this:
    median ~660 `(freq, power)` points per band-object periodogram, up to ~1900. Saving the
    *whole* grid for the HQ sample would run to roughly a billion pairs for the single-band
    pass alone (tens of GB) — saving only local maxima (`scipy.signal.find_peaks`, not just
    the top-N raw grid points, which cluster around the single tallest peak rather than being
    distinct candidate periods) cuts that to an estimated ~7-8M peak rows.
  - Found and fixed the same class of empty-DataFrame bug as the earlier `map_partitions`
    entries, in a new place: `nested_pandas.NestedFrame.join_nested()` (the non-deprecated
    replacement for `add_nested()`) crashes packing an empty peaks table into a nested column
    when that table has no columns at all — which is exactly what `pd.DataFrame([])` (from an
    empty list of dicts) produces, and exactly what `map_partitions`'s empty-frame
    meta-inference call hits every time. Fixed by building the peaks table with explicit
    per-column dtypes (`pd.array(..., dtype=...)`) instead of inferring them from a
    possibly-empty list of dicts, so the column set exists even with zero rows.
  - Verified end to end against real HQ partition data: the peaks nested column round-trips
    correctly through `write_catalog`/reopen/`.explode()`, and — same rigor as the earlier
    `map_partitions` rewrite — re-ran the exact code extracted verbatim from the notebook file
    (not a hand-copied version) through the full nb_01→nb_02→nb_03→nb_04(single)→nb_04(multi)
    write-to-temp-then-promote chain, confirming no transcription error and that both new
    nested columns survive every subsequent promotion.
  - Clarified in nb_04 (unprompted question from the user) that `FULL_COLLECTION_ROWS` is
    purely cosmetic — it only feeds one projection print statement and has no effect on
    `write_catalog`/`map_partitions`/row counts; objects without a period are never dropped
    from the write regardless of that constant, since the periodogram functions fill `NaN`
    for them rather than removing the row.

## 2026-09-01 (6)

- Refactored nb_02-05 to read and write **one shared collection** (`dia_object_lc_hq`) instead
  of each spinning off its own `..._with_X` copy — per the user's report that disk quota was
  being eaten fast: `dia_object_lc_hq` (17 GB), `dia_object_lc_hq_with_stats` (17 GB), and
  `dia_object_lc_hq_with_mags` (15 GB) were all real, already on disk, each one a full copy of
  everything before it, nested light curves included — by nb_04 the same light curves would
  have existed on disk four times over (~66 GB for what's fundamentally one table gaining
  columns).
  - nb_02/nb_03/nb_04 (both passes) now write their new columns to a temporary path with
    `resume=True`, then *promote* it — delete the current `dia_object_lc_hq`, rename the
    temporary one into place — once the write actually completes, instead of writing to a
    separate collection name. This is the same write-to-temp-then-promote pattern nb_04's
    multiband pass already used to extend an existing collection in place; every heavy step
    needs it now, not just multiband, since `dia_object_lc_hq` already has content by the time
    any of nb_02/03/04 run (nb_01's base, plus whatever earlier notebooks already added) —
    `resume=True` straight onto it would silently skip writing new columns for every pixel
    that's already there, only checking whether a pixel's file exists, not whether it has the
    columns the current run would add.
  - All `dp.register()` calls in nb_02/03/04 now target the single name `dia_object_lc_hq`
    (`overwrite_history=True`, as before) instead of `dia_object_lc_hq_with_stats`/`_with_mags`/
    `_with_periods`; those three registry entries and artifact names are retired.
  - Renamed the per-notebook lazy-catalog variable (`stats_cat`, `mags_cat`, `periods_cat`,
    `cmd_cat`) to `hq_cat` everywhere, reflecting that every notebook now points at the same
    physical/logical collection — reopening it at any point in any notebook reflects whatever
    has actually been added so far, which may be more than that specific notebook's own
    columns if later notebooks already ran.
  - Verified the full nb_01→nb_02→nb_03→nb_04(single-band)→nb_04(multiband) chain end to end
    against a real HQ partition, promoting into the *same* path five times in a row — final
    collection has every expected column (light curves included) and reopens correctly.
    Additionally extracted the four `map_partitions` functions verbatim from the actual
    notebook files (not a hand-copied version) and re-ran the same chain against them
    specifically, to rule out a transcription error during editing.
  - Left the pre-existing `dia_object_lc_hq_with_stats`/`dia_object_lc_hq_with_mags`
    directories (~32 GB combined) and the registry's now-stray `dia_object_lc_hq_with_stats`
    entry alone rather than deleting/reverting them unasked — flagged to the user as the next
    thing to clean up once they've confirmed the new code reproduces what's needed.

## 2026-09-01 (5)

- Vectorized nb_02's `lc_stats_partition` and nb_03's `band_mags_partition` — replacing the
  `for i in range(len(df)): row = df.iloc[i]` loop each used inside its `map_partitions` call
  with `.explode(...)` (same method nb_01 uses) to a long, one-row-per-epoch table, followed by
  ordinary pandas `groupby` aggregations across every object in the partition at once. Per the
  user's own observation that the loop — a natural thing to reach for with a `map_rows`/
  `map_partitions`-style per-row API — wasn't actually necessary, since a nested column is just
  every object's epochs concatenated together.
  - **Measured on a real 75-partition, 2,713-object slice, not estimated**: nb_02's version is
    ~300x faster (0.35s vs 105s), nb_03's ~50x (2.1s vs 107s). At HQ scale (~399k objects,
    ~57x this slice) that projects nb_02's pass from ~4.4 hours down to ~50s, and nb_03's from
    ~4.4 hours down to ~5 minutes — the loop version would have made both about as expensive as
    nb_04's multiband pass, for computations that are actually cheap once vectorized.
  - Verified numerically identical to the original loop version on that same slice (exact
    match for nb_02's stats; nb_03's per-band medians differ by ~1e-6, a float32-storage
    rounding artifact between `np.median` and pandas' groupby `.median()`, not a logic
    difference) — every column, not spot-checked.
  - Found and fixed a real bug while vectorizing nb_02's amplitude calculation: an initial
    version used `groupby([id, band]).quantile([0.1, 0.9]).unstack(-1)` to get both
    percentiles in one pass, which crashes with `KeyError: 0.9` on an empty input — and
    `map_partitions` calls the function once on an empty `DataFrame` to infer its output
    schema when `meta` isn't given explicitly, so this would have broken *every* real
    `RUN_HEAVY_CALC=True` run, not just an edge case. Fixed by looping over the 6 bands (still
    fully vectorized across objects within each band) instead of trying to get both
    percentiles from one grouped call — simpler and empty-safe.
  - Re-verified the full `map_partitions` → `write_catalog(..., resume=True)` → reopen
    round-trip end to end with both new functions against real HQ partitions (not just the
    bare function output), same as the prior entry's approach for the loop versions.
  - nb_04's Lomb-Scargle functions are unchanged — `astropy.timeseries.LombScargle`/
    `LombScargleMultiband` operate on one object's own ragged, differently-sized time array at
    a time with no batched multi-object API, so there's no equivalent vectorization available
    there; the per-object loop is the actual computation, not a shortcut around it.

## 2026-09-01 (4)

- Reworked nb_02/nb_03/nb_04's heavy-calculation cells from `map_rows(..., append_columns=True)`
  onto `map_partitions`, per the user's own observation that the `.compute()` +
  `lsdb.from_dataframe()` roundtrip the previous entry's `map_rows` version needed (a
  workaround for a margin-cache-index bug, not something `map_rows` itself requires) forces
  the *entire* ~399k-object HQ sample into memory at once and makes the write all-or-nothing —
  risky, and not resumable.
  - `map_partitions` hands the per-partition function a whole `nested_pandas.NestedFrame`
    (nested columns stay nested, e.g. `row["diaSource"]["midpointMjdTai"]`, unlike `map_rows`'s
    flattened `row["diaSource.midpointMjdTai"]` convention) and returns a genuinely lazy
    `Catalog` — writing straight from it with `write_catalog(..., resume=True)` doesn't hit the
    margin-cache bug (verified against real HQ data at both single- and 75-partition scale, not
    just inferred), and `resume=True` — checked directly against the `lsdb`/`hats` source
    (`lsdb/io/to_hats.py`), not just its docstring — genuinely tracks and skips already-written
    pixels on a rerun, not just files.
  - Kept the Dask `dask.distributed.Client` the user added to nb_02 (per LSDB's own
    recommendation for this kind of computation) and added the same pattern to nb_03/nb_04,
    closed after each notebook's last heavy cell.
  - **`resume=True` only tracks which pixels exist on disk, not whether the mapped function
    changed** — every notebook's heavy-flag markdown now calls this out: editing
    `lc_stats_partition`/`band_mags_partition`/`band_periods_partition`/
    `multiband_period_partition` and rerunning with `resume=True` silently keeps stale values
    for any pixel already written under the old version. Delete the target collection (or pass
    `overwrite=True`) for a clean rebuild after a function change.
  - **nb_04's multiband pass (section 5) can't reuse `resume=True` in place**, since it *adds
    columns* to the already-complete single-band collection at the same path — `resume=True`
    would see those pixels' files already exist and skip writing the new multiband columns
    entirely, silently. Section 5 now writes to a temporary path with `resume=True` (protecting
    the ~4h-projected computation itself), then promotes it — delete the old collection,
    rename the temp one into place — once the write actually completes; verified end-to-end at
    small scale, including that the final collection carries every prior column (stats, mags,
    single-band periods, and the nested light curves) plus the two new multiband ones, not just
    the new columns.
  - nb_04's execution-time measurement (the spec's explicit ask) now wraps the `write_catalog`
    call itself rather than a separate `.compute()`, since that's what actually forces
    computation now; object counts for the ms/object rate come from
    `catalog.hc_structure.catalog_info.total_rows` (free, no data read) instead of `len()` on a
    materialized frame.
  - Caught and fixed a process-hygiene mistake while cleaning up after a test run in this
    session: ran `pkill -f "dask worker"`, which killed a Dask cluster that turned out to
    belong to the user's own long-running live JupyterLab kernel (a different process than
    this session's `nbconvert` test), not anything this session had started. No work was lost
    (nothing was running in it at the time), but added an "RSP session hygiene" section to
    `AGENTS.md`: check a process's parent PID/start time before killing it by pattern match,
    since this repo is worked on directly inside a shared live RSP session, not an isolated
    sandbox.
  - **Verification**: same approach as the prior entry (no HQ-scale run — nb_02's
    `RUN_HEAVY_CALC` was left `True`, as the user had set it, but not executed by this session
    for exactly that reason). All four `map_partitions` functions re-verified against real HQ
    partitions after the rewrite, including the write-to-temp-then-promote round-trip for
    nb_04's multiband case. `nbconvert --execute` on nb_03 and nb_04 (redirected to scratch
    files) both failed at the expected point — a `FileNotFoundError` on the upstream
    collection nb_02's real run hasn't produced yet — not from an unrelated bug.

## 2026-09-01 (3)

- Refactored nb_02-05 (on the new `nb-v02` branch, off `nb-v01`'s tip) to work on nb_01's HQ
  sample (`dia_object_lc_hq`, ~399k objects) instead of the old 5-field, 7,036-object subset,
  and rewrote nb_05's interactive explorer onto `holoviews`/`bokeh`/`panel`, closing both
  remaining `docs/backlog.md` items.
  - Added `src/dataio/hq_sample.py` (`select_slice`): picks either one partition or a cone
    search out of a lazy `lsdb.Catalog`. Every notebook from nb_02 on opens with a "pick a
    slice of the HQ sample" section using it, per the backlog's ask — nb_02-04 use it for a
    look-and-discard sample (their own plots work on the whole HQ sample); nb_05 uses it as
    its actual working dataset, since `interactive_scatter_lc`'s `lc_df` must be materialized
    and the whole ~399k-object sample is too big for that.
    - Named the package `dataio`, not the originally-planned `io` (see `pyproject.toml`'s old
      comment) — `io` would shadow Python's stdlib `io` module once nb_05 does
      `sys.path.insert(0, ...)` (prepending, not appending), silently breaking anything in the
      kernel that does `import io` afterward (pandas, pyarrow, IPython all rely on it). Caught
      before it shipped, not from a real failure.
  - nb_02: reads `hq_cat` directly instead of the old subset; the `nDiaSources` histogram is
    now one combined panel (no more per-field split — HQ has no `field` column). Folded what
    nb-v01 left as an open "Next" item — collapsing the separate compute-then-write steps into
    one `map_rows(..., append_columns=True)` call — into this pass, since running it unfolded
    at HQ scale would materialize the whole collection into memory twice. Output renamed
    `dia_object_lc_hq_with_stats`.
  - nb_03: same HQ-scale rename (`dia_object_lc_hq_with_mags`). Replaced all per-field
    scatter/legend plots with `hexbin` density maps — alpha-blended scatter that worked at
    ~7,000 points saturates into a solid blob well before HQ's ~399k, and there's no `field`
    column to split panels by anymore anyway. The CMD panel that used to color by amplitude
    per field now shows median r-band amplitude per hexbin instead (still answers "does
    variability track a part of the CMD", now as one whole-sample view instead of N per-field
    ones). Dropped the now-redundant "same, split per field" duplicate plot in section 4.
  - nb_04: same HQ-scale rename (`dia_object_lc_hq_with_periods`); single-band and multiband
    Lomb-Scargle stay behind one shared `RUN_HEAVY_CALC` flag (per explicit confirmation, given
    multiband's ~59x cost). Extrapolated nb-v01's measured per-object rates to HQ scale in the
    heavy-flag markdown: ~3.7 min single-band, ~3.9 hours multiband — not actually measured
    against the full sample yet (see below). Found and fixed a real staleness bug in the
    process: the multiband-vs-single-band comparison cell read the in-memory frame left over
    from the multiband `map_rows` cell, which only existed right after that cell had run — it
    now reopens the registered collection from disk instead.
  - nb_05: rewrote `src/visualization/lc_explorer.py`'s `interactive_scatter_lc` from
    `plotly.graph_objects.FigureWidget` + `ipywidgets` onto `holoviews` + `bokeh` + `panel` —
    the stack RSP's own interactive-plot tutorials use
    (`notebooks/tutorials/DP2/300_Science_demos/312_Interactive_plots`), and one already
    shipped in the RSP kernel with no extra install (unlike `anywidget`, needed for plotly's
    `FigureWidget`, which wasn't and needed `pip install --user anywidget` + a browser reload
    the first time nb-v01 hit it). Click handling now uses `hv.streams.Selection1D` on an
    `hv.Points` scatter, combined with `panel` toggle widgets via `pn.bind` +
    `hv.DynamicMap`; the function's public signature (`scatter_df`/`x_col`/`y_col`/`lc_df`/
    `color_col`/`period_col`/etc.) is unchanged, so nb_05's two demo calls only needed their
    data source and `color_col` updated (HQ has no `field` column; switched to
    `max_reliability`/`duration_days`).
    - **Resolved a real limitation of the old version in the process**: a categorical
      `color_col` couldn't get a per-category legend on a single plotly trace before (the
      category rode along in hover text instead); `holoviews`'s native categorical coloring
      draws a real legend, no workaround needed.
    - Kept `plotly`/`ipywidgets` in `pyproject.toml` (both predate nb_05 and
      `lc_explorer.py` in the pinned environment — confirmed via `git log` — so may be used
      elsewhere in the mirrored conda env); removed only `anywidget`, which the 2026-08-29
      entry confirms was added specifically for plotly's `FigureWidget` and has no other
      purpose in this repo. Added `holoviews==1.23.2` (the version this session's live RSP
      kernel actually has).
  - **Verification approach, given none of the HQ-scale heavy calcs were actually run in this
    session (explicit choice — code + small-scale verification only, not multi-minute-to-hour
    RSP compute)**:
    - `select_slice` (both modes) confirmed against the real `dia_object_lc_hq` collection.
    - Each notebook's `map_rows` function (nb_02's `lc_stats`, nb_03's `band_mags`, nb_04's
      `band_periods`/`multiband_period`) run end-to-end — including a real `write_catalog` +
      reopen round-trip for nb_02's — against a real single partition of the HQ sample (42
      objects), not a synthetic one.
    - nb_03's `hexbin` plotting and nb_05's `interactive_scatter_lc` (numeric `color_col`,
      categorical `color_col`, no `color_col`, no `period_col`, and the empty-selection state)
      all built and were forced through actual Bokeh plot compilation
      (`hv.renderer("bokeh").get_plot(...)`) against real HQ-derived data — not just "the
      Python object constructs without error".
    - nb_05's per-object light-curve rendering logic specifically was exercised for every
      object in a 42-object test partition, across all four fold/error-bar toggle
      combinations, with zero errors — the same "click everything programmatically" approach
      used to verify the plotly version on 2026-08-29.
    - `jupyter nbconvert --execute` on nb_02 (redirected to a scratch file, not the committed
      notebook) confirmed section 0/1 run cleanly against the real full HQ sample (the ~70 s
      whole-sample flat-column read included) and that execution fails exactly where expected
      — a `FileNotFoundError` on the not-yet-created `dia_object_lc_hq_with_stats` — not from
      an unrelated bug earlier in the notebook.
    - **Not done**: an actual full end-to-end `nbconvert --execute` of nb_02 through nb_05 with
      `RUN_HEAVY_CALC=True`. Whoever populates this branch's registry for real first should
      run nb_01 (already done) through nb_04 in order with the flag on once — expect nb_04's
      multiband pass specifically to take hours, not minutes — then re-verify nb_05 live in
      JupyterLab (its click-to-update behavior still can't be checked non-interactively either
      way, plotly or holoviews).

## 2026-09-01 (2)

- Added a `RUN_HEAVY_CALC` flag (default `False`) to nb_01, nb_02, nb_03, and nb_04, on the
  new `nb-v02` branch — one flag per notebook, gating only the expensive step each one has
  (nb_01's whole-collection HQ-sample query, nb_02's/nb_03's/nb_04's `map_rows` passes and the
  `write_catalog`/`dp.register` calls that follow them) so workshop participants can read and
  run each notebook end to end without relaunching a multi-minute-plus computation, while still
  being able to flip the flag to `True` and regenerate everything from scratch.
  - When `False`, each gated cell now loads its inputs from the already-registered artifact on
    disk instead (e.g. nb_02 reads `dia_object_lc_10plus_with_stats` rather than recomputing LC
    stats via `map_rows`) — reading/inspection/plotting sections downstream are otherwise
    unchanged and don't need the flag.
  - nb_04's single-band (sections 1-2) and multiband (section 5) Lomb-Scargle passes share one
    flag, per the ~59x cost difference already logged for multiband — flipping `RUN_HEAVY_CALC`
    reruns both together rather than one at a time.
  - Found and fixed a latent staleness bug while doing this: nb_04's multiband-vs-single-band
    comparison cell (after section 5) read the in-memory `merged_df` left over from the
    multiband `map_rows` cell, which only existed when that cell had just run — it now reopens
    `dia_object_lc_10plus_with_periods` from disk instead, so it works correctly whether or not
    `RUN_HEAVY_CALC` triggered a fresh write in the same run.
  - Verified all four notebooks end-to-end via `jupyter nbconvert --execute --inplace` with the
    new `RUN_HEAVY_CALC=False` default on the real RSP data/artifacts — no errors, and nb_02's
    reloaded stats and nb_04's reloaded periods matched the shapes/values from the original
    `RUN_HEAVY_CALC=True` runs logged earlier in this changelog.

## 2026-09-01

- Moved the high-quality sample (`nDiaSources > 100`, nb_01 section 5) from the private
  `/deleted-sundays/shrra-ung/dp2_hq` path it was manually written to, into the shared
  `dp2_subset` root (`~/share/trieste/dia_object_lc_hq`) so workshop attendees can actually
  reach it — the previous location wasn't accessible to them.
  - Copied all 4,454 files / ~17 GB across filesystems (`/deleted-sundays` → `/home`),
    verified file count, total bytes, and the `collection.properties` hash all matched before
    removing the old copy, and confirmed `lsdb.open_catalog` reads the new location correctly
    (4,445 partitions, same columns as before).
  - Fixed a real bug found in the process: nb_01 section 5 wrote to a hardcoded absolute path
    (`'/deleted-sundays/shrra-ung/dp2_hq'`) instead of going through `dp["dp2_hq"]` or any
    `datapaths` root at all — the write, the `dp.register` call, and the reopen afterward now
    all route through `dp["dp2_subset"] / "dia_object_lc_hq"` (a `hq_path` variable), matching
    every other artifact in this repo.
  - Updated `configs/artifacts_registry.yaml`'s `dia_object_lc_hq` entry (`root`/`type`
    `dp2_hq` → `dp2_subset`, `path` → `dia_object_lc_hq/collection.properties`) via
    `dp.register(..., overwrite_history=True)`, and retired the now-unused `dp2_hq` root from
    `configs/roots.local.yaml` (gitignored, machine-local only).

## 2026-08-29 (7)

- Root cause of the "no light curve appears" report found: the user's actual call set `mag_col`/
  `magerr_col` to `psfDiffFlux`/`psfDiffFluxErr` but left `nested_col` at its default
  (`"diaSource"`) — those two columns only exist in `diaObjectForcedSource`, so `_fetch_lightcurve`
  raised `KeyError: 'psfDiffFlux'` (confirmed by the user via RSP's log panel, not the notebook —
  the previous "surface errors in the info line" fix hadn't taken effect for them yet, since
  editing the `.py` file on disk doesn't retroactively patch an already-imported module in a
  running kernel; needs a kernel restart or `importlib.reload` plus re-running the widget cell).
  - Fixed `_fetch_lightcurve` to check `time_col`/`mag_col`/`band_col` against the chosen
    `nested_col`'s actual columns upfront and raise a specific `KeyError` naming the missing
    column, the nested column it was looked for in, and the full list of what's actually
    available there — plus a direct hint ("...pass the matching nested_col=... too") for exactly
    this mismatch, since a column living in a different nested table than the one selected is an
    easy mistake to repeat.
  - The scaling-artifact hypothesis from the previous entry no longer applies — this was always
    a straightforward `KeyError`, not a rendering issue.

## 2026-08-29 (6)

- Investigated a report that no light curve appears after clicking a scatter point when
  `interactive_scatter_lc` is configured with `nested_col="diaObjectForcedSource"`,
  `mag_col="psfDiffFlux"`. Clicked all 6907 objects in a reconstructed repro programmatically
  (via each trace's stored `_click_callbacks`, bypassing the need for a real browser) and found
  zero exceptions — so whatever's happening isn't a crash in this exact configuration, at least
  not one reproduced so far.
  - Along the way, fixed a real bug regardless: the light-curve panel's y-axis was
    unconditionally reversed (assuming a magnitude, smaller-is-brighter), which is wrong for a
    flux-valued `mag_col` like `psfDiffFlux` — now only reverses when `"mag"` is in `mag_col`.
  - Fixed a real diagnosability gap: ipywidgets silently swallows exceptions raised inside
    `on_click`/`.observe()` callbacks (they don't appear anywhere in the notebook, only
    potentially in the Jupyter server's terminal log) — `render()` now wraps its work in
    try/except and surfaces any error into the info line above the light-curve panel, so a
    future misconfiguration is visible instead of silently looking like "clicking does nothing".
  - Root cause not yet confirmed; leading hypothesis is a visual scaling issue, not a bug: forced
    photometry (`diaObjectForcedSource`) reports a value at every visit regardless of detection,
    so a typical object's `psfDiffFlux` clusters near zero at most epochs with only the actual
    detection epochs showing a real signal — a wide enough dynamic range on a linear axis could
    visually squash the real light curve into what looks like a flat, empty line.

## 2026-08-29 (5)

- Fixed two `interactive_scatter_lc` (`src/visualization/lc_explorer.py`) display issues, per
  user feedback after live-testing nb_05 on RSP:
  - MJD tick labels on the light-curve panel's x-axis were showing plotly's default abbreviated
    form (e.g. `60.88k`) instead of the full value — fixed with an explicit `tickformat=".2f"` +
    `exponentformat="none"` on that axis.
  - The band legend disappeared whenever only one band actually had data for the clicked object
    (plotly defaults to hiding the legend when just one trace has non-empty data, even though
    the other bands' traces still exist, just empty) — fixed with an explicit `showlegend=True`
    on both the layout and each trace, overriding that default.
  - Logged the `anywidget` failure and its resolution: `pip install --user anywidget` alone
    didn't register the frontend module in the live RSP JupyterLab session (`Failed to load
    model class 'AnyModel'`) — a browser reload fixed it, no code change needed. Also logged the
    user's pointer to RSP's own interactive-plot tutorials
    (`notebooks/tutorials/DP2/300_Science_demos/312_Interactive_plots`, bokeh + holoviews) as a
    `docs/backlog.md` item for a possible future tech-stack refactor.

## 2026-08-29 (4)

- Added `src/visualization/lc_explorer.py` (`interactive_scatter_lc`), implementing
  `docs/SPEC_V01.md`'s rough plan step 6: click a point in a scatter plot, see that object's
  light curve on the right, with toggles to fold on a period and to show/hide flux errors. Built
  on `plotly.graph_objects.FigureWidget` + `ipywidgets`, chosen over bokeh/bqplot/panel (all
  already pinned in `pyproject.toml`) after checking with the user, given the priority on
  reliable behavior in plain JupyterLab on RSP.
  - `pyproject.toml`'s `[tool.setuptools]` now actually builds `src/visualization` as a package
    (previously `py-modules = []`, with a comment noting it and `src/io` were still empty).
  - Found plotly 6.x's `FigureWidget` requires `anywidget`, which wasn't in the pinned dependency
    list and had to be installed separately (`pip install --user anywidget`) — added to both
    `pyproject.toml` and `README.md`'s setup section.
  - Found passing a categorical (string) column as `color_col` crashes plotly's continuous
    `colorscale` machinery (`marker.color` requires numeric values for a colorscale) — fixed by
    detecting non-numeric columns and mapping them to a discrete palette instead (no per-category
    legend on a single trace, so the category rides along in the hover text instead).
- Added `notebooks/05_interactive_explorer.ipynb`, demoing the function against nb_03's CMD and
  nb_04's period-amplitude data. Can't verify the actual click-to-update behavior via
  non-interactive `nbconvert --execute` (no simulated browser click) — only that the widgets
  build without error; real verification needs a live RSP JupyterLab session.
  - Found `jupyter nbconvert --execute --inplace` embeds a full widget-state snapshot in
    `metadata.widgets` on save — ~21 MB for this notebook (the scatter data serialized into the
    saved model), vs. ~11 KB without it. Stripped before committing (`nb["metadata"].pop
    ("widgets", None)`), since that snapshot only exists for static viewers (nbviewer, GitHub)
    and this notebook's whole point is being clicked live.

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
