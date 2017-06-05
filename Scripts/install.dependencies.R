#!/usr/bin/env Rscript

# install packages needed from CRAN
list.of.packages <- c("jsonlite", "signal")
new.packages <- list.of.packages[!(list.of.packages %in% installed.packages()[, "Package"])]
if (length(new.packages)) {
  print("installing : ")
  print(new.packages)
  install.packages(new.packages, repos = "http://cran.rstudio.com/")
  
  warning("If Maeswrap Package download fails, please refer to PEcAn documentation for download instructions")
}