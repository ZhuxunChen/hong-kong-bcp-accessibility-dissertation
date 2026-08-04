#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(sf)
  library(ggplot2)
  library(ggrepel)
})

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_path <- normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
root <- normalizePath(file.path(dirname(script_path), "..", "..", ".."), winslash = "/", mustWork = TRUE)
stage <- file.path(root, "analysis", "stage9a")
if (!dir.exists(file.path(stage, "inputs"))) {
  stage <- file.path(root, "reference_outputs", "stage9a")
}
results <- file.path(root, "analysis", "meeting3_checks", "results")
dir.create(results, recursive = TRUE, showWarnings = FALSE)

tpu <- st_read(file.path(stage, "inputs", "tpu_geography_v3.gpkg"), quiet = TRUE)
tpu <- st_transform(tpu, 4326)
shenzhen_path <- file.path(root, "analysis", "meeting3_checks", "inputs", "shenzhen_context", "440300.shp")
shenzhen <- st_read(shenzhen_path, quiet = TRUE)
# The source shapefile stores longitude/latitude coordinates but omits its CRS metadata.
st_crs(shenzhen) <- 4326
shenzhen <- st_make_valid(shenzhen)
bcps <- read.csv(file.path(stage, "inputs", "bcp_destination_provenance_v3.csv"), stringsAsFactors = FALSE)
bcp_sf <- st_as_sf(bcps, coords = c("lon", "lat"), crs = 4326, remove = FALSE)

places <- data.frame(
  label = c("Shenzhen", "New Territories", "Kowloon", "Hong Kong Island", "Lantau Island"),
  lon = c(114.09, 114.10, 114.18, 114.18, 113.96),
  lat = c(22.595, 22.425, 22.325, 22.265, 22.275)
)

base_theme <- theme_void(base_size = 9) +
  theme(
    plot.background = element_rect(fill = "white", colour = NA),
    panel.background = element_rect(fill = "#EAF3F7", colour = NA),
    plot.title = element_text(face = "bold", size = 10, hjust = 0),
    plot.subtitle = element_text(size = 7.5, colour = "#555555"),
    plot.margin = margin(5, 5, 5, 5),
    legend.position = "none"
  )

territory <- ggplot() +
  geom_sf(data = shenzhen, fill = "#E7E8E3", colour = "#A9AAA5", linewidth = 0.15) +
  geom_sf(data = tpu, fill = "#F2F1EC", colour = "#C8C8C8", linewidth = 0.10) +
  geom_sf(data = st_union(tpu), fill = NA, colour = "#555555", linewidth = 0.35) +
  geom_sf(data = bcp_sf, shape = 24, size = 2.2, fill = "#D55E00", colour = "white", stroke = 0.35) +
  geom_text(data = places, aes(lon, lat, label = label), colour = "#666666", size = 2.45, fontface = "italic") +
  coord_sf(xlim = c(113.82, 114.44), ylim = c(22.14, 22.63), expand = FALSE) +
  labs(title = "a  Territory-wide origin geography", subtitle = "Light land-water context with TPU boundaries") +
  base_theme

detail <- ggplot() +
  geom_sf(data = shenzhen, fill = "#E7E8E3", colour = "#A9AAA5", linewidth = 0.15) +
  geom_sf(data = tpu, fill = "#F2F1EC", colour = "#D0D0D0", linewidth = 0.08) +
  geom_sf(data = st_union(tpu), fill = NA, colour = "#555555", linewidth = 0.35) +
  geom_sf(data = bcp_sf, shape = 24, size = 2.4, fill = "#D55E00", colour = "white", stroke = 0.35) +
  geom_text_repel(
    data = bcps,
    aes(lon, lat, label = paste0(id, "  ", bcp_name)),
    size = 2.15, colour = "#222222", fontface = "bold",
    box.padding = 0.35, point.padding = 0.22, min.segment.length = 0,
    segment.colour = "#777777", segment.size = 0.25, seed = 20260804,
    max.overlaps = Inf
  ) +
  annotate("text", x = 114.08, y = 22.592, label = "Shenzhen", colour = "#666666", size = 2.6, fontface = "italic") +
  coord_sf(xlim = c(113.88, 114.36), ylim = c(22.36, 22.64), expand = FALSE) +
  labs(title = "b  Northern boundary gateways", subtitle = "Six operational passenger land BCPs") +
  base_theme

if (!requireNamespace("gridExtra", quietly = TRUE)) stop("The gridExtra R package is required")
combined <- gridExtra::arrangeGrob(
  territory, detail, ncol = 2, widths = c(1.15, 1)
)

ggsave(file.path(results, "figure_study_area_light_context.png"), combined, width = 9.0, height = 4.6, dpi = 400, bg = "white")
ggsave(file.path(results, "figure_study_area_light_context.pdf"), combined, width = 9.0, height = 4.6, device = "pdf", bg = "white")
cat("Saved enhanced study-area map in", results, "\n")
