#!/usr/bin/env Rscript

args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_path <- normalizePath(sub("^--file=", "", file_arg[1]), winslash = "/", mustWork = TRUE)
results_dir <- normalizePath(file.path(dirname(script_path), "..", "results"), winslash = "/", mustWork = TRUE)

data <- read.csv(file.path(results_dir, "minimal_distance_benchmark_tpu.csv"))
png_path <- file.path(results_dir, "figure_minimal_distance_benchmark.png")
pdf_path <- file.path(results_dir, "figure_minimal_distance_benchmark.pdf")

draw_figure <- function() {
  old <- par(no.readonly = TRUE)
  on.exit(par(old))
  par(mfrow = c(1, 2), mar = c(4.3, 4.4, 2.5, 1), oma = c(0, 0, 2, 0), family = "sans")
  x <- data$fixed_20kph_time
  y <- data$min_tt
  lim <- c(0, max(c(x, y), na.rm = TRUE) * 1.03)
  plot(x, y, xlim = lim, ylim = lim, pch = 16, cex = 0.65,
       col = grDevices::adjustcolor("#2A788E", alpha.f = 0.70),
       xlab = "Distance-only time (minutes)",
       ylab = "R5 minimum time (minutes)", main = "a  Distance-only benchmark", cex.main = 0.88)
  abline(0, 1, col = "#B23A48", lty = 2, lwd = 1.3)
  rho <- cor(data$nearest_straight_km, y, method = "spearman")
  mae <- mean(abs(y - x))
  legend("topleft", legend = sprintf("Spearman rho = %.2f\nMAE = %.1f min", rho, mae),
         bty = "n", cex = 0.82)

  hist(data$calibrated_residual, breaks = 18, col = "#7B6D8D", border = "white",
       xlab = "R5 minus distance-only time (minutes)", ylab = "TPUs",
       main = "b  Network-model error", cex.main = 0.88)
  abline(v = 0, col = "#B23A48", lty = 2, lwd = 1.3)
  mtext("Full-network travel time versus a fixed-speed distance model", outer = TRUE, cex = 1.05)
}

png(png_path, width = 2160, height = 960, res = 300)
draw_figure()
dev.off()
pdf(pdf_path, width = 7.2, height = 3.2, useDingbats = FALSE)
draw_figure()
dev.off()

cat("Saved", png_path, "and", pdf_path, "\n")
