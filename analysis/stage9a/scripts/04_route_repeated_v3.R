# Stage 9A: repeated routing on the bidirectional MTR network.

options(java.parameters = "-Xmx6G")
suppressPackageStartupMessages({
  library(data.table)
  library(r5r)
})

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
base <- normalizePath(file.path(dirname(script_arg), "..", "..", ".."), mustWork = TRUE)
input_dir <- file.path(base, "analysis", "stage9a", "inputs")
network_dir <- file.path(base, "analysis", "stage9a", "network")
runs_dir <- file.path(base, "analysis", "stage9a", "runs")
dir.create(runs_dir, recursive = TRUE, showWarnings = FALSE)

repetitions <- as.integer(Sys.getenv("STAGE9A_REPS", unset = "5"))
if (is.na(repetitions) || repetitions < 1L) stop("STAGE9A_REPS must be a positive integer")

tpu_origins <- fread(file.path(input_dir, "tpu_origins_v3.csv"))
stpug_origins <- fread(file.path(input_dir, "stpug_origins_v3.csv"))
destinations <- fread(file.path(input_dir, "bcp_destinations_v3.csv"))
stopifnot(nrow(tpu_origins) == 292L, !anyDuplicated(tpu_origins$id))
stopifnot(nrow(stpug_origins) == 211L, !anyDuplicated(stpug_origins$id))
stopifnot(nrow(destinations) == 6L, !anyDuplicated(destinations$id))

departure <- as.POSIXct(
  "2026-06-29 08:00:00", tz = "Asia/Hong_Kong",
  format = "%Y-%m-%d %H:%M:%S"
)

route_matrix <- function(network, origins, label) {
  cat("Routing ", label, ": ", nrow(origins), " origins x 6 BCPs\n", sep = "")
  travel_time_matrix(
    r5r_network = network,
    origins = origins,
    destinations = destinations,
    mode = c("WALK", "TRANSIT"),
    departure_datetime = departure,
    max_trip_duration = 120L,
    max_walk_time = 20L,
    time_window = 30L,
    percentiles = c(25, 50, 75),
    draws_per_minute = 5L,
    verbose = FALSE
  )
}

network <- setup_r5(data_path = network_dir, verbose = FALSE)
on.exit(try(stop_r5(network), silent = TRUE), add = TRUE)

for (iteration in seq_len(repetitions)) {
  run_id <- sprintf("run_%02d", iteration)
  run_dir <- file.path(runs_dir, run_id)
  dir.create(run_dir, recursive = TRUE, showWarnings = FALSE)
  tpu_path <- file.path(run_dir, "travel_time_matrix_tpu_v3.csv")
  stpug_path <- file.path(run_dir, "travel_time_matrix_stpug_v3.csv")
  log_path <- file.path(run_dir, "routing_run_v3.txt")
  outputs <- c(tpu_path, stpug_path, log_path)

  if (all(file.exists(outputs))) {
    cat("Skipping complete ", run_id, "\n", sep = "")
    next
  }
  if (any(file.exists(outputs))) {
    stop("Refusing to overwrite partial outputs in ", run_dir)
  }

  started <- Sys.time()
  cat("\n=== ", run_id, " of ", repetitions, " ===\n", sep = "")
  tpu_matrix <- route_matrix(network, tpu_origins, "TPU")
  stpug_matrix <- route_matrix(network, stpug_origins, "STPUG")
  fwrite(tpu_matrix, tpu_path)
  fwrite(stpug_matrix, stpug_path)

  log_lines <- c(
    paste0("Stage 9A routing repetition: ", run_id),
    paste0("Started: ", format(started, tz = "Europe/London", usetz = TRUE)),
    paste0("Finished: ", format(Sys.time(), tz = "Europe/London", usetz = TRUE)),
    "Network: bidirectional MTR GTFS v3 + frozen Hong Kong GTFS + frozen OSM PBF",
    "Departure: 2026-06-29 08:00:00 Asia/Hong_Kong (Monday)",
    "Modes: WALK + TRANSIT",
    "Time window: 30 minutes; draws_per_minute: 5",
    "Percentiles: 25, 50, 75",
    "Maximum trip duration: 120 minutes; maximum walking time: 20 minutes",
    paste0("Destinations: ", paste(destinations$id, collapse = ", ")),
    paste0("TPU origins requested: ", nrow(tpu_origins)),
    paste0("TPU origins returned: ", uniqueN(tpu_matrix$from_id)),
    paste0("TPU OD rows returned: ", nrow(tpu_matrix)),
    paste0("STPUG origins requested: ", nrow(stpug_origins)),
    paste0("STPUG origins returned: ", uniqueN(stpug_matrix$from_id)),
    paste0("STPUG OD rows returned: ", nrow(stpug_matrix))
  )
  writeLines(log_lines, log_path)
  cat(paste(log_lines, collapse = "\n"), "\n")
}

stop_r5(network)
cat("Completed ", repetitions, " Stage 9A routing repetitions.\n", sep = "")

