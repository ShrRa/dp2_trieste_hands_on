"""Interactive scatter-plot-plus-light-curve explorer (SPEC_V01.md, rough plan step 6).

Click a point in a scatter plot (color-magnitude, period-amplitude, or anything else keyed by
an object id), see that object's light curve on the right. Built on `holoviews` + `bokeh` +
`panel`, matching the stack used by RSP's own interactive-plot tutorials
(`notebooks/tutorials/DP2/300_Science_demos/312_Interactive_plots`) — all three ship in the
RSP `lsst-scipipe` kernel already, unlike the `plotly`/`ipywidgets`/`anywidget` combination this
replaced, which needed a manual `pip install` + browser reload the first time it was used there.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
from holoviews import opts, streams

hv.extension("bokeh")
pn.extension()

DEFAULT_BANDS = "ugriz"  # per spec: default bands to plot, y excluded

BAND_COLORS = {
    "u": "#7570b3",
    "g": "#1b9e77",
    "r": "#d95f02",
    "i": "#e7298a",
    "z": "#666666",
    "y": "#66a61e",
}


def _fetch_lightcurve(
    lc_df: pd.DataFrame,
    obj_id,
    id_col: str,
    nested_col: str | None,
    time_col: str,
    mag_col: str,
    magerr_col: str,
    band_col: str,
) -> pd.DataFrame:
    """Return a flat (time, mag, magerr, band) table for one object.

    `lc_df` is either nested (has a `nested_col` column holding a per-object sub-table, the
    shape `lsdb`/`nested_pandas` produce) or already flat (one row per epoch, `id_col` repeats).
    Either way it must already be materialized (a plain/nested pandas DataFrame, not a lazy
    `lsdb.Catalog`) — fetching per click has to be fast enough to feel interactive.
    """
    if nested_col is not None and nested_col in lc_df.columns:
        match = lc_df.loc[lc_df[id_col] == obj_id]
        if len(match) == 0:
            return pd.DataFrame(columns=[time_col, mag_col, magerr_col, band_col])
        nested = match.iloc[0][nested_col]
        for required in (time_col, mag_col, band_col):
            if required not in nested.columns:
                raise KeyError(
                    f"'{required}' not found in nested column '{nested_col}' "
                    f"(available: {sorted(nested.columns)}). If {required!r} actually lives in a "
                    f"different nested column (e.g. psfDiffFlux is in diaObjectForcedSource, not "
                    f"diaSource), pass the matching nested_col=... too."
                )
        magerr = np.asarray(nested[magerr_col], dtype=float) if magerr_col in nested.columns else np.full(len(nested), np.nan)
        return pd.DataFrame(
            {
                time_col: np.asarray(nested[time_col], dtype=float),
                mag_col: np.asarray(nested[mag_col], dtype=float),
                magerr_col: magerr,
                band_col: np.asarray(nested[band_col]),
            }
        )

    sub = lc_df.loc[lc_df[id_col] == obj_id, [time_col, mag_col, band_col]].copy()
    sub[magerr_col] = lc_df.loc[sub.index, magerr_col] if magerr_col in lc_df.columns else np.nan
    return sub


def _empty_lc_overlay(bands: Sequence[str], title: str, xlabel: str, ylabel: str, invert_yaxis: bool):
    curves = {b: hv.Scatter([], "x", "y").opts(color=BAND_COLORS.get(b), size=6) for b in bands}
    overlay = hv.NdOverlay(curves, kdims="band")
    return overlay.opts(
        opts.NdOverlay(
            width=560, height=460, title=title, xlabel=xlabel, ylabel=ylabel,
            legend_position="right", invert_yaxis=invert_yaxis,
        )
    )


def interactive_scatter_lc(
    scatter_df: pd.DataFrame,
    x_col: str,
    y_col: str,
    lc_df: pd.DataFrame,
    id_col: str = "diaObjectId",
    color_col: str | None = None,
    bands: Sequence[str] = DEFAULT_BANDS,
    period_col: str | None = None,
    nested_col: str | None = "diaSource",
    time_col: str = "midpointMjdTai",
    mag_col: str = "scienceMag",
    magerr_col: str = "scienceMagErr",
    band_col: str = "band",
    scatter_title: str | None = None,
    x_log: bool = False,
    y_log: bool = False,
):
    """Scatter plot (left) linked to a per-object light curve (right), click to update.

    Parameters mirror SPEC_V01.md's rough plan step 6: `scatter_df`/`x_col`/`y_col` are the
    scatter data (any flat pandas DataFrame — a CMD, a period-amplitude diagram, ...); `lc_df`
    is the light-curve data, keyed by the same `id_col` as `scatter_df` (see `_fetch_lightcurve`
    for the two shapes it accepts); `bands` are the bands drawn in the light-curve panel;
    `period_col`, if given, names a column in `scatter_df` holding each object's period, enabling
    the fold toggle. `x_log`/`y_log` set a log scale on the scatter panel's axes (a period axis
    usually wants this) — purely cosmetic, doesn't affect the point indices the click handler
    uses. Returns a `panel.Row` — display it (or let it be the cell's last expression) in a
    Jupyter session; no widget-support install needed beyond what RSP's kernel already ships.
    """
    scatter_df = scatter_df.reset_index(drop=True)

    vdims = [id_col]
    if color_col is not None and color_col != id_col:
        vdims.append(color_col)
    points = hv.Points(scatter_df, kdims=[x_col, y_col], vdims=vdims)

    point_opts = dict(
        size=6, alpha=0.7, tools=["tap", "hover"], nonselection_alpha=0.3,
        width=460, height=460, title=scatter_title or f"{y_col} vs {x_col}",
        logx=x_log, logy=y_log, xlabel=x_col, ylabel=y_col,
    )
    if color_col is not None:
        is_numeric = pd.api.types.is_numeric_dtype(scatter_df[color_col])
        point_opts.update(
            color=color_col,
            cmap="plasma" if is_numeric else "Category20",
            colorbar=is_numeric,
            legend_position="right" if not is_numeric else "top_right",
            show_legend=not is_numeric,
        )
    if "mag" in y_col.lower():
        point_opts["invert_yaxis"] = True

    points = points.opts(**point_opts)
    selection = streams.Selection1D(source=points)

    has_period = period_col is not None
    fold_toggle = pn.widgets.RadioButtonGroup(
        name="fold", options={"Folded": True, "Unfolded": False},
        value=has_period, disabled=not has_period,
    )
    err_toggle = pn.widgets.Checkbox(name="show flux errors", value=True)
    info = pn.pane.HTML("<i>click a point in the left panel</i>")

    lc_ylabel = mag_col
    lc_invert = "mag" in mag_col.lower()

    def render_lc(index, fold, show_err):
        if not index:
            info.object = "<i>click a point in the left panel</i>"
            return _empty_lc_overlay(bands, "no object selected", "MJD", lc_ylabel, lc_invert)

        obj_id = scatter_df.iloc[index[0]][id_col]
        try:
            lc = _fetch_lightcurve(lc_df, obj_id, id_col, nested_col, time_col, mag_col, magerr_col, band_col)
        except Exception as exc:
            # panel doesn't surface exceptions raised inside a bound callback anywhere in the
            # notebook by default — same footgun the plotly version hit with ipywidgets. Surface
            # it in the info panel before re-raising so it isn't silently swallowed.
            info.object = f"<b style='color:#b00'>Error rendering diaObjectId={obj_id}: {type(exc).__name__}: {exc}</b>"
            raise

        period = None
        if has_period:
            match = scatter_df.loc[scatter_df[id_col] == obj_id, period_col]
            if len(match) and pd.notna(match.iloc[0]):
                period = float(match.iloc[0])
        do_fold = fold and period is not None and period > 0

        curves = {}
        for b in bands:
            sel = lc[band_col] == b
            t = lc.loc[sel, time_col].to_numpy()
            mag = lc.loc[sel, mag_col].to_numpy()
            magerr = lc.loc[sel, magerr_col].to_numpy()
            x = (t / period) % 1.0 if do_fold else t
            band_df = pd.DataFrame({"x": x, "y": mag, "err": magerr})
            scatter_el = hv.Scatter(band_df, "x", "y").opts(color=BAND_COLORS.get(b), size=6)
            if show_err and len(band_df):
                curves[b] = hv.ErrorBars(band_df, "x", ["y", "err"]).opts(color=BAND_COLORS.get(b)) * scatter_el
            else:
                curves[b] = scatter_el

        title = f"diaObjectId={obj_id}" + (f", period={period:.3f} d" if do_fold else "")
        xlabel = "phase" if do_fold else "MJD"
        overlay = hv.NdOverlay(curves, kdims="band").opts(
            opts.NdOverlay(
                width=560, height=460, title=title, xlabel=xlabel, ylabel=lc_ylabel,
                legend_position="right", invert_yaxis=lc_invert,
            )
        )

        period_text = f" | period={period:.3f} d" if period is not None else " | no period available"
        info.object = f"<b>diaObjectId={obj_id}</b>{period_text if has_period else ''}"
        return overlay

    lc_dmap = hv.DynamicMap(pn.bind(render_lc, index=selection.param.index, fold=fold_toggle, show_err=err_toggle))

    controls = [err_toggle] if not has_period else [fold_toggle, err_toggle]
    right_panel = pn.Column(info, pn.Row(*controls), lc_dmap)
    return pn.Row(points, right_panel)
