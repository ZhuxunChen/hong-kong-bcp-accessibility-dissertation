# Stage 9A: rebuild stable TPU/STPUG origins and authoritative destinations.

suppressPackageStartupMessages({
  library(data.table)
  library(dplyr)
  library(readxl)
  library(sf)
})
sf_use_s2(FALSE)

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
base <- normalizePath(file.path(dirname(script_arg), "..", "..", ".."), mustWork = TRUE)
data_dir <- file.path(base, "数据")
out_dir <- file.path(base, "analysis", "stage9a", "inputs")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

outputs <- file.path(out_dir, c(
  "census_stpug_v3.csv",
  "stpug_tpu_crosswalk_v3.csv",
  "stpug_geography_v3.gpkg",
  "stpug_origins_v3.csv",
  "bcp_destination_provenance_v3.csv",
  "bcp_destinations_v3.csv",
  "input_preparation_audit_v3.md",
  "tpu_geography_v3.gpkg",
  "tpu_origins_v3.csv"
))
if (any(file.exists(outputs))) {
  stop("Refusing to overwrite existing Stage 9A inputs: ",
       paste(outputs[file.exists(outputs)], collapse = ", "))
}

parse_members <- function(code, label) {
  if (grepl("^[0-9]+$", code)) return(as.character(as.integer(code)))
  text <- gsub("\\s+", " ", trimws(label))
  text <- gsub("\\band\\b", ",", text, ignore.case = TRUE)
  parts <- trimws(unlist(strsplit(text, ",")))
  members <- unlist(lapply(parts, function(part) {
    numbers <- as.integer(unlist(regmatches(part, gregexpr("[0-9]+", part))))
    if (length(numbers) == 1) return(numbers)
    if (length(numbers) == 2 && grepl("-", part)) return(seq(numbers[1], numbers[2]))
    stop("Could not parse STPUG membership: ", code, " = ", label)
  }))
  as.character(members)
}

# Census workbook: row 5 contains machine-readable field names.
census_raw <- read_excel(
  file.path(data_dir, "HK_普查_STPUG", "STPUG_21C.xlsx"),
  sheet = "STPUG", skip = 4
)
census <- census_raw |>
  filter(!is.na(stpug), !is.na(t_pop), stpug != "9999") |>
  transmute(
    stpug_id = as.character(stpug),
    stpug_name_en = as.character(stpug_eng),
    stpug_name_zh = as.character(stpug_chi),
    population = as.numeric(t_pop),
    median_hh_income = as.numeric(ma_hh),
    median_emp_income = as.numeric(t_mmearn_xfdh),
    is_composite = grepl("S$", stpug_id)
  )

stopifnot(nrow(census) == 211L)
stopifnot(!anyDuplicated(census$stpug_id))
stopifnot(sum(census$is_composite) == 45L)
stopifnot(all(census$population > 0))

crosswalk <- bind_rows(lapply(seq_len(nrow(census)), function(i) {
  members <- parse_members(census$stpug_id[i], census$stpug_name_en[i])
  data.frame(
    stpug_id = census$stpug_id[i],
    stpug_name_en = census$stpug_name_en[i],
    is_composite = census$is_composite[i],
    group_size = length(members),
    tpu_id = members,
    stringsAsFactors = FALSE
  )
}))

tpu_raw <- st_read(
  file.path(data_dir, "HK_GIS边界", "TPU_SU_2021.shp"), quiet = TRUE
)
source_crs <- st_crs(tpu_raw)$input
tpu <- tpu_raw |>
  mutate(TPU = as.character(TPU)) |>
  st_transform(2326) |>
  st_make_valid() |>
  group_by(TPU) |>
  summarise(geometry = st_union(geometry), .groups = "drop")

stopifnot(nrow(tpu) == 292L)
stopifnot(nrow(crosswalk) == 292L)
stopifnot(!anyDuplicated(crosswalk$tpu_id))
stopifnot(setequal(crosswalk$tpu_id, tpu$TPU))

# Create deterministic metric-CRS representative points for all 292 TPUs.
tpu_centroids <- suppressWarnings(st_centroid(tpu))
tpu_inside <- lengths(st_within(tpu_centroids, tpu, sparse = TRUE)) > 0
tpu_representative <- tpu_centroids
tpu_representative$geometry[!tpu_inside] <- st_geometry(
  st_point_on_surface(tpu[!tpu_inside, ])
)
tpu_representative <- st_transform(tpu_representative, 4326)
tpu_coords <- st_coordinates(tpu_representative)
tpu_origins <- data.frame(
  id = tpu_representative$TPU,
  lon = tpu_coords[, 1],
  lat = tpu_coords[, 2]
)
stopifnot(nrow(tpu_origins) == 292L, !anyDuplicated(tpu_origins$id))
stopifnot(all(tpu_origins$lon > 113.8 & tpu_origins$lon < 114.5))
stopifnot(all(tpu_origins$lat > 22.1 & tpu_origins$lat < 22.7))

stpug_geo <- tpu |>
  left_join(crosswalk, by = c("TPU" = "tpu_id")) |>
  group_by(stpug_id, stpug_name_en, is_composite, group_size) |>
  summarise(geometry = st_union(geometry), .groups = "drop") |>
  left_join(census, by = c("stpug_id", "stpug_name_en", "is_composite")) |>
  mutate(
    area_km2 = as.numeric(st_area(geometry)) / 1e6,
    pop_density_km2 = population / area_km2
  )

stopifnot(nrow(stpug_geo) == 211L)
stopifnot(all(stpug_geo$area_km2 > 0))
stopifnot(!any(is.na(stpug_geo$median_hh_income)))

