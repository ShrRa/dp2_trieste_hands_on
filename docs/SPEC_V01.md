# Repository for initial LSST DP2 analysis of variable objects. Trieste Regional Workshop version (August 2026)

## The goals: 

- Get candidates for periodic, stochastic, and transient objects in the DP2.
- Get their main properties distributions: histograms of numbers of detections, baseline durations, limiting magnitudes, colors, characteristic times, etc.
- Search for objects of specific variable types, e.g. RR Lyrae, Cepheids, stellar flares, AGNS - depending on the expertise of the people present during the hands-on.
- Visually spot-check LCs of these objects, write down most obvious failure modes (problematic cadence gaps, uneven bands coverage, photometric scatter laying outside of the photometric errors boundaries...)

## The non-goals:

- No completeness analysis - for that we need to have full catalog and to make sure we're not missing something because of the margins, quality flags being overly cautious, etc.
- Not crossmatch with other catalogs - that would require careful considerations of field crowdedness, separation limits, and detection quality. No time for this yet.
- No model fitting at scale - same reason, time/resources.

## TODO:

- **Catalog reading features**. 
    - *Problem:* LSDB DP2 collections are over 5Tb in total; if we try to query it all at once on RSP, we'll spend the whole session meditating on the progress bar. 
    - *Solution:* I am downloading diaObject and Object collections filtered to keep only the objects with more than 10 sources/diaSources (~300 Gb in total). From these, I'll select several partitions with up 4 Gb of total volume to upload to a shared folder, for the participants to download it in advance to their laptops/preferred clusters to work in peace. Querying those on RSP, of course, also remain an option.
    - *TODO before workshop* setup `datapaths` artifacts.yaml, prepare a notebook demonstrating how to load, query, convert to numpy/pandas, and save subsets of data.
- **Histogram visualization features**.
    - *Problem:* We're using HATS with nested columns, for which we have to calculate cumulative statistics (+ some simple statistics, like colors).
    - *Solution:* Prepare a couple of demos of how to handle creating new statistics for this data format.
    - *TODO before workshop:* Make a demo notebook demonstrating histograms for nDiaSources, LCs durations, and min/max/median colors for LCs.
    - *TODO during the workshop:* Visually inspect LCs and analyze how to handle outliers that will be skewing these statistics.
- **Specific types search**.
    - *Problem:* Each type has its own selection criteria. We need to understand how reliable are these selection criteria for DP2 data. Warning: we'll need to compute a number of things for this (e.g. periods for periodic candidates), so we should measure performance in advance.
    - *Solution:* Pick several object types and search for them the way we'd do it for other catalogs.
    - *TODO before workshop:* Measure period calculation performance on RSP and locally.
- **Visual spot-checking**.
    - *Problem:* We don't know what to expect from the data yet, so we need to have a look - but efficiently, to cover a lot of ground in the time that we have.
    - *Solution:* Interactive scatter plots with LC plotting upon clicking on the data point; multipanel LC plotter.
    - *TODO before workshop:* Implement the major visualization functions. Warning: interactive stuff will behave differently in Jupyter and in VSCode or other IDEs; write functions for both cases.