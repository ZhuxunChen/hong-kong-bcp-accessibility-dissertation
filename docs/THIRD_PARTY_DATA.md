# Third-Party Data and Attribution

The repository's code does not alter upstream data terms. Reusers must review the source terms before redistribution.

| Retained files | Provider/source | Terms or attribution |
|---|---|---|
| `data/hk_tpu_boundaries/TPU_SU_2021.*` | Hong Kong Planning Department via DATA.GOV.HK | DATA.GOV.HK Terms of Use v1.2; acknowledge the HKSAR Government and provider |
| `data/hk_census_stpug/STPUG_21C.xlsx` | Census and Statistics Department | DATA.GOV.HK Terms of Use v1.2 |
| `data/hk_gtfs/hk_gtfs.zip` | Transport Department | DATA.GOV.HK Terms of Use v1.2 |
| `data/hk_gtfs/hong-kong-260624.osm.pbf` | OpenStreetMap contributors; Geofabrik extract | ODbL 1.0; copyright OpenStreetMap contributors |
| `data/hk_gtfs/mtr_gtfs.zip` | Project-generated approximation from public station/service information | Included for academic reproducibility; not an official MTR timetable; upstream rights are not transferred |
| `analysis/meeting3_checks/inputs/shenzhen_context/440300.*` | POI86 Shenzhen district boundary snapshot | Contextual map background only; not used in routing or statistical analysis |

Government data: https://data.gov.hk/en/terms-and-conditions

OpenStreetMap: https://www.openstreetmap.org/copyright

The Stage 9A script `02_build_mtr_gtfs_bidirectional_v3.R` derives a structurally checked two-direction analytical feed from the frozen project-generated MTR input. Headways and running times are approximations documented in the dissertation; no MTR endorsement is claimed.
