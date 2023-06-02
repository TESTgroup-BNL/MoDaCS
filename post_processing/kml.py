from genericpath import exists
import json, ast, os
from os import path, makedirs
from datetime import datetime
import logging
import zipfile
import simplekml


class BuildKML():

    def __init__(self, run_cfg=None):
        
        logging.basicConfig(level=logging.DEBUG)
        self.post_log = logging.getLogger("Post_Processing")
    
        if run_cfg is None:
            self.post_log.warning("No data download path provided, skipping post processing")
            return
        
        self.run_cfg = run_cfg
        self.build_dir = False
        self.post_log.info("Checking paths...")

        if type(self.run_cfg) is str:
            self.data_root = self.run_cfg
        else:
            self.data_root = self.run_cfg["Data"]["dataPath"]

        self.fname = path.join(self.data_root, "RunData.json")

    def read_data(self, fname=None):
        self.post_log.info("\tReading JSON data...")

        if fname==None:
            fname = self.fname

        try:
            with open(fname) as rdJSON:
                self.runData = json.load(rdJSON)
        except Exception as e:
            self.post_log.info("\tError loading JSON data")
            return str(e)

        insts = self.runData["InstrumentPaths"]
        self.data = {}

        self.post_log.info("\tProcessing instrument data...")

        for name, inst_path in insts.items():
            self.post_log.info("\t\t%s" % name)
            inst_path = path.join(self.data_root, os.path.split(inst_path)[1]) + ".json"
            func_name = name.replace("-","_")
            if hasattr(Instruments, func_name):
                try:
                    self.data[name] = getattr(Instruments, func_name)(self, inst_path)
                except FileNotFoundError as e:
                    self.post_log.info("\t\t\tMissing some flight data (or maybe a dashboard log), skipping flight")
                    return str(e)
            else:
                self.post_log.info("\t\t\tNo processing function found, skipping instrument")

        return None

    def build_kml(self, locations=None, images=None, out_file_path=""):
        #if data_root==None:
        #    data_root = self.data_root
        try:
            flight_start = self.splitall(self.data_root)[-1] #datetime.fromtimestamp(self.data["pixhawk_v2"]["timestamps"][i]).strftime('%Y-%m-%d_%H%M%S')
            self.post_log.info("\tBuilding KML output for %s..." % flight_start)

            if locations is None:
                locations = {}
                for i_name, inst in self.data.items():
                    try:
                        locations["timestamps"] = inst["timestamps"]
                        locations["coords"] = inst["coords"]
                        self.post_log.info("\tUsing location data from %s" % i_name)
                        break
                    except (KeyError, TypeError):
                        continue

            try:
                coords_list = [(lon, lat, alt) for ((lon, lat), alt) in zip(locations["coords"], locations["alt"])]
                alt_mode = simplekml.AltitudeMode.absolute
            except KeyError:
                coords_list = locations["coords"]
                alt_mode = simplekml.AltitudeMode.clamptoground

            kml = simplekml.Kml()
            ls = kml.newlinestring(name=flight_start)
            ls.coords = coords_list
            ls.extrude = 1
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.lightblue)
            ls.altitudemode = alt_mode
            ls.style.linestyle.width = 5
            ls.style.linestyle.color = simplekml.Color.lightblue

            for i, coords in enumerate(coords_list):
                pnt = kml.newpoint(name="%i" % i)
                pnt.coords = [coords]
                pnt.altitudemode = alt_mode
                pnt.style.iconstyle.scale = 0.8
                pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/airports.png'
                pnt.style.iconstyle.heading = locations["yaw"][i]
                pnt.style.labelstyle.scale = 0.8
                if images is not None:
                    img_str = ""
                    for img in images[i]:
                        try:
                            img_str += r"<tr><td><img width=100% src='" + path.relpath(img, self.data_root) + r"' /></td></tr>"
                        except ValueError:
                            img_str += r"<tr><td><div width=100%>(No preview available)</div></td></tr>"

                    pnt.balloonstyle.text = r"<![CDATA[ <table width=640px cellpadding=0 cellspacing=0>" + img_str + r"</table>]]>"
                pnt.timestamp.when = datetime.fromtimestamp(locations["timestamps"][i]).strftime('%Y-%m-%dT%H:%M:%SZ')

            if out_file_path=="":
                out_file_path = path.join(self.data_root, flight_start + ".kml")

            kml.save(out_file_path)
            
            self.post_log.info("\tDone.")
        except KeyError:
            self.post_log.info("\tMissing info from instrument data, skipping flight")
        return

    def build_kmz(self, locations=None, images=[]):
        self.post_log.info("Building KMZ...")
        try:
            flight_start = self.splitall(self.data_root)[-1]
            out_file_path = path.join(self.data_root, flight_start + ".kmz")
            makedirs(path.join(self.data_root, "post"), exist_ok=True)
            self.post_log.info("\tCreating file: %s" % out_file_path)

            with zipfile.ZipFile(out_file_path, 'w') as kmz:
                self.post_log.info("\tAdding previews for %i points..." % len(images))
                for recNum, pt in enumerate(images):
                    if int(recNum) % 50 == 0:
                        self.post_log.info("\t\t%i%% (%i/%i)" % (round(int(recNum)/len(images)*100), int(recNum), len(images)))
                    for f in pt:
                        try:
                            f_arc = path.relpath(f, self.data_root)
                            kmz.write(f,f_arc)
                        except ValueError:
                            pass
                kml_temp = path.join(self.data_root,"post","doc.kml")
                self.build_kml(locations, images, out_file_path=kml_temp)
                kmz.write(kml_temp, "doc.kml")

            self.post_log.info("\tDone writing, checking integrity...")
            with zipfile.ZipFile(out_file_path, 'r') as kmz:
                test = kmz.testzip() 
                if test is None:
                    self.post_log.info("\t\tAll files and checksums are good.")
                else:
                    self.post_log.warning("\t\tError in file: %s, KMZ may be corrupt" % test)

            self.post_log.info("\tRemoving temp files...")
            os.remove(kml_temp)
            self.post_log.info("\tDone.")
        except KeyError as e:
            self.post_log.info("\t'%s', skipping flight" % str(e))
        return

    def reprocess_dir(self):
        self.starting_root = self.data_root
        self.build_dir = True

        #with open(path.join(root_temp, "Overview.kml", 'w') as self.build_dir_file:
        for root, subdirs, files in os.walk(self.starting_root):
            self.post_log.info("Looking in %s" % root)
            if "RunData.json" in files:
                self.data_root = root
                self.post_log.info("\tFound RunData.json")
                if self.read_data(path.join(root, "RunData.json")) is None:
                    self.build_kml()

    def splitall(self, path):
        """Split a path into all of its parts.

        From: Python Cookbook, Credit: Trent Mick
        """
        allparts = []
        while 1:
            parts = os.path.split(path)
            if parts[0] == path:
                allparts.insert(0, parts[0])
                break
            elif parts[1] == path:
                allparts.insert(0, parts[1])
                break
            else:
                path = parts[0]
                allparts.insert(0, parts[1])
        return allparts

class Instruments():
    def pixhawk_v2(self, inst_data_path):
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

    def pi_gps_ublox(self, inst_data_path):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []

        for recNum in sorted(data["Data"].keys(), key=lambda k: int(k)):
            #print(str(recNum))
            x = data["Data"][recNum]
            lat = x[1]["Global Location"]["lat"]
            try:
                lon = x[1]["Global Location"]["lon"]
            except KeyError:
                lon = x[1]["Global Location"]["long"]
            output["coords"].append((lon, lat))
            output["timestamps"].append(x[0])
        return output

    def USB2000_pair(self, inst_data_path):
        pass

    def ici_thermal(self, inst_data_path):
        pass



#if __name__ == '__main__':

#    buildkml = BuildKML(r"C:\Users\amcmahon\Desktop\Nome_2018_MoDaCS_Postprocessed\2018-07-14_035048")
#    buildkml.read_data()
#    buildkml.build_kml()
