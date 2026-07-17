# Stage 9A Input Preparation Audit

- Source TPU CRS: `WGS 84`.
- Area calculations use Hong Kong 1980 Grid (EPSG:2326) in metres.
- Census analytical rows: 211.
- Single-unit STPUGs: 166.
- Composite STPUGs: 45.
- Crosswalk TPU members: 292/292, each assigned exactly once.
- Rebuilt STPUG geometries and routing origins: 211.
- Rebuilt TPU geometries and routing origins: 292.
- TPU centroids replaced by on-surface points where needed: 13.
- STPUG centroids replaced by on-surface points where needed: 6.
- Existing single-unit census values reproduced exactly: TRUE.
- Six routing destinations are sourced by stop ID from the exact GTFS ZIP files.
- Sha Tau Kok is not included in the rebuilt main destination set.

## Destination provenance

| ID | BCP | Feed | Stop ID | Stop name | Longitude | Latitude |
|---|---|---|---|---|---:|---:|
| LW | Lo Wu | `mtr_gtfs.zip` | `MTR_LOW` | Lo Wu | 114.1142 | 22.52810 |
| LMC | Lok Ma Chau Spur Line | `mtr_gtfs.zip` | `MTR_LMC` | Lok Ma Chau | 114.0692 | 22.51470 |
| HG | Lok Ma Chau | `hk_gtfs.zip` | `10000339` | [XB] LOK MA CHAU CONTROL POINT (BOARDING STOP) | 114.0733 | 22.50991 |
| SB | Shenzhen Bay Port | `hk_gtfs.zip` | `12728` | [CTB] SHENZHEN BAY PORT/[NLB] SHENZHEN BAY PORT | 113.9458 | 22.50140 |
| MKT | Man Kam To | `hk_gtfs.zip` | `6701` | [KMB] MAN KAM TO (SAN UK LING) | 114.1317 | 22.53455 |
| HYW | Heung Yuen Wai | `hk_gtfs.zip` | `10000179` | [CTB] HEUNG YUEN WAI PORT/[KMB] HEUNG YUEN WAI CONTROL POINT | 114.1541 | 22.55202 |
