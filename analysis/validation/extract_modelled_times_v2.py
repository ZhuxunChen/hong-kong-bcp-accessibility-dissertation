#!/usr/bin/env python3
"""Read-only: extract modelled in-vehicle station-to-station MTR times from the frozen feed.
Default feed path is resolved from this file's location so it runs from any cwd.
Does NOT modify any analytical file, script, frozen output or the dissertation."""
import csv, collections, sys
from pathlib import Path
DEFAULT = (
    Path(__file__).resolve().parents[2]
    / "reference_outputs/stage9a/network/mtr_gtfs_bidirectional_v3"
)
def load(feed):
    feed=Path(feed)
    trips={r['trip_id']:r['route_id'] for r in csv.DictReader(open(feed/"trips.txt"))}
    st=collections.defaultdict(list)
    for r in csv.DictReader(open(feed/"stop_times.txt")):
        st[r['trip_id']].append((int(r['stop_sequence']), r['stop_id'], r['departure_time']))
    for t in st: st[t].sort()
    return trips, st
def tmin(h): a,b,c=map(int,h.split(':')); return a*60+b+c/60
def modelled(trips, st, o, de, route_pref=None):
    best=None
    for tid,rid in trips.items():
        if route_pref and route_pref not in rid: continue
        ids=[s[1] for s in st[tid]]
        if o in ids and de in ids and ids.index(o)<ids.index(de):
            dt=tmin(st[tid][ids.index(de)][2]) - tmin(st[tid][ids.index(o)][2])
            best=dt if best is None else min(best, dt)
    return best
if __name__=="__main__":
    feed = sys.argv[1] if len(sys.argv)>1 else DEFAULT
    trips, st = load(feed)
    JN=[("Admiralty->Lo Wu","MTR_ADM","MTR_LOW","MTR_EAL"),
        ("Lo Wu->Admiralty (reverse-dup)","MTR_LOW","MTR_ADM","MTR_EAL"),
        ("Admiralty->Lok Ma Chau","MTR_ADM","MTR_LMC","MTR_EAL_LMC"),
        ("Central->Tsuen Wan","MTR_CEN","MTR_TSW","MTR_TWL"),
        ("Hong Kong->Tung Chung","MTR_HOK","MTR_TUC","MTR_TCL"),
        ("Central->Chai Wan","MTR_CEN","MTR_CHW","MTR_ISL"),
        ("Tuen Mun->Hung Hom","MTR_TUM","MTR_HUH","MTR_TML")]
    for label,o,de,rp in JN:
        print(f"{label:32} {modelled(trips,st,o,de,rp)}")
