# Stage 9A: classify omitted origins using R5 network snapping evidence.

options(java.parameters = "-Xmx4G")
suppressPackageStartupMessages({
  library(data.table)
  library(r5r)
})

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
base <- normalizePath(file.path(dirname(script_arg), "..", "..", ".."), mustWork = TRUE)
input_dir <- file.path(base, "analysis", "stage9a", "inputs")
network_dir <- file.path(base, "analysis", "stage9a", "network")
result_dir <- file.path(base, "analysis", "stage9a", "results")

network <- setup_r5(data_path = network_dir, verbose = FALSE)
on.exit(try(stop_r5(network), silent = TRUE), add = TRUE)

audit_grain <- function(grain, origin_file, stable_matrix_file) {
  origins <- fread(file.path(input_dir, origin_file))
  origins[, id := as.character(id)]
  stable <- fread(file.path(result_dir, stable_matrix_file))
  stable_ids <- unique(as.character(stable$from_id[!is.na(stable$travel_time_p50)]))

  snap_1600 <- find_snap(network, points = origins, radius = 1600, mode = "WALK")
  snap_1600 <- as.data.table(snap_1600)
  setnames(snap_1600, "point_id", "id")
  snap_1600[, id := as.character(id)]
  setnames(
    snap_1600,
    old = setdiff(names(snap_1600), c("id", "lon", "lat")),
    new = paste0(setdiff(names(snap_1600), c("id", "lon", "lat")), "_1600")
  )

  snap_5000 <- find_snap(network, points = origins, radius = 5000, mode = "WALK")
  snap_5000 <- as.data.table(snap_5000)
  setnames(snap_5000, "point_id", "id")
  snap_5000[, id := as.character(id)]
  setnames(
    snap_5000,
    old = setdiff(names(snap_5000), c("id", "lon", "lat")),
    new = paste0(setdiff(names(snap_5000), c("id", "lon", "lat")), "_5000")
  )

  audit <- merge(origins, snap_1600, by = c("id", "lon", "lat"), all.x = TRUE)
  audit <- merge(audit, snap_5000, by = c("id", "lon", "lat"), all.x = TRUE)
  audit[, stable_route := id %in% stable_ids]
  audit[, classification := fifelse(
    stable_route,
    "stable_route",
    fifelse(
      found_1600 %in% TRUE,
      "snapped_but_no_stable_p50_route_within_120min",
      fifelse(found_5000 %in% TRUE, "requires_snap_radius_over_1600m", "not_snapped_within_5000m")
    )
  )]
  setorder(audit, classification, id)
  fwrite(audit, file.path(result_dir, paste0("omitted_origin_audit_", grain, "_v3.csv")))
  counts <- audit[, .N, by = classification][order(classification)]
  counts[, grain := grain]
  counts[, total_origins := nrow(audit)]
  counts[, share := N / total_origins]
  counts
}

tpu_counts <- audit_grain(
  "tpu", "tpu_origins_v3.csv", "travel_time_matrix_tpu_v3.csv"
)
stpug_counts <- audit_grain(
  "stpug", "stpug_origins_v3.csv", "travel_time_matrix_stpug_v3.csv"
)
summary <- rbindlist(list(tpu_counts, stpug_counts), use.names = TRUE)
fwrite(summary, file.path(result_dir, "omitted_origin_audit_summary_v3.csv"))

stop_r5(network)
print(summary)
