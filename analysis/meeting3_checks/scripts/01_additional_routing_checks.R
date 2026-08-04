#!/usr/bin/env Rscript
# Meeting 3 additions: extended Monte Carlo checks and West Kowloon HSR scenario.

options(java.parameters = "-Xmx6G")
suppressPackageStartupMessages(library(r5r))

script_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
script_path <- normalizePath(sub("^--file=", "", script_arg), mustWork = TRUE)
root <- normalizePath(file.path(dirname(script_path), "..", "..", ".."), mustWork = TRUE)
stage <- file.path(root, "analysis", "stage9a")
if (!dir.exists(file.path(stage, "inputs"))) {
  stage <- file.path(root, "reference_outputs", "stage9a")
}
out_dir <- file.path(root, "analysis", "meeting3_checks", "results")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

origins <- read.csv(file.path(stage, "inputs", "tpu_origins_v3.csv"), stringsAsFactors = FALSE)
origins$id <- as.character(origins$id)
destinations <- read.csv(file.path(stage, "inputs", "bcp_destinations_v3.csv"), stringsAsFactors = FALSE)
destinations$id <- as.character(destinations$id)

# Stable origins span the frozen min-time distribution; 158 and 310 are snapped
# but had no stable route in the main run. TPU 622 is the Lo Wu-adjacent case.
sample_ids <- c("627", "728", "284", "421", "838", "835", "971", "622", "158", "310")
sample_origins <- origins[origins$id %in% sample_ids, ]
stopifnot(nrow(sample_origins) == length(sample_ids))

# Anchor West Kowloon to the official-feed HSR bus terminus stop (stop_id 13341).
west_kowloon <- data.frame(id = "WKS", lon = 114.16446, lat = 22.30684)
departure <- as.POSIXct(
  "2026-06-29 08:00:00", tz = "Asia/Hong_Kong",
  format = "%Y-%m-%d %H:%M:%S"
)

route_once <- function(network, from, to) {
  travel_time_matrix(
    r5r_network = network,
    origins = from,
    destinations = to,
    mode = c("WALK", "TRANSIT"),
    departure_datetime = departure,
    max_trip_duration = 120L,
    max_walk_time = 20L,
    time_window = 30L,
    percentiles = c(25, 50, 75),
    draws_per_minute = 5L,
    verbose = FALSE,
    progress = FALSE
  )
}

network <- setup_r5(file.path(stage, "network"), verbose = FALSE)
on.exit(try(stop_r5(network), silent = TRUE), add = TRUE)

extended <- vector("list", 30L)
for (run in seq_len(30L)) {
  cat("Representative-OD run", run, "of 30\n")
  x <- route_once(network, sample_origins, destinations)
  x$run <- run
  extended[[run]] <- x
}
extended <- do.call(rbind, extended)
write.csv(
  extended,
  file.path(out_dir, "representative_od_30_runs_raw.csv"),
  row.names = FALSE,
  na = ""
)

hsr <- vector("list", 5L)
for (run in seq_len(5L)) {
  cat("West Kowloon run", run, "of 5\n")
  x <- route_once(network, origins, west_kowloon)
  x$run <- run
  hsr[[run]] <- x
}
hsr <- do.call(rbind, hsr)
write.csv(
  hsr,
  file.path(out_dir, "west_kowloon_5_runs_raw.csv"),
  row.names = FALSE,
  na = ""
)

writeLines(
  c(
    "Meeting 3 additional routing checks",
    "Departure: 2026-06-29 08:00 Asia/Hong_Kong",
    "Modes: WALK + TRANSIT; time window: 30 minutes; max walk: 20 minutes",
    "Representative sample: 10 TPU origins x 6 BCPs x 30 independent calls",
    "HSR scenario: 292 TPU origins x West Kowloon stop 13341 x 5 independent calls"
  ),
  file.path(out_dir, "additional_routing_checks_readme.txt")
)

cat("Additional routing outputs saved in", out_dir, "\n")
