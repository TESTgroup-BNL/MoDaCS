import json, ast, os
import logging
from glob import glob
from os import path, makedirs
from datetime import datetime
from shutil import ExecError, copy2

from util import JSONFileField
from post_processing.post_handlers import PostHandlers

class PostProcessing():

    def __init__(self, run_cfg=None):
        
        if run_cfg is None:
            logging.warning("No data download path provided, skipping post processing")
            return
        
        self.run_cfg = run_cfg
        self.build_dir = False

        logging.basicConfig(level=logging.DEBUG)
        logging.info("Running post-processing...")

        if type(self.run_cfg) is str:
            self.data_root = self.run_cfg
        else:
            self.data_root = self.run_cfg["Data"]["dataPath"]

        self.fname = path.join(self.data_root, "RunData.json")
        makedirs(path.join(self.data_root, "post"), exist_ok=True)
          
        self.close_partial_json()


    def close_partial_json(self):
        #check for un-closed json files
        logging.info("\tChecking for files that didn't close correctly...")
        temp_f_list = glob(path.join(self.data_root, "*.json_*"))
        if len(temp_f_list) > 0:
            makedirs(path.join(self.data_root, "post", "partial_jsons"), exist_ok=True)
            logging.info("\t\tFound %i, creating backup copy" % len(temp_f_list))
            for f in temp_f_list:
                copy2(f, path.join(self.data_root, "post", "partial_jsons"))

            logging.info("\t\tCombining partial files...")
            jff = JSONFileField()
            jff.closeOpenFiles(self.data_root)
            logging.info("\t\tDone.")
        else:
            logging.info("\t\tNone found.")



    def read_data(self, fname=None, priority=[]):
        logging.info("Reading JSON data...")

        if fname==None:
            fname = self.fname

        try:
            with open(fname) as rdJSON:
                self.runData = json.load(rdJSON)
        except Exception as e:
            logging.info("Error loading JSON data")
            return str(e)

        inst_paths = self.runData["InstrumentPaths"]
        insts = list(self.runData["InstrumentPaths"].keys())
        priority.reverse()
        for p in priority:
            try:
                insts.remove(p)
                insts.insert(0,p)
            except Exception:
                pass
        
        self.data = {}

        logging.info("Processing instrument data...")
        for name in insts:
            logging.info("\t%s" % name)
            inst_path = inst_paths[name]
            inst_path = path.join(self.data_root, os.path.split(inst_path)[1]) + ".json"
            if hasattr(PostHandlers, name):
                try:
                    self.data[name] = getattr(PostHandlers, name)(self, inst_path, self.data)
                except FileNotFoundError as e:
                    logging.info("\t\tMissing some data, skipping %s: %s" % (name, str(e)))
                    return str(e)
            else:
                logging.info("\t\tNo processing function found, skipping instrument")

        return None

        