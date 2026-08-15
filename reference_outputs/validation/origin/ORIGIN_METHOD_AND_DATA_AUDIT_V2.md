# Origin Method and Data Audit (V2)

**Date:** 2026-08-15
**Status:** Audit only. Stage 9A frozen outputs were not modified and no alternative-origin routing was run. Its bounded interpretation was subsequently incorporated into the dissertation.

## Population-weighting feasibility

- `inputs/tpu_origins_v3.csv`: one centroid point per TPU. No intra-TPU population surface.
- `inputs/census_stpug_v3.csv`: population at STPUG level (a different 211-unit partition), not below TPU level.
- Geometry files are polygons only.

**Conclusion:** No population data exist below the TPU level, so a defensible population-weighted origin within each TPU cannot be constructed. Population weights are NOT invented and no centroid is relabelled as population-weighted.

## Why no re-route was run and what this deliverable therefore is

A true origin-sensitivity test requires re-routing alternative origins with the r5r/R5 engine (Java + OSM + GTFS) under identical parameters. That was not run (environment/budget). This deliverable is therefore renamed a **threshold-margin diagnostic**: it reports only the frozen distribution of zero-access minimum times relative to the 60-minute threshold. It is NOT a bounding analysis and NOT an origin-sensitivity result, because:

- the 5- and 10-minute figures are arbitrary arithmetic buffers, not values derived from TPU geometry, the walk network, stop distribution or alternative-origin routing;
- a within-TPU origin change can alter the nearest stop, line, transfer pattern and waiting time, not only the walk leg, and in large or unevenly served TPUs the effect can exceed 10 minutes;
- the direction of change is unknown: an alternative origin can worsen as well as improve access.

## What can and cannot be said

- CAN: report the frozen distribution and note that 52 zero-access TPUs lie within 10 minutes above the threshold, so the exact 66.0% share may be sensitive to within-TPU origin placement.
- CANNOT: claim any lower bound, any "realistic" revised share, any count of TPUs that "cannot flip", or any conclusion that the majority result is robust to origin definition. None of these are supported without a re-route.
