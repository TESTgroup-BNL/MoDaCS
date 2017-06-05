####################################################################################################
#
#
#     Authors: Shawn Serbin. Last updated 2017.06.05 by <sserbin@bnl.gov>
####################################################################################################


#---------------- Close all devices and delete all variables. -------------------------------------#
# reset environment
rm(list=ls(all=TRUE))   # clear workspace
graphics.off()          # close any open graphics
closeAllConnections()   # close any open connections to files
#--------------------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------------------#
## Load libs
library(jsonlite)
library(signal)
#--------------------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------------------#
## Load json data file
json_data_files <- '~/Data/GitHub/MoDaCS/Scripts/example_data/2017-05-16_193712_USB2000+_Pair_data.json'
json_data <- fromJSON(txt=json_data_files, flatten=TRUE)
str(json_data)
#--------------------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------------------#
## Parse
wavelengths <-json_data$Header$Downward$Wavelengths
all.refl <- json_data$Data[[3]][[3]]$Reflectance
all.refl.smooth <- sgolayfilt(x=all.refl,p=1,n=5)

plot(wavelengths,all.refl,type="l",xlim=c(415,900),ylim=c(0,1),ylab="Reflectance (-)",
     xlab="Wavelength (nm)",col="grey70")
lines(wavelengths,all.refl.smooth)
box(lwd=2.2)
#--------------------------------------------------------------------------------------------------#


#--------------------------------------------------------------------------------------------------#
### EOF