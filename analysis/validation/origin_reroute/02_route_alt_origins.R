# Origin-sensitivity re-route: routes UNWEIGHTED within-TPU alternative origins
# with parameters identical to Stage 9A 04_route_repeated_v3.R.
# Writes ONLY to analysis/stage9a/alt_origin_runs/. Does not touch frozen runs/results.
options(java.parameters = "-Xmx6G")
suppressPackageStartupMessages({library(data.table); library(r5r)})
args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
base <- normalizePath(file.path(dirname(script_arg), "..", "..", ".."), mustWork = TRUE)
if (!dir.exists(file.path(base,"analysis","stage9a","network"))) {
  base <- normalizePath(Sys.getenv("PROJECT_ROOT", unset="."), mustWork=TRUE)
}
input_dir   <- file.path(base,"analysis","stage9a","inputs")
network_dir <- file.path(base,"analysis","stage9a","network")
runs_dir    <- file.path(base,"analysis","stage9a","alt_origin_runs")
alt_input_dir <- file.path(runs_dir,"inputs")
dir.create(runs_dir, recursive=TRUE, showWarnings=FALSE)
reps <- as.integer(Sys.getenv("STAGE9A_REPS", unset="5"))
stopifnot(!is.na(reps), reps >= 1L, reps <= 5L)
origin_meta <- fread(file.path(alt_input_dir,"tpu_alt_origins_v3.csv"))
origins <- origin_meta[, .(id,lon,lat)]
destinations <- fread(file.path(input_dir,"bcp_destinations_v3.csv"))
stopifnot(nrow(destinations)==6L)
departure <- as.POSIXct("2026-06-29 08:00:00", tz="Asia/Hong_Kong", format="%Y-%m-%d %H:%M:%S")
network <- setup_r5(data_path=network_dir, verbose=FALSE)
on.exit(try(stop_r5(network), silent=TRUE), add=TRUE)
prior_dir <- file.path(runs_dir,"attempt_01_without_frozen_centroid")
prior_files <- file.path(prior_dir, sprintf("run_%02d",seq_len(reps)), "travel_time_matrix_alt_v3.csv")
reuse_prior <- reps==5L && all(file.exists(prior_files))
route_origins <- if (reuse_prior) origin_meta[origin_type=="frozen_centroid",.(id,lon,lat)] else origins
if (reuse_prior) {
  cat("Reusing five completed alternative-point matrices and routing only",
      nrow(route_origins), "frozen centroids.\n")
} else {
  cat("No reusable alternative-point matrices found; routing all",
      nrow(route_origins), "origins.\n")
}
for (i in seq_len(reps)) {
  rd <- file.path(runs_dir, sprintf("run_%02d", i)); dir.create(rd, showWarnings=FALSE)
  out <- file.path(rd, "travel_time_matrix_alt_v3.csv")
  if (file.exists(out)) { cat("skip", rd, "\n"); next }
  cat("=== alt run", i, "of", reps, ":", nrow(route_origins), "new origins x 6 BCPs ===\n")
  m <- travel_time_matrix(r5r_network=network, origins=route_origins, destinations=destinations,
        mode=c("WALK","TRANSIT"), departure_datetime=departure, max_trip_duration=120L,
        max_walk_time=20L, time_window=30L, percentiles=c(25,50,75), draws_per_minute=5L, verbose=FALSE)
  if (reuse_prior) {
    component <- file.path(rd,"travel_time_matrix_centroid_component_v3.csv")
    fwrite(m, component)
    prior <- fread(prior_files[i])
    combined <- rbindlist(list(prior,m),use.names=TRUE,fill=TRUE)
    stopifnot(!anyDuplicated(combined[,.(from_id,to_id)]))
    fwrite(combined,out)
    cat("wrote", nrow(m), "centroid rows and", nrow(combined), "combined rows to", rd, "\n")
  } else {
    fwrite(m, out)
    cat("wrote", nrow(m), "rows to", out, "\n")
  }
}
stop_r5(network); cat("Alt-origin routing complete.\n")
