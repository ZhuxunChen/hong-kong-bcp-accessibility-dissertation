# TPU Threshold-Margin Diagnostic (V2)

**Date:** 2026-08-15
**Status:** Diagnostic of the frozen distribution only. No re-route was run, no population weights were constructed and Stage 9A frozen outputs were not modified. Its bounded interpretation was subsequently incorporated into the dissertation.

## 1. What this is

This reports how the frozen, centroid-based minimum travel times of the zero-access TPUs sit relative to the 60-minute threshold. It is a **threshold-margin diagnostic**, not a bounding analysis and not an origin-sensitivity result. Alternative origins were not routed, so the effect of origin definition cannot be estimated.

## 2. Frozen baseline (unchanged)

- Stable-routed TPUs: 209
- Mean minimum travel time 67.0 min; median 66.0 min
- Zero-access within 60 min: 138 TPUs = **66.0%** (centroid-based)

## 3. Distribution of the 138 zero-access TPUs

| min_tt band | count |
|---|---:|
| (60, 70] | 52 |
| (70, 80] | 43 |
| (80, 90] | 23 |
| > 90 | 20 |

Median minimum time among zero-access TPUs: 74.0 min; minimum 61.0 min. **52 of the 138 zero-access TPUs lie within 10 minutes above the 60-minute threshold.**

## 4. Illustrative arithmetic scenarios (NOT bounds, NOT estimates)

Purely to show the threshold's arithmetic sensitivity, if the zero-access TPUs within a fixed buffer above 60 minutes were hypothetically removed:

- subtract those in (60, 65]: 26 TPUs -> the share would arithmetically read 53.6%.
- subtract those in (60, 70]: 52 TPUs -> the share would arithmetically read 41.1%.

These are **illustrative arithmetic only**. The 5- and 10-minute buffers are not derived from geometry, the walk network or routing; they ignore TPUs whose access could worsen under an alternative origin; and they are neither lower bounds nor realistic estimates.

## 5. Lo Wu-adjacent TPU 622

TPU 622 has min_tt = 52.0 min and reaches 3 BCPs within 60 min. It is already reachable and is **not** part of the 66%.

## 6. Conclusion

- The 66.0% is a **centroid-based threshold estimate**.
- Because 52 zero-access TPUs lie within 10 minutes above the threshold, the exact 66.0% share **may be sensitive to within-TPU origin placement**.
- Because alternative origins were not re-routed, **neither the direction nor the magnitude of that sensitivity can be estimated** from the available data.

No claim is made that the figure is a lower-bounded, robust, or majority-preserving result, and this diagnostic is not combined with the MTR check to assert a common bias direction.
