from glob import glob
import json
import logging
import ctypes
import subprocess
import os
from os import path, makedirs
from datetime import datetime, timezone

import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from PIL import Image
import tifffile

import post_processing.gpsphoto as gpsphoto
import post_processing.kml as kml


class PostHandlers():

    def __init__(self, config={}):
        self.config = config
        self.post_log = logging.getLogger("Post_Processing")
        self.locations = {"source":""}
        self.cam_attitudes = {"source":""}

    def get_locations(self, data, preferred_source="", no_cache=False):      
        try:
            if preferred_source == "":
                preferred_source=self.config["preferred_location_source"]
        except KeyError:
            self.post_log.warning("No preferred location data specified")

        if preferred_source in data and (not (preferred_source == self.locations["source"])):
            no_cache = True #Force refresh if the preferred source becomes available

        if (self.locations["source"] == "") or (no_cache == True):
            if preferred_source in data:
                self.locations["timestamps"] = data[preferred_source]["timestamps"]
                self.locations["coords"] = data[preferred_source]["coords"]
                self.locations["alt"] = data[preferred_source]["alt"]
                self.locations["yaw"] = data[preferred_source]["yaw"]
                self.locations["recNum"] = data[preferred_source]["recNum"]
                self.post_log.info("Using location data from %s" % preferred_source)
            else:
                for i_name, inst in data.items():
                    try:
                        self.locations["timestamps"] = inst["timestamps"]
                        self.locations["coords"] = inst["coords"]
                        self.locations["alt"] = inst["alt"]
                        self.locations["yaw"] = inst["yaw"]
                        self.locations["recNum"] = inst["recNum"]
                        self.locations["source"] = i_name
                        self.post_log.info("Using location data from %s" % i_name)
                        break
                    except (KeyError, TypeError):
                        continue
        else:
            self.post_log.info("Using cached location data from %s" % self.locations["source"])
        return self.locations

    def get_cam_attitude(self, data, preferred_source="", no_cache=False):      
        try:
            if preferred_source == "":
                preferred_source=self.config["preferred_attitude_source"]
        except KeyError:
            self.post_log.warning("No preferred attitude data specified")

        if preferred_source in data and (not (preferred_source == self.cam_attitudes["source"])):
            no_cache = True #Force refresh if the preferred source becomes available

        if (self.cam_attitudes["source"] == "") or (no_cache == True):
            if preferred_source in data:
                self.cam_attitudes["timestamps"] = data[preferred_source]["timestamps"]
                self.cam_attitudes["pitch"] = data[preferred_source]["pitch"]
                self.cam_attitudes["roll"] = data[preferred_source]["roll"]
                self.cam_attitudes["yaw"] = data[preferred_source]["yaw"]
                self.cam_attitudes["recNum"] = data[preferred_source]["recNum"]
                self.post_log.info("Using attitude data from %s" % preferred_source)
            else:
                for i_name, inst in data.items():
                    try:
                        self.cam_attitudes["timestamps"] = inst["timestamps"]
                        self.cam_attitudes["pitch"] = inst["pitch"]
                        self.cam_attitudes["roll"] = inst["roll"]
                        self.cam_attitudes["yaw"] = inst["yaw"]
                        self.cam_attitudes["recNum"] = inst["recNum"]
                        self.cam_attitudes["source"] = i_name
                        self.post_log.info("Using location data from %s" % i_name)
                        break
                    except (KeyError, TypeError):
                        continue
        else:
            self.post_log.info("Using cached attitude data from %s" % self.cam_attitudes["source"])
        return self.cam_attitudes

    def export_loc_and_att(self, inst_data_path, data):
        self.post_log.info("Exporting location and attitude info...")
        fname = path.normpath(path.join(inst_data_path,"location_attitude.txt"))
        with open(fname, 'w') as csv_f:
            csv_f.write("recNum,loc_timestamp,att_timestamp,long,lat,alt,yaw,cam_pitch,cam_roll,cam_yaw\n")
            locations = self.get_locations(data)
            attitudes = self.get_cam_attitude(data)
            rec_list = sorted([int(r) for r in set(list(locations["recNum"]) + list(attitudes["recNum"]))])
            
            combined = {}
            for rec in rec_list:
                loc_idx = locations["recNum"].index(str(rec))
                att_idx = attitudes["recNum"].index(str(rec))
                combined = {"recNum":rec}
                try:
                    locs_dict = {"loc_timestamp":locations["timestamps"][loc_idx], "coords":locations["coords"][loc_idx], "alt":locations["alt"][loc_idx], "yaw":locations["yaw"][loc_idx]}
                except KeyError:
                    self.post_log.warning("\tLocation missing for recNum %i" % rec)
                    locs_dict = {"loc_timestamp":np.NaN, "coords":(np.NaN,np.NaN), "alt":np.NaN, "yaw":np.NaN}
                finally:
                    combined.update(locs_dict)

                try:
                    atts_dict = {"att_timestamp":attitudes["timestamps"][att_idx], "cam_pitch":attitudes["pitch"][att_idx], "cam_roll":attitudes["roll"][att_idx], "cam_yaw":attitudes["yaw"][att_idx]}
                except KeyError:
                    self.post_log.warning("\tAtittude missing for recNum %i" % rec)
                    atts_dict = {"att_timestamp":np.NaN, "cam_pitch":np.NaN, "cam_roll":np.NaN, "cam_yaw":np.NaN}
                finally:
                    combined.update(atts_dict)

                rec_str = "%i,%f,%f,%f,%f,%f,%f,%f,%f,%f\n" % (combined["recNum"],combined["loc_timestamp"],combined["att_timestamp"],combined["coords"][0],combined["coords"][1],combined["alt"],combined["yaw"],combined["cam_pitch"],combined["cam_roll"],combined["cam_yaw"])
                csv_f.write(rec_str)
        self.post_log.info("Done saving to %s" % fname)
        return
    
    def export_geo(self, inst_data_path, data):
        self.post_log.info("Exporting location and attitude info...")

        locations = self.get_locations(data)
        attitudes = self.get_cam_attitude(data)

        for i_name, inst in data.items():
            try:
                img_list = inst["images"]
                rec_list = [int(r) for r in inst["recNum"]]
            except KeyError:
                self.post_log.info("No images for instrument %s, skipping")
                continue

            fname = path.normpath(path.join(path.dirname(img_list[0]),"geo.txt"))

            with open(fname, 'w') as csv_f:
                csv_f.write("EPSG:4326\n")
                combined = {}
                for rec in rec_list:
                    loc_idx = locations["recNum"].index(str(rec))
                    att_idx = attitudes["recNum"].index(str(rec))
                    img_file = img_list[rec_list.index(rec)]

                    combined = {"file":path.split(img_file)[1]}
                    locs_dict = {}
                    atts_dict = {}

                    try:
                        locs_dict = {"loc_timestamp":locations["timestamps"][loc_idx], "coords":locations["coords"][loc_idx], "alt":locations["alt"][loc_idx], "yaw":locations["yaw"][loc_idx]}
                    except KeyError:
                        self.post_log.warning("\tLocation missing for recNum %i" % rec)
                        locs_dict = {"loc_timestamp":np.NaN, "coords":(np.NaN,np.NaN), "alt":np.NaN, "yaw":np.NaN}
                    finally:
                        combined.update(locs_dict)

                    try:
                        atts_dict = {"att_timestamp":attitudes["timestamps"][att_idx], "cam_pitch":attitudes["pitch"][att_idx], "cam_roll":attitudes["roll"][att_idx], "cam_yaw":attitudes["yaw"][att_idx]}
                    except KeyError:
                        self.post_log.warning("\tAtittude missing for recNum %i" % rec)
                        atts_dict = {"att_timestamp":np.NaN, "cam_pitch":np.NaN, "cam_roll":np.NaN, "cam_yaw":np.NaN}
                    finally:
                        combined.update(atts_dict)

                    rec_str = "%s\t%f\t%f\t%f\t%f\t%f\t%f\n" % (combined["file"],combined["coords"][0],combined["coords"][1],combined["alt"],combined["yaw"]+combined["cam_yaw"],combined["cam_pitch"],combined["cam_roll"])
                    csv_f.write(rec_str)
            self.post_log.info("Done saving to %s" % i_name)
        return       

    def pixhawk_v2(self, inst_data_path, data):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []
        output["gps_timestamps"] = []
        output["recNum"] = []

        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]
            lat = x[1]["Global Location"]["lat"]
            lon = x[1]["Global Location"]["lon"]
            
            year = int(x[1]["GPS"]["Raw Data"].split("year=")[1].split(',')[0])
            month = int(x[1]["GPS"]["Raw Data"].split("month=")[1].split(',')[0])
            day = int(x[1]["GPS"]["Raw Data"].split("day=")[1].split(',')[0])
            hour = int(x[1]["GPS"]["Raw Data"].split("hour=")[1].split(',')[0])
            minute = int(x[1]["GPS"]["Raw Data"].split("min=")[1].split(',')[0])
            second = int(x[1]["GPS"]["Raw Data"].split("sec=")[1].split(',')[0])
            try:
                micro = int(x[1]["GPS"]["Raw Data"].split("nano=")[1].split(',')[0]) / 1000
            except IndexError:
                micro = 0

            gps_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, tzinfo=timezone.utc).timestamp()
            gps_time += micro * 1000000

            output["coords"].append((lon, lat))
            output["timestamps"].append(x[0])
            output["gps_timestamps"].append(gps_time)
            output["recNum"].append(recNum)

        return output
    
    def gremsy_gimbal(self, inst_data_path, data):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["timestamps"] = []
        output["recNum"] = []
        output["pitch"] = []
        output["roll"] = []
        output["yaw"] = []

        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]
            output["timestamps"].append(x[0])
            output["pitch"].append(x[1]["pitch"])
            output["roll"].append(x[1]["roll"])
            output["yaw"].append(x[1]["yaw"])
            output["recNum"].append(recNum)

        return output

    def pi_gps_ublox(self, inst_data_path, data):
        self.post_log.info("Loading Pi GPS data...")
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []
        output["gps_timestamps"] = []
        output["alt"] = []
        output["yaw"] = []
        output["pdop"] = []
        output["recNum"] = []

        self.post_log.info("Extracting location info...")
        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]

            year = int(x[1]["GPS"]["Raw Data"].split("year=")[1].split(',')[0])
            month = int(x[1]["GPS"]["Raw Data"].split("month=")[1].split(',')[0])
            day = int(x[1]["GPS"]["Raw Data"].split("day=")[1].split(',')[0])
            hour = int(x[1]["GPS"]["Raw Data"].split("hour=")[1].split(',')[0])
            minute = int(x[1]["GPS"]["Raw Data"].split("min=")[1].split(',')[0])
            second = int(x[1]["GPS"]["Raw Data"].split("sec=")[1].split(',')[0])
            try:
                micro = int(x[1]["GPS"]["Raw Data"].split("nano=")[1].split(',')[0]) / 1000
            except IndexError:
                micro = 0

            gps_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, tzinfo=timezone.utc).timestamp()
            gps_time += micro / 1000000

            lat = x[1]["Global Location"]["lat"]
            try:
                lon = x[1]["Global Location"]["lon"]
            except KeyError:
                lon = x[1]["Global Location"]["long"]
            alt = x[1]["Global Location"]["alt"]
            output["coords"].append((lon, lat))
            output["timestamps"].append(x[0])
            output["gps_timestamps"].append(gps_time)
            output["alt"].append(alt)
            output["yaw"].append(float(x[1]["GPS"]["Raw Data"].split("headVeh=")[1].split(',')[0]))
            output["pdop"].append(float(x[1]["GPS"]["Raw Data"].split("pDOP=")[1].split(',')[0]))
            output["recNum"].append(recNum)

        return output

    def usb2000_pair(self, inst_data_path, data):

        def generate_preview(wavelengths, record, fname):
            plt.plot(wavelengths, record[1]["Reflectance"])
            plt.xlabel('Wavelength (nm)')
            plt.ylabel('Reflectance')
            plt.ylim([min(wavelengths),max(wavelengths)])
            plt.ylim([0,1])
            plt.savefig(fname, bbox_inches='tight', dpi=100)
            plt.close()
            return fname

        output = {} #list of preview filenames
        output["images"] = []
        output["recNum"] = []

        try:
            if self.config["spec_recalc"].lower() == "true":
                self.post_log.info("Reprocessing spec data...")
                try:
                    recalc = subprocess.call(["python",path.join("instruments","usb2000-pair","recalc.py"),inst_data_path])
                except ImportError:
                    self.post_log.warning("Recalc funciton not found, skipping")
        except KeyError:
            self.post_log.warning("Spec recalc not configured, skipping")

        base_dir = path.normpath(path.join(path.split(inst_data_path)[0], "post", "Specs"))
        gen_previews = self.config["generate_spec_previews"].lower() == "true"

        if gen_previews or path.isdir(base_dir):
            if gen_previews:
                self.post_log.info("Generating spec previews...")
                makedirs(base_dir, exist_ok=True)
            else:
                self.post_log.info("Indexing existing spec previews...")
            
            with open(inst_data_path, 'r') as data_file:
                data = json.load(data_file)

            for recNum, rec in data["Data"].items():
                if int(recNum) % 50 == 0:
                    self.post_log.info("\t%i%% (%i/%i)" % (round(int(recNum)/len(data["Data"])*100), int(recNum), len(data["Data"])))
                out_path = path.join(base_dir, "recNum_" + recNum + ".png")
                
                if gen_previews:
                    generate_preview(data["Wavelengths"]["Downward"], rec, out_path)
                
                if int(recNum) >= 0 and (recNum not in output["recNum"]):   #keep only global events
                    output["images"].append(out_path)
                    output["recNum"].append(recNum)
            self.post_log.info("Done.")
        return output


    def gphoto2_cam(self, inst_data_path, data):
        output = {} #list of preview filenames
        output["images"] = []
        output["recNum"] = []

        self.post_log.info("\t\tProcessing RGB images...")

        #get locations
        locations = self.get_locations(data)

        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
            
        try:
            cfg_out_path = self.config["gphoto2_cam_path"]
            if os.path.isabs(cfg_out_path):
                out_path_base = cfg_out_path
            else:
                out_path_base = path.join(path.split(inst_data_path)[0], "Canon", cfg_out_path)
        except KeyError:
            out_path_base = path.join(path.split(inst_data_path)[0], "Canon")
            self.post_log.warning("Full size path not specified, attempting to use preview path")
        
        self.post_log.info("Preview path:\t%s" % path.normpath(path.join(path.split(inst_data_path)[0], "Canon")))
        self.post_log.info("Full size path:\t%s" % out_path_base)

        for recNum, rec in data["Data"].items():
        #for recNum, rec in [(recNum, data["Data"][str(recNum)]) for recNum in sorted(int(i) for i in data["Data"].keys())]:
            if int(recNum) % 50 == 0:
                self.post_log.info("\t%i%% (%i/%i)" % (round(int(recNum)/len(data["Data"])*100), int(recNum), len(data["Data"])))
        
            #Get prev filename
            out_prev_path = path.normpath(path.join(path.split(inst_data_path)[0], "Canon", "prev_" + path.split(rec[1])[1]))
            if int(recNum) >= 0 and (recNum not in output["recNum"]):   #keep only global events
                output["images"].append(out_prev_path)
                output["recNum"].append(recNum)


            #Get full size filename
            out_path = path.normpath(path.join(out_path_base, path.split(rec[1])[1]))

            if self.config["convert_raw_to_jpg"].lower() == "true":
                if out_path[:-3].upper() == "CR2":
                    jpg_path = out_path.rsplit(out_path[:-3], 1)[0] + ".JPG"
                    im = Image.open(out_path)
                    rgb_im = im.convert('RGB')
                    rgb_im.save(jpg_path)
                    out_path = jpg_path

            if self.config["geotag"].lower() == "true":
                #Prep GPS data
                try:
                    coords = [float(f) for f in locations["coords"][int(recNum)]]
                    if np.isnan(coords).any():
                        raise KeyError
                    coords.reverse()
                    dt = datetime.fromtimestamp(locations["timestamps"][int(recNum)])
                    alt_vals = float(locations["alt"][int(recNum)])
                    gps_meta = gpsphoto.GPSInfo(coords, timeStamp=dt)
                    gps_meta.setAlt(alt_vals)

                    # Modify previews
                    try:
                        photo = gpsphoto.GPSPhoto(out_prev_path)
                        photo.modGPSData(gps_meta, out_prev_path)
                    except FileNotFoundError:
                        self.post_log.warning("\tPreview %s not found, skipping" % out_prev_path)

                    #Modify full size
                    try:
                        photo = gpsphoto.GPSPhoto(out_path)
                        photo.modGPSData(gps_meta, out_path)
                    except FileNotFoundError:
                        self.post_log.warning("\tFull sized image %s not found, skipping" % out_path)

                except KeyError:
                    self.post_log.warning("No location data for record %s, EXIF not updated." % recNum)

        return output

    def ici_thermal(self, inst_data_path, data):
        output = {} #list of preview filenames
        output["images"] = []
        output["recNum"] = []

        self.post_log.info("\t\tGenerating thermal previews...")

        #get locations
        locations = self.get_locations(data)

        #Create previews
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)

        im_height = data["Header"]["Height"]
        im_width = data["Header"]["Width"]
        im_size = data["Header"]["Size"]

        imgbuf = np.zeros((im_height, im_width), np.float32)
        datbuf = (ctypes.c_float * im_size)()   

        for recNum, rec in data["Data"].items():
        #for recNum, rec in [(recNum, data["Data"][str(recNum)]) for recNum in sorted(int(i) for i in data["Data"].keys())]:
            #Get filename
            try:
                fname = rec[1]["file"]  #check for newer format
                fpaState = rec[1]["fpaState"]
            except (TypeError, KeyError):
                fname = rec[1]
                fpaState = -1
        
            imgFile = path.normpath(path.join(path.split(inst_data_path)[0], "Thermal", path.split(fname)[1]))
            out_path = path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal", path.split(fname)[1]))[:-3] + "jpg"
            out_path_tif = path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal", path.split(fname)[1]))[:-3] + "tif"
            if int(recNum) >= 0 and (recNum not in output["recNum"]):   #keep only global events
                output["images"].append(out_path_tif)
                output["recNum"].append(recNum)

            if self.config["generate_ici_previews"].lower() == "true":
                #Load binary
                with open(imgFile, 'rb') as in_file:
                    in_file.readinto(datbuf)
                    
                #Save File
                imgbuf = np.reshape(datbuf, (im_height, im_width))
                makedirs(path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal")), exist_ok=True)
                #out_path = path.normpath(path.join(path.split(inst_data_path)[0], "post", "Thermal", path.split(rec[1])[1]))[:-3] + "jpg"
                plt.imsave(out_path, imgbuf, cmap='inferno', vmin=0, vmax=45)
                tifffile.imwrite(out_path_tif, imgbuf, photometric='minisblack')

                if self.config["geotag"].lower() == "true":
                    #Prep GPS data
                    try:
                        photo = gpsphoto.GPSPhoto(out_path)
                        coords = [float(f) for f in locations["coords"][int(recNum)]]
                        if np.isnan(coords).any():
                            raise KeyError
                        coords.reverse()
                        dt = datetime.fromtimestamp(locations["timestamps"][int(recNum)])
                        alt_vals = float(locations["alt"][int(recNum)])
                        gps_meta = gpsphoto.GPSInfo(coords, timeStamp=dt)
                        gps_meta.setAlt(alt_vals)
                        photo.modGPSData(gps_meta, out_path)
                        #tifffile.imwrite(out_path_tif, imgbuf, photometric='minisblack', metadata=)
                    except KeyError:
                        self.post_log.warning("No location data for record %s, EXIF not updated." % recNum)
                    
        return output
        
    def kml_builder(self, inst_data_path, data):

        buildkml = kml.BuildKML(inst_data_path)
        buildkml.read_data()
        
        locations = self.get_locations(data)
        rec_list = locations["recNum"]
        image_lists = {}

        for i_name, inst in data.items():
            try:
                image_list = [inst["images"][rec] if rec >=0 else "" for rec in [inst["recNum"].index(r) if r in inst["recNum"] else -1 for r in rec_list]]
                image_lists[i_name] = image_list
            except (KeyError, TypeError):
                continue

        images = list(zip(*image_lists.values()))
        buildkml.build_kml(locations, images)

        if self.config["generate_kmz"].lower() == "true":
            buildkml.build_kmz(locations, images)


    def px4_ulog(self, inst_data_path, data):
        try:
            from scipy import interpolate
            import pyulog
        except Exception:
            self.post_log.warning("pyulog or scipy not found, skipping px4 log data")
            return

        primary = data["pi_gps_ublox"]
        fuse_method = "interp_ulog_only" # "weighted_with_threshold" "threshold" "weighted"
        pdop_threshold = 2
        interp_method = 'nearest'

        def gps_fusion(primary, secondary, fuse_method, pdop_threshold, interp_method):

            #Interp to primary timestamp
            ulog_interp = {}
            for v in ("lat", "lon", "alt", "pdop", "yaw"):
                interp_ser = interpolate.interp1d(secondary["gps_timestamps"],secondary[v], kind=interp_method, bounds_error=False, fill_value=(secondary[v][0], secondary[v][-1]))
                ulog_interp[v] = interp_ser(primary["gps_timestamps"])

            extrap_count = sum(primary["gps_timestamps"] < min(secondary["gps_timestamps"])) + sum(primary["gps_timestamps"] > max(secondary["gps_timestamps"]))
            if extrap_count > 0:
                self.post_log.warning("\t%d values extrapolated" % extrap_count)

            #Fuse data
            fused = {}
            
            if fuse_method == "threshold":
                use_ulog = np.where((primary["pdop"] > ulog_interp["pdop"]) & (primary["pdop"] > pdop_threshold), True, False)
                for v in ("lat", "lon", "alt", "yaw"):
                    fused[v] = np.where(use_ulog, ulog_interp[v], primary[v])

            elif fuse_method == "weighted":
                pdop_ratio = primary["pdop"] / ulog_interp["pdop"]
                for v in ("lat", "lon", "alt", "yaw"):
                    fused[v] = (ulog_interp[v]*pdop_ratio + primary[v])/(pdop_ratio + 1)

            elif fuse_method == "weighted_with_threshold":
                bad_primary = np.where((primary["pdop"] > ulog_interp["pdop"]) & (primary["pdop"] > pdop_threshold), True, False)
                pdop_ratio = primary["pdop"] / ulog_interp["pdop"]
                for v in ("lat", "lon", "alt", "yaw"):
                    weigthed = (ulog_interp[v]*pdop_ratio + primary[v]/pdop_ratio)/(pdop_ratio + 1/pdop_ratio)  
                    fused[v] = np.where(bad_primary, ulog_interp[v], weigthed)

            else:   #interp ts and use ulog only
                fused = ulog_interp

            fused["timestamps"] = primary["timestamps"]
            fused["recNum"] = primary["recNum"]

            return fused
        
        #Load primary data
        primary["lon"], primary["lat"] = zip(*primary["coords"])
        primary["lon"] = np.array(primary["lon"], dtype=np.float32)
        primary["lat"] = np.array(primary["lat"], dtype=np.float32)
        primary["alt"] = np.array(primary["alt"], dtype=np.float32)
        primary["pdop"] = np.array(primary["pdop"], dtype=np.float32)
        primary["yaw"] = np.array(primary["yaw"], dtype=np.float32)

        #Load secondary data
        msg_list = ["vehicle_gps_position","vehicle_global_position"]
        ulog_paths = sorted(glob(path.normpath(path.join(inst_data_path,"*.ulg"))))
        if len(ulog_paths) > 1:
            self.post_log.warning("Multiple ulog files found, using %s" % ulog_paths[0])
        elif len(ulog_paths) == 0:
            self.post_log.warning("No ulog files found, skipping px4 log data")
            return
            
        ulog = pyulog.ULog(ulog_paths[0], msg_list)
        if ulog.data_list[0].name == "vehicle_gps_position":
            ulog_dict = ulog.data_list[0].data
            ulog_global_dict = ulog.data_list[1].data
        else:
            ulog_dict = ulog.data_list[1].data
            ulog_global_dict = ulog.data_list[0].data
            
        ulog_dict["pdop"] = np.sqrt(np.power(ulog_dict["hdop"],2) + np.power(ulog_dict["vdop"],2))     #calc pdop since ulog provides h and v separately
        ulog_dict["lon"] = ulog_dict["lon"] / 10000000
        ulog_dict["lat"] = ulog_dict["lat"] / 10000000
        ulog_dict["alt"] = ulog_dict["alt"] / 1000          #convert to meters
        ulog_dict["gps_timestamps"] = ulog_dict["time_utc_usec"]/1000000

        yaw_interp = interpolate.interp1d(ulog_global_dict["timestamp"], ulog_global_dict["yaw"], kind="nearest", bounds_error=False, fill_value=(ulog_global_dict["yaw"][0], ulog_global_dict["yaw"][-1]))
        ulog_dict["yaw"] = yaw_interp(ulog_dict["timestamp"]) / np.pi * 180   #match imu to gps timescale and convert to degrees

        fused = gps_fusion(primary, ulog_dict, fuse_method, pdop_threshold, interp_method)
    
        ## Plot pdops
        # plt.scatter(primary_ts, ulog_interp["pdop"], c='g', marker='o')
        # plt.scatter(gps_dict["time_utc_usec"]/1000000, gps_dict["pdop"], c='b', marker='*')
        # plt.scatter(primary_ts, primary_pdop, c='r', marker='x')
        # plt.show()

        ## Plot Lat vs Time
        # plt.scatter(gps_dict["time_utc_usec"]/1000000, gps_dict["lat"]/10000000, c='b', marker='.', label="Alta")
        # plt.scatter(primary["ts"], fused["lat"], c='g', marker='o', label="Fused")
        # plt.scatter(primary["ts"], primary["lat"], c='r', marker='.', label="Rasp Pi GPS")
        # plt.legend(loc="upper left")
        # plt.show(block=True)

        fig, axs = plt.subplots(3)
        fig.set_size_inches(8,10)

        # Plot Lon vs Lat
        axs[0].scatter(ulog_dict["lon"], ulog_dict["lat"], c='b', marker='.', label="Alta")
        axs[0].scatter(fused["lon"], fused["lat"], c='g', marker='o', label="Fused")
        axs[0].scatter(primary["lon"], primary["lat"], c='r', marker='.', label="Rasp Pi GPS")
        axs[0].legend(loc="lower left")
        axs[0].set(xlabel='Longitude', ylabel='Latitude')

        # Plot alt and pdop
        axs[1].plot(ulog_dict["gps_timestamps"], ulog_dict["alt"], c='b', marker='.', label="Alta")
        axs[1].plot(primary["gps_timestamps"], fused["alt"], c='g', marker='o', label="Fused")
        axs[1].plot(primary["gps_timestamps"], primary["alt"], c='r', marker='.', label="Rasp Pi GPS")
        axs[1].legend(loc="lower left")
        axs[1].set(ylabel='Altitude')

        axs[2].plot(ulog_dict["gps_timestamps"], ulog_dict["pdop"], c='b', marker='.', label="Alta")
        axs[2].plot(primary["gps_timestamps"], fused["pdop"], c='g', marker='o', label="Fused")
        axs[2].plot(primary["gps_timestamps"], primary["pdop"], c='r', marker='.', label="Rasp Pi GPS")
        axs[2].legend(loc="lower left")
        axs[2].sharex(axs[1])
        axs[2].set(xlabel='GPS Timestamp', ylabel='PDOP')

        fig.savefig(path.normpath(path.join(inst_data_path,"gps_fusion_result.png")), bbox_inches='tight', dpi=100)
        plt.close()

        fused["coords"] = list(zip(fused["lon"],fused["lat"]))

        return fused