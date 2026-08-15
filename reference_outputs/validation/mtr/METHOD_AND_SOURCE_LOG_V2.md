# Method and Source Log (V2)

**External retrieval date:** 2026-08-15
**Environment note:** The official MTR journey planner is JavaScript-rendered and was not queried interactively. The two gateway benchmarks below use Hong Kong Transport Department official pages; the four non-East-Rail benchmarks use secondary published sources and are explicitly approximate.

## Modelled-time extraction

- Feed: `reference_outputs/stage9a/network/mtr_gtfs_bidirectional_v3/`.
- Modelled time = departure(destination) − departure(origin) on a representative trip of the relevant route in `stop_times.txt` (feed encodes no dwell). Pure inter-station running time.
- Script `extract_modelled_times_v2.py` resolves the feed path from `Path(__file__).resolve().parents[2]`, so it runs from the project root or from this folder.

## External sources (retrieved 2026-08-15)

| Segment | External figure | Source type | Page title | Full URL |
|---|---|---|---|---|
| Admiralty–Lo Wu | about 45 min | Official (Transport Department) | Access to Lo Wu Control Point | https://www.td.gov.hk/en/transport_in_hong_kong/land_based_cross_boundary_transport/access_to_lo_wu_control_point/ |
| Admiralty–Lok Ma Chau | about 50 min | Official (Transport Department) | Access to Lok Ma Chau Spur Line Control Point | https://www.td.gov.hk/en/transport_in_hong_kong/land_based_cross_boundary_transport/access_to_lok_ma_chau_spur_line_control_point/ |
| Central–Tsuen Wan | ~30 min | Secondary (approximate) | Tsuen Wan Line, Hong Kong MTR | https://www.travelchinaguide.com/cityguides/hongkong/transportation/metro-tsuenwan-line.htm |
| Hong Kong–Tung Chung | ~27 min | Secondary (approximate) | Tung Chung Line, Hong Kong MTR | https://www.travelchinaguide.com/cityguides/hongkong/transportation/metro-tungchung-line.htm |
| Central–Chai Wan | ~23 min | Secondary (approximate) | Island Line, Hong Kong MTR | https://www.travelchinaguide.com/cityguides/hongkong/transportation/metro-island-line.htm |
| Tuen Mun–Hung Hom | ~39 min | Secondary (approximate) | West Rail/Tuen Ma Line, Hong Kong MTR | https://www.travelchinaguide.com/cityguides/hongkong/transportation/metro-west-rail-line.htm |

## Independence note

Seven direct CSV rows were computed, but there are only **six unique external anchors**: Lo Wu→Admiralty reuses the same official 45-minute Lo Wu figure in reverse and is NOT an independent observation. The East Rail comparison rests on only **two unique official gateway anchors** (Lo Wu, Lok Ma Chau).

## Honesty controls

- No official journey time was invented. The two gateway figures are quoted from Transport Department pages; four others are secondary and marked approximate.
- Only in-vehicle station-to-station times are compared; door-to-door times (walking, waiting, interchange) are out of scope.
- Derived/single-stop journeys from the earlier version are not carried into V2.
