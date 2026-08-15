#!/usr/bin/env python3
"""Read-only threshold-margin diagnostic on the 60-min zero-access share.
Uses frozen accessibility_tpu_v3.csv only. Does NOT re-route or modify any file.
Outputs the distribution of zero-access minimum times and clearly-labelled
illustrative arithmetic scenarios. These scenarios are NOT bounds and NOT estimates."""
import csv, statistics as st, sys
from pathlib import Path
DEFAULT = (
    Path(__file__).resolve().parents[2]
    / "reference_outputs/stage9a/results/accessibility_tpu_v3.csv"
)
f = sys.argv[1] if len(sys.argv)>1 else DEFAULT
rows=list(csv.DictReader(open(f)))
n=len(rows); mintt=[float(r['min_tt']) for r in rows]
zero=[float(r['min_tt']) for r in rows if int(r['bcps_within_60'])==0]
print(f"stable_routed_TPU={n}")
print(f"mean_min_tt={sum(mintt)/n:.1f} median_min_tt={st.median(mintt):.1f}")
print(f"zero_access_60={len(zero)} share={len(zero)/n*100:.1f}%")
print(f"zero_access_min_tt_median={st.median(zero):.1f} min_tt_min={min(zero):.1f}")
for lo,hi in [(60,70),(70,80),(80,90),(90,999)]:
    print(f"  band ({lo},{hi}]: {sum(1 for v in zero if lo<v<=hi)}")
print("--- ILLUSTRATIVE ARITHMETIC SCENARIOS (not bounds, not estimates) ---")
for buf in (5,10):
    m=sum(1 for v in zero if v<=60+buf)
    print(f"  if {m} TPUs in (60,{60+buf}] are hypothetically subtracted: share would arithmetically read {(len(zero)-m)/n*100:.1f}% "
          f"(illustrative only; buffer not derived from geometry/network; ignores TPUs that could worsen)")
