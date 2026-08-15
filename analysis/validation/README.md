# Validation checks added on 15 August 2026

This folder contains two read-only diagnostics cited in the dissertation. They
do not modify the frozen Stage 9A results.

## MTR external plausibility check

```bash
python3 analysis/validation/extract_modelled_times_v2.py
```

The script reads station-to-station times from the frozen analytical MTR feed.
The saved comparison table, source log and report are under
`reference_outputs/validation/mtr/`. Two gateway benchmarks come from the Hong
Kong Transport Department; the four non-East-Rail anchors are approximate
secondary sources. This is a small plausibility check, not a full network
validation, and the aggregate accessibility indicators were not re-estimated.

## TPU threshold-margin diagnostic

```bash
python3 analysis/validation/threshold_margin_diagnostic_v2.py
```

The script describes how centroid-based minimum times sit relative to the
60-minute threshold. The saved table, method audit and report are under
`reference_outputs/validation/origin/`. No alternative origins were re-routed;
the diagnostic therefore does not estimate the direction or magnitude of
origin sensitivity.
