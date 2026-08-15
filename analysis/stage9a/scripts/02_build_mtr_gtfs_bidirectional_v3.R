# Stage 9A: derive a bidirectional MTR GTFS from the frozen v19 feed.

suppressPackageStartupMessages(library(data.table))

args <- commandArgs(trailingOnly = FALSE)
script_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
base <- normalizePath(file.path(dirname(script_arg), "..", "..", ".."), mustWork = TRUE)
source_dir <- file.path(base, "data", "hk_gtfs")
source_zip <- file.path(source_dir, "mtr_gtfs.zip")
network_dir <- file.path(base, "analysis", "stage9a", "network")
build_dir <- file.path(network_dir, "mtr_gtfs_bidirectional_v3")
output_zip <- file.path(network_dir, "mtr_gtfs_bidirectional_v3.zip")
audit_csv <- file.path(network_dir, "mtr_route_direction_audit_v3.csv")

dir.create(network_dir, recursive = TRUE, showWarnings = FALSE)
if (any(file.exists(c(output_zip, audit_csv))) || dir.exists(build_dir)) {
  stop("Refusing to overwrite existing Stage 9A MTR GTFS outputs.")
}
dir.create(build_dir, recursive = TRUE)

read_gtfs <- function(name) {
  as.data.table(read.csv(
    unz(source_zip, name), stringsAsFactors = FALSE,
    fileEncoding = "UTF-8-BOM", check.names = FALSE
  ))
}

agency <- read_gtfs("agency.txt")
calendar <- read_gtfs("calendar.txt")
routes <- read_gtfs("routes.txt")
stops <- read_gtfs("stops.txt")
trips <- read_gtfs("trips.txt")
stop_times <- read_gtfs("stop_times.txt")

stopifnot(nrow(routes) == 9L)
stopifnot(setequal(unique(trips$direction_id), 0L))
stopifnot(!anyDuplicated(trips$trip_id))
stopifnot(!anyDuplicated(stops$stop_id))

time_to_seconds <- function(x) {
  pieces <- tstrsplit(as.character(x), ":", fixed = TRUE)
  as.integer(pieces[[1]]) * 3600L + as.integer(pieces[[2]]) * 60L + as.integer(pieces[[3]])
}

seconds_to_time <- function(x) {
  sprintf("%02d:%02d:%02d", x %/% 3600L, (x %% 3600L) %/% 60L, x %% 60L)
}

reverse_trip <- function(trip_id) {
  target_id <- trip_id
  rows <- stop_times[stop_times$trip_id == target_id][order(stop_sequence)]
  if (nrow(rows) < 2L) stop("Trip has fewer than two stops: ", trip_id)
  arrivals <- time_to_seconds(rows$arrival_time)
  departures <- time_to_seconds(rows$departure_time)
  if (any(diff(arrivals) < 0L) || any(departures < arrivals)) {
    stop("Non-monotonic source stop times: ", trip_id)
  }
  segment_seconds <- diff(arrivals)
  reverse_offsets <- c(0L, cumsum(rev(segment_seconds)))
  reverse_arrivals <- arrivals[1] + reverse_offsets
  data.table(
    trip_id = paste0(trip_id, "_R"),
    arrival_time = seconds_to_time(reverse_arrivals),
    departure_time = seconds_to_time(reverse_arrivals),
    stop_id = rev(rows$stop_id),
    stop_sequence = seq_len(nrow(rows))
  )
}

reverse_times <- rbindlist(lapply(trips$trip_id, reverse_trip), use.names = TRUE)
reverse_trips <- copy(trips)
reverse_trips[, trip_id := paste0(trip_id, "_R")]
reverse_trips[, direction_id := 1L]

all_trips <- rbindlist(list(trips, reverse_trips), use.names = TRUE)
all_stop_times <- rbindlist(list(stop_times, reverse_times), use.names = TRUE)
setorder(all_trips, route_id, service_id, direction_id, trip_id)
setorder(all_stop_times, trip_id, stop_sequence)

stopifnot(!anyDuplicated(all_trips$trip_id))
stopifnot(setequal(unique(all_trips$direction_id), c(0L, 1L)))
stopifnot(setequal(all_trips$trip_id, unique(all_stop_times$trip_id)))

direction_audit <- all_trips[, .(
  trip_count = .N,
  direction_count = uniqueN(direction_id),
  direction_ids = paste(sort(unique(direction_id)), collapse = ",")
), by = route_id][order(route_id)]
stopifnot(nrow(direction_audit) == nrow(routes))
stopifnot(all(direction_audit$direction_count == 2L))

fwrite(agency, file.path(build_dir, "agency.txt"))
fwrite(calendar, file.path(build_dir, "calendar.txt"))
fwrite(routes, file.path(build_dir, "routes.txt"))
fwrite(stops, file.path(build_dir, "stops.txt"))
fwrite(all_trips, file.path(build_dir, "trips.txt"))
fwrite(all_stop_times, file.path(build_dir, "stop_times.txt"))
fwrite(direction_audit, audit_csv)

old_wd <- getwd()
setwd(build_dir)
on.exit(setwd(old_wd), add = TRUE)
utils::zip(
  zipfile = output_zip,
  files = c("agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt"),
  flags = "-q"
)
setwd(old_wd)

for (name in c("hk_gtfs.zip", "hong-kong-260624.osm.pbf")) {
  destination <- file.path(network_dir, name)
  if (!file.exists(destination)) {
    copied <- file.copy(file.path(source_dir, name), destination, overwrite = FALSE)
    if (!copied) stop("Could not copy network input: ", name)
  }
}

cat("Built bidirectional MTR GTFS:\n", output_zip, "\n")
cat("Trips:", nrow(trips), "forward +", nrow(reverse_trips), "reverse =", nrow(all_trips), "\n")
print(direction_audit)
