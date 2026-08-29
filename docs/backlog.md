# Backlog

- **nb_05 tech stack**: `interactive_scatter_lc` currently uses `plotly.graph_objects.FigureWidget`
  + `ipywidgets` (hit and resolved a `FigureWidget` requires `anywidget` issue — the RSP
  JupyterLab frontend didn't have it registered until a browser reload). Official RSP tutorials
  for interactive plots (`notebooks/tutorials/DP2/300_Science_demos/312_Interactive_plots`) use
  `bokeh` + `holoviews` instead — worth refactoring to match that stack for consistency with
  what workshop attendees will have already seen, and since it's presumably vetted to work on
  RSP's frontend build. Not done yet; current plotly version works, so this is a nice-to-have
  consistency pass, not a bug fix.
