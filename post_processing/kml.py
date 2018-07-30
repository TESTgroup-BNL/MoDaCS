import json, ast
from os import path
from datetime import datetime

import simplekml, logging



class BuildKML():
    
    def __init__(self, run_cfg):
        self.run_cfg = run_cfg
        logging.info("Running post-processing...")
        
    
    def read_data(self):
        logging.info("Reading JSON data...")
        
        if type(self.run_cfg) is str:
            self.data_root = self.run_cfg
        else:
            self.data_root = self.run_cfg["Data"]["dataPath"]
            
        fname = path.join(self.data_root, "RunData.json")
        
        with open(fname) as rdJSON:
            self.runData = json.load(rdJSON)
        
        insts = self.runData["InstrumentPaths"]
        self.data = {}
        
        logging.info("Processing instrument data...")
        
        for name, inst_path in insts.items():
            logging.info("\t%s" % name)
            inst_path = path.join(self.data_root, inst_path.split("/")[-1]) + ".json"
            if hasattr(Instruments, name):
                self.data[name] = getattr(Instruments, name)(self, inst_path)
            else:
                logging.info("\tNo processing function found, skipping")
            
    def build_kml(self):
        logging.info("Building KML output...")
        kml = simplekml.Kml()
        ls = kml.newlinestring(name='Flight Path')
        ls.coords = self.data["pixhawk_v2"]["coords"]
        ls.extrude = 1
        ls.altitudemode = simplekml.AltitudeMode.clamptoground
        ls.style.linestyle.width = 5
        ls.style.linestyle.color = simplekml.Color.lightblue
        
        for i, coords in enumerate(self.data["pixhawk_v2"]["coords"]):
            pnt = kml.newpoint(name="Sample %i" % i)
            pnt.coords = [coords]
            pnt.style.iconstyle.scale = 3  # Icon thrice as big
            pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/info-i.png'
            pnt.style.labelstyle.scale = 0.5
            pnt.timestamp.when = datetime.fromtimestamp(self.data["pixhawk_v2"]["timestamps"][i]).strftime('%Y-%m-%dT%H:%M:%SZ')
            
        kml.save(path.join(self.data_root, "FlightPreview.kml"))
        logging.info("Done.")
            
        
        
class Instruments():
    def pixhawk_v2(self, inst_data_path):
        with open(inst_data_path, 'r') as data_file:
            data = json.load(data_file)
        output = {}
        output["coords"] = []
        output["timestamps"] = []
        
        for recNum, x in data["Data"].items():
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
    