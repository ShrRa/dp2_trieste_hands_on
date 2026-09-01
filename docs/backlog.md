# Backlog

- **Refactor notebooks 02-05 to use HQ sample, not the per-fields sample**:
  - Do this work in a new branch, nb-v02.

  - Since the hq-sample is still too large, at the beginning of each notebook we should select a partition to inspect (or run a cone search) for the participants to play with. The plots should be edited to treat the sample as a whole, without per-partition subplots.

   - However, LC statistics and periods should be calculated for the whole HQ sample, saved to the hq collection, and wrapped under the 'long calculations' flag.

- **nb_05 tech stack**: `interactive_scatter_lc` currently uses `plotly.graph_objects.FigureWidget`
  + `ipywidgets` (hit and resolved a `FigureWidget` requires `anywidget` issue — the RSP
  JupyterLab frontend didn't have it registered until a browser reload). Official RSP tutorials
  for interactive plots (`notebooks/tutorials/DP2/300_Science_demos/312_Interactive_plots`) use
  `bokeh` + `holoviews` instead — refactor nb_05 to match that stack for consistency with
  what workshop attendees will have already seen, and to avoid them having to install new packages in their environment, refresh pages, etc. 