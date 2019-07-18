import json, ast, os
from os import path
from datetime import datetime

import simplekml, logging



class BuildKML():
    
    def __init__(self, run_cfg):
        self.run_cfg = run_cfg
        self.build_dir = False
        
        logging.basicConfig(level=logging.DEBUG)
        logging.info("Running post-processing...")
        
        if type(self.run_cfg) is str:
            self.data_root = self.run_cfg
        else:
            self.data_root = self.run_cfg["Data"]["dataPath"]
        
        self.fname = path.join(self.data_root, "RunData.json")
    
    def read_data(self, fname=None):
        logging.info("Reading JSON data...")
        
        if fname==None:
            fname = fname.self
            
        try:
            with open(fname) as rdJSON:
                self.runData = json.load(rdJSON)
        except Exception as e:
            logging.info("Error loading JSON data")
            return str(e)
        
        insts = self.runData["InstrumentPaths"]
        self.data = {}
        
        logging.info("Processing instrument data...")
        
        for name, inst_path in insts.items():
            logging.info("\t%s" % name)
            inst_path = path.join(self.data_root, os.path.split(inst_path)[1]) + ".json"
            if hasattr(Instruments, name):
                try:
                    self.data[name] = getattr(Instruments, name)(self, inst_path)
                except FileNotFoundError as e:
                    logging.info("\t\tMissing some flight data (or maybe a dashboard log), skipping flight")
                    return str(e)
            else:
                logging.info("\t\tNo processing function found, skipping instrument")
                
        return None
            
    def build_kml(self):
        #if data_root==None:
        #    data_root = self.data_root
        try:
            flight_start = self.splitall(self.data_root)[-1] #datetime.fromtimestamp(self.data["pixhawk_v2"]["timestamps"][i]).strftime('%Y-%m-%d_%H%M%S')
            logging.info("Building KML output for %s..." % flight_start)
            
            kml = simplekml.Kml()
            ls = kml.newlinestring(name=flight_start)
            ls.coords = self.data["pixhawk_v2"]["coords"]
            ls.extrude = 1
            ls.altitudemode = simplekml.AltitudeMode.clamptoground
            ls.style.linestyle.width = 5
            ls.style.linestyle.color = simplekml.Color.lightblue
            
            for i, coords in enumerate(self.data["pixhawk_v2"]["coords"]):
                pnt = kml.newpoint(name="%i" % i)
                pnt.coords = [coords]
                pnt.style.iconstyle.scale = 0.8
                pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/blu-blank.png'
                pnt.style.labelstyle.scale = 0.8
                pnt.timestamp.when = datetime.fromtimestamp(self.data["pixhawk_v2"]["timestamps"][i]).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            out_file_path = path.join(self.data_root, flight_start + ".kml")
            kml.save(out_file_path)
            if self.build_dir==True:
                kml.save(path.join(self.starting_root, flight_start + ".kml"))
            logging.info("Done.")
        except KeyError:
            logging.info("Missing info from instrument data, skipping flight")
        return
    
    def reprocess_dir(self):
        self.starting_root = self.data_root
        self.build_dir = True
        
        #with open(path.join(root_temp, "Overview.kml", 'w') as self.build_dir_file:
        for root, subdirs, files in os.walk(self.starting_root):
            logging.info("Looking in %s" % root)
            if "RunData.json" in files:
                self.data_root = root
                logging.info("\tFound RunData.json")
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
    
    def USB2000pair(self, inst_data_path):
        pass
    
    def ici_thermal(self, inst_data_path):
        pass
    
    
    
#if __name__ == '__main__':
    
#    buildkml = BuildKML(r"C:\Users\amcmahon\Desktop\Nome_2018_MoDaCS_Postprocessed\2018-07-14_035048")
#    buildkml.read_data()
#    buildkml.build_kml()
    