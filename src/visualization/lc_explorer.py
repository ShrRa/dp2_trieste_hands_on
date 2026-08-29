"""Interactive scatter-plot-plus-light-curve explorer (SPEC_V01.md, rough plan step 6).

Click a point in a scatter plot (color-magnitude, period-amplitude, or anything else keyed by
an object id), see that object's light curve on the right. Built on `plotly.graph_objects`
`FigureWidget` + `ipywidgets`, which need a live Jupyter kernel with widget support (JupyterLab
on RSP is the target; this hasn't been checked in VSCode or other IDEs).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd
import ipywidgets as widgets
import plotly.graph_objects as go
import plotly.colors as pcolors

DEFAULT_BANDS = "ugriz"  # per spec: default bands to plot, y excluded
DISCRETE_PALETTE = pcolors.qualitative.Plotly

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
) -> widgets.HBox:
    """Scatter plot (left) linked to a per-object light curve (right), click to update.

    Parameters mirror SPEC_V01.md's rough plan step 6: `scatter_df`/`x_col`/`y_col` are the
    scatter data (any flat pandas DataFrame — a CMD, a period-amplitude diagram, ...); `lc_df`
    is the light-curve data, keyed by the same `id_col` as `scatter_df` (see `_fetch_lightcurve`
    for the two shapes it accepts); `bands` are the bands drawn in the light-curve panel;
    `period_col`, if given, names a column in `scatter_df` holding each object's period, enabling
    the fold toggle. `x_log`/`y_log` set a log scale on the scatter panel's axes (a period axis
    usually wants this) — purely cosmetic, doesn't affect the point indices the click handler
    uses. Returns an `ipywidgets.HBox` — display it (or let it be the cell's last expression) in
    a Jupyter session with widget support.
    """
    scatter_df = scatter_df.reset_index(drop=True)

    hover_text = scatter_df[id_col].astype(str)
    marker = dict(size=6, opacity=0.7)
    if color_col is not None:
        values = scatter_df[color_col]
        if pd.api.types.is_numeric_dtype(values):
            marker.update(color=values, colorscale="Plasma", showscale=True, colorbar=dict(title=color_col))
        else:
            # A continuous colorscale can't take strings — map categories to a discrete palette
            # instead (no legend on a single go.Scatter trace, so the category rides along in
            # the hover text instead).
            categories = sorted(values.astype(str).unique())
            cat_to_color = {c: DISCRETE_PALETTE[i % len(DISCRETE_PALETTE)] for i, c in enumerate(categories)}
            marker.update(color=[cat_to_color[v] for v in values.astype(str)])
        hover_text = hover_text + " | " + color_col + "=" + values.astype(str)

    scatter_fig = go.FigureWidget(
        data=[go.Scatter(x=scatter_df[x_col], y=scatter_df[y_col], mode="markers", marker=marker, text=hover_text, hoverinfo="text")]
    )
    scatter_fig.update_layout(title=scatter_title or f"{y_col} vs {x_col}", xaxis_title=x_col, yaxis_title=y_col, width=460, height=460)
    if "mag" in y_col.lower():
        scatter_fig.update_yaxes(autorange="reversed")
    if x_log:
        scatter_fig.update_xaxes(type="log")
    if y_log:
        scatter_fig.update_yaxes(type="log")

    lc_fig = go.FigureWidget()
    for b in bands:
        lc_fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="markers",
                name=b,
                showlegend=True,
                marker=dict(color=BAND_COLORS.get(b)),
                error_y=dict(type="data", array=[], visible=False),
            )
        )
    # showlegend=True at the layout level too: plotly defaults to hiding the legend when only
    # one trace actually has data (the other bands' traces are empty, not just invisible), which
    # would otherwise leave a single-band light curve with no indication of which band it is.
    lc_fig.update_layout(width=560, height=460, xaxis_title="MJD", yaxis_title=mag_col, showlegend=True)
    if "mag" in mag_col.lower():
        lc_fig.update_yaxes(autorange="reversed")
    # Plain full MJD values on the x-axis — plotly's default numeric tick formatting abbreviates
    # a range like 60880 into "60.88k" otherwise.
    lc_fig.update_xaxes(tickformat=".2f", exponentformat="none")

    has_period = period_col is not None
    fold_toggle = widgets.ToggleButtons(options=[("Folded", True), ("Unfolded", False)], value=has_period, disabled=not has_period)
    err_toggle = widgets.Checkbox(value=True, description="show flux errors")
    info = widgets.HTML("<i>click a point in the left panel</i>")

    state: dict = {"obj_id": None}

    def render():
        obj_id = state["obj_id"]
        if obj_id is None:
            return
        try:
            _render(obj_id)
        except Exception as exc:  # noqa: BLE001 - deliberately broad: see comment below.
            # ipywidgets swallows exceptions raised inside on_click/observe callbacks instead of
            # showing them anywhere in the notebook (they go to the kernel's terminal log at
            # best) - a misconfigured column name would otherwise look exactly like "clicking
            # does nothing", with no way for a user to tell why. Surface it in the info panel.
            info.value = f"<b style='color:#b00'>Error rendering diaObjectId={obj_id}: {type(exc).__name__}: {exc}</b>"
            raise

    def _render(obj_id):
        lc = _fetch_lightcurve(lc_df, obj_id, id_col, nested_col, time_col, mag_col, magerr_col, band_col)

        period = None
        if has_period:
            match = scatter_df.loc[scatter_df[id_col] == obj_id, period_col]
            if len(match) and pd.notna(match.iloc[0]):
                period = float(match.iloc[0])
        fold = fold_toggle.value and period is not None and period > 0

        with lc_fig.batch_update():
            for trace, b in zip(lc_fig.data, bands):
                sel = lc[band_col] == b
                t = lc.loc[sel, time_col].to_numpy()
                mag = lc.loc[sel, mag_col].to_numpy()
                magerr = lc.loc[sel, magerr_col].to_numpy()
                trace.x = (t / period) % 1.0 if fold else t
                trace.y = mag
                trace.error_y = dict(type="data", array=magerr, visible=bool(err_toggle.value))
            lc_fig.update_layout(
                title=f"diaObjectId={obj_id}" + (f", period={period:.3f} d" if fold else ""),
                xaxis_title="phase" if fold else "MJD",
            )
        period_text = f" | period={period:.3f} d" if period is not None else " | no period available"
        info.value = f"<b>diaObjectId={obj_id}</b>{period_text if has_period else ''}"

    def on_click(_trace, points, _state):
        if not points.point_inds:
            return
        state["obj_id"] = scatter_df.iloc[points.point_inds[0]][id_col]
        render()

    scatter_fig.data[0].on_click(on_click)
    fold_toggle.observe(lambda _change: render(), names="value")
    err_toggle.observe(lambda _change: render(), names="value")

    controls = [err_toggle] if not has_period else [fold_toggle, err_toggle]
    right_panel = widgets.VBox([info, widgets.HBox(controls), lc_fig])
    return widgets.HBox([scatter_fig, right_panel])
