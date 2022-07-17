import json
import logging
import ctypes
from os import path, makedirs
from datetime import datetime

import numpy as np
from matplotlib import pyplot as plt
from GPSPhoto import gpsphoto

class PostHandlers():

    def pixhawk_v2(self, inst_data_path, data):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []

        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]
            lat = x[1]["Global Location"]["lat"]
            lon = x[1]["Global Location"]["lon"]
            output["coords"].append((lon, lat))
            output["timestamps"].append(x[0])

        return output

    def pi_gps_ublox(self, inst_data_path, data):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []
        output["alts"] = []

        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]
            lat = x[1]["Global Location"]["lat"]
            try:
                lon = x[1]["Global Location"]["lon"]
            except KeyError:
                lon = x[1]["Global Location"]["long"]
            alt = x[1]["Global Location"]["alt"]
            output["coords"].append((lon, lat))
            output["timestamps"].append(x[0])
            output["alts"].append(alt)
        return output

    def USB2000pair(self, inst_data_path, data):
        print("Specs!")
        pass

    def gphoto2_cam(self, inst_data_path, data):
        logging.info("\t\tGenerating RGB previews...")

        #get locations
        locations = {}
        for i_name, inst in data.items():
            try:
                locations["timestamps"] = inst["timestamps"]
                locations["coords"] = inst["coords"]
                locations["alts"] = inst["alts"]
                logging.info("Using location data from %s" % i_name)
                break
            except (KeyError, TypeError):
                continue

        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)

        for recNum, rec in data["Data"].items():
            #Get filename
            out_path = path.normpath(path.join(path.split(inst_data_path)[0], "Canon", "prev_" + path.split(rec[1])[1]))

            #Prep GPS data
            try:
                photo = gpsphoto.GPSPhoto(out_path)
                coords = [float(f) for f in locations["coords"][int(recNum)]]
                coords.reverse()
                dt = datetime.fromtimestamp(locations["timestamps"][int(recNum)])
                alt_vals = float(locations["alts"][int(recNum)])
                gps_meta = gpsphoto.GPSInfo(coords, timeStamp=dt)
                gps_meta.setAlt(alt_vals)
                photo.modGPSData(gps_meta, out_path)
            except KeyError:
                logging.warning("No location data for record %s, EXIF not updated." % recNum)


    def ici_thermal(self, inst_data_path, data):
        logging.info("\t\tGenerating thermal previews...")

        #get locations
        locations = {}
        for i_name, inst in data.items():
            try:
                locations["timestamps"] = inst["timestamps"]
                locations["coords"] = inst["coords"]
                locations["alts"] = inst["alts"]
                logging.info("Using location data from %s" % i_name)
                break
            except (KeyError, TypeError):
                continue

        #Create previews
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)

        im_height = data["Header"]["Height"]
        im_width = data["Header"]["Width"]
        im_size = data["Header"]["Size"]

        imgbuf = np.zeros((im_height, im_width), np.float)
        datbuf = (ctypes.c_float * im_size)()   

        for recNum, rec in data["Data"].items():
            #Get filename
            imgFile = path.normpath(path.join(path.split(inst_data_path)[0], "Thermal", path.split(rec[1])[1]))

            #Load binary
            with open(imgFile, 'rb') as in_file:
                in_file.readinto(datbuf)
                
            #Save File
            imgbuf = np.reshape(datbuf, (im_height, im_width))
            makedirs(path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal")), exist_ok=True)
            out_path = path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal", path.split(rec[1])[1]))[:-3] + "jpg"
            plt.imsave(out_path, imgbuf, cmap='inferno', vmin=0, vmax=45)

            #Prep GPS data
            try:
                photo = gpsphoto.GPSPhoto(out_path)
                coords = [float(f) for f in locations["coords"][int(recNum)]]
                coords.reverse()
                dt = datetime.fromtimestamp(locations["timestamps"][int(recNum)])
                alt_vals = float(locations["alts"][int(recNum)])
                gps_meta = gpsphoto.GPSInfo(coords, timeStamp=dt)
                gps_meta.setAlt(alt_vals)
                photo.modGPSData(gps_meta, out_path)
            except KeyError:
                logging.warning("No location data for record %s, EXIF not updated." % recNum)

