# MTR External Plausibility Check (V2)

**Date:** 2026-08-15
**Status:** Small external plausibility check only. Stage 9A frozen outputs were not modified, and aggregate indicators and spatial models were NOT re-estimated. Its bounded interpretation was subsequently incorporated into the dissertation.

## 1. Scope and honest limits

This compares in-vehicle station-to-station times in the analytical MTR feed with published journey times. It is a small plausibility check, not a network validation. The word "validated" is deliberately avoided. Door-to-door times (walking, waiting, interchange) are out of scope.

## 2. Comparison

| Journey | Route | Modelled (min) | External (min) | Source | Unique anchor | Signed error |
|---|---|---:|---:|---|---|---:|
| Admiralty → Lo Wu | EAL | 54 | ~45 | Official (Transport Dept) | yes | +9 |
| Lo Wu → Admiralty | EAL | 54 | ~45 | Official (reverse duplicate) | no | +9 |
| Admiralty → Lok Ma Chau | EAL-LMC | 58 | ~50 | Official (Transport Dept) | yes | +8 |
| Central → Tsuen Wan | TWL | 32 | ~30 | Secondary (approx) | yes | +2 |
| Hong Kong → Tung Chung | TCL | 28 | ~27 | Secondary (approx) | yes | +1 |
| Central → Chai Wan | ISL | 26 | ~23 | Secondary (approx) | yes | +3 |
| Tuen Mun → Hung Hom | TML | 39 | ~39 | Secondary (approx) | yes | 0 |

## 3. Descriptive statistics (reported at two levels, not as a large sample)

- **Row-level (7 direct rows):** mean signed +4.57 min, mean absolute 4.57, median absolute 3, max 9.
- **Unique-anchor (6 unique external anchors):** mean signed +3.83 min, mean absolute 3.83, median absolute 2.5, max 9. (Lo Wu→Admiralty is excluded as a reverse duplicate of the Lo Wu anchor.)

These are small-sample descriptive figures, not statistical estimates of a network-wide error.

## 4. The two official gateway anchors

The two most important comparisons — the rail BCPs — rest on **two unique official Transport Department anchors**:

- Admiralty → Lo Wu: modelled 54 vs official ~45 → **+9 min**.
- Admiralty → Lok Ma Chau: modelled 58 vs official ~50 → **+8 min**.

**Both official gateway checks indicate an 8–9 minute overstatement in the analytical feed.** This is not generalised to a verified systematic error across the entire East Rail Line; it is two consistent gateway-level observations.

## 5. Non-East-Rail anchors

The four secondary anchors (Tsuen Wan, Tung Chung, Island, Tuen Ma) differ by 0–3 minutes (mean +1.5), consistent with rounding and differing end-to-end definitions. They are approximate secondary sources, not official.

## 6. What this does and does not support

- Supports: the feed is broadly plausible on the four non-gateway lines, and the two official gateway checks both show the feed running 8–9 minutes long.
- Does NOT support any claim about aggregate indicators: **the 60-minute zero-access share, nearest-BCP classification, Gini, Moran's I and the regression models were not re-estimated after this check.** The only defensible statement about direction is that the gateway overstatement is conservative for East-Rail-dependent journeys (it lengthens, not shortens, modelled time).

## 7. Verdict

**mixed evidence — usable as a small plausibility check with caveats.**

Both official gateway anchors indicate an 8–9 minute overstatement at the two rail BCPs; non-East-Rail secondary anchors match within 0–3 minutes. This may be written into the dissertation as a small external plausibility check and a limitation, but not as a full validation, not as a verified system-wide East Rail error, and not as evidence that aggregate or spatial results are unchanged.