# Use the grouped polygon centroid; if a centroid falls outside a multipart
# polygon, replace it with a guaranteed on-surface representative point.
centroids <- suppressWarnings(st_centroid(stpug_geo))
inside <- lengths(st_within(centroids, stpug_geo, sparse = TRUE)) > 0
representative <- centroids
representative$geometry[!inside] <- st_geometry(st_point_on_surface(stpug_geo[!inside, ]))
representative <- st_transform(representative, 4326)
coords <- st_coordinates(representative)
origins <- data.frame(
  id = representative$stpug_id,
  lon = coords[, 1],
  lat = coords[, 2]
)
stopifnot(nrow(origins) == 211L, !anyDuplicated(origins$id))

# Anchor destinations to stops contained in the exact feeds used by r5r.
read_gtfs_stops <- function(zip_path) {
  read.csv(unz(zip_path, "stops.txt"), stringsAsFactors = FALSE,
           fileEncoding = "UTF-8-BOM", check.names = FALSE)
}
hk_stops <- read_gtfs_stops(file.path(data_dir, "HK_GTFS", "hk_gtfs.zip"))
mtr_stops <- read_gtfs_stops(file.path(data_dir, "HK_GTFS", "mtr_gtfs.zip"))

bcp_spec <- data.frame(
  id = c("LW", "LMC", "HG", "SB", "MKT", "HYW"),
  bcp_name = c(
    "Lo Wu", "Lok Ma Chau Spur Line", "Lok Ma Chau",
    "Shenzhen Bay Port", "Man Kam To", "Heung Yuen Wai"
  ),
  source_feed = c("mtr_gtfs.zip", "mtr_gtfs.zip", rep("hk_gtfs.zip", 4)),
  source_stop_id = c("MTR_LOW", "MTR_LMC", "10000339", "12728", "6701", "10000179"),
  stringsAsFactors = FALSE
)

extract_stop <- function(i) {
  feed <- if (bcp_spec$source_feed[i] == "mtr_gtfs.zip") mtr_stops else hk_stops
  row <- feed[as.character(feed$stop_id) == bcp_spec$source_stop_id[i], ]
  if (nrow(row) != 1L) stop("Expected exactly one GTFS stop for ", bcp_spec$id[i])
  data.frame(
    id = bcp_spec$id[i],
    bcp_name = bcp_spec$bcp_name[i],
    source_feed = bcp_spec$source_feed[i],
    source_stop_id = bcp_spec$source_stop_id[i],
    source_stop_name = row$stop_name,
    lon = as.numeric(row$stop_lon),
    lat = as.numeric(row$stop_lat),
    stringsAsFactors = FALSE
  )
}
bcp_provenance <- bind_rows(lapply(seq_len(nrow(bcp_spec)), extract_stop))
stopifnot(nrow(bcp_provenance) == 6L, !anyDuplicated(bcp_provenance$id))
stopifnot(all(bcp_provenance$lon > 113.8 & bcp_provenance$lon < 114.3))
stopifnot(all(bcp_provenance$lat > 22.4 & bcp_provenance$lat < 22.7))

write.csv(st_drop_geometry(stpug_geo), outputs[1], row.names = FALSE, na = "")
write.csv(crosswalk, outputs[2], row.names = FALSE, na = "")
st_write(stpug_geo, outputs[3], layer = "stpug_2021", quiet = TRUE)
write.csv(origins, outputs[4], row.names = FALSE, na = "")
write.csv(bcp_provenance, outputs[5], row.names = FALSE, na = "")
write.csv(bcp_provenance[, c("id", "lon", "lat")], outputs[6], row.names = FALSE, na = "")
st_write(tpu, outputs[8], layer = "tpu_2021", quiet = TRUE)
write.csv(tpu_origins, outputs[9], row.names = FALSE, na = "")

audit <- c(
  "# Stage 9A Input Preparation Audit",
  "",
  paste0("- Source TPU CRS: `", source_crs, "`."),
  "- Area calculations use Hong Kong 1980 Grid (EPSG:2326) in metres.",
  paste0("- Census analytical rows: ", nrow(census), "."),
  paste0("- Single-unit STPUGs: ", sum(!census$is_composite), "."),
  paste0("- Composite STPUGs: ", sum(census$is_composite), "."),
  paste0("- Crosswalk TPU members: ", nrow(crosswalk), "/292, each assigned exactly once."),
  paste0("- Rebuilt STPUG geometries and routing origins: ", nrow(stpug_geo), "."),
  paste0("- Rebuilt TPU geometries and routing origins: ", nrow(tpu), "."),
  paste0("- TPU centroids replaced by on-surface points where needed: ", sum(!tpu_inside), "."),
  paste0("- STPUG centroids replaced by on-surface points where needed: ", sum(!inside), "."),
  "- Census attributes are read directly from the retained 2021 STPUG workbook; no legacy cleaned table is required.",
  "- Six routing destinations are sourced by stop ID from the exact GTFS ZIP files.",
  "- Sha Tau Kok is not included in the rebuilt main destination set.",
  "",
  "## Destination provenance",
  "",
  "| ID | BCP | Feed | Stop ID | Stop name | Longitude | Latitude |",
  "|---|---|---|---|---|---:|---:|",
  apply(bcp_provenance, 1, function(x) paste0(
    "| ", x[["id"]], " | ", x[["bcp_name"]], " | `", x[["source_feed"]],
    "` | `", x[["source_stop_id"]], "` | ", gsub("\\|", "/", x[["source_stop_name"]]),
    " | ", x[["lon"]], " | ", x[["lat"]], " |"
  ))
)
writeLines(audit, outputs[7], useBytes = TRUE)

cat("Prepared 292 TPU origins, 211 STPUG origins and six GTFS-anchored BCPs.\n")
