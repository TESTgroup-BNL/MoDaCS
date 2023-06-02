import json, ast, os, sys, getopt
import logging
from glob import glob
from os import path, makedirs
from datetime import datetime
from shutil import ExecError, copy2
import configparser

from core.JSONFileField.jsonfilefield import JSONFileField
from post_processing.post_handlers import PostHandlers

class PostProcessing():

    def __init__(self, run_cfg=None, post_cfg_fname=None):

        #Start logging to console
        #logging.basicConfig(level=logging.DEBUG)
        self.post_log = logging.getLogger("Post_Processing")
        self.post_log.setLevel(logging.INFO)
        self.log_sh = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)-10s] (%(threadName)-10s), %(asctime)s,        [Post_Processing]: %(message)s")
        self.log_sh.setFormatter(formatter)
        self.post_log.addHandler(self.log_sh)
        self.post_log.propagate = False

        if run_cfg is None:
            self.post_log.warning("No data download path provided, skipping post processing")
            return
        
        self.run_cfg = run_cfg
        self.build_dir = False

        self.post_log.info("Running post-processing...")

        if type(self.run_cfg) is str:
            self.data_root = self.run_cfg
        else:
            self.data_root = self.run_cfg["Data"]["dataPath"]

        self.fname = path.join(self.data_root, "RunData.json")
        makedirs(path.join(self.data_root, "post"), exist_ok=True)

        #Add file log now that paths are established
        self.logPath = path.join(self.data_root, "post", "Post_Processing_Log.txt") 
        formatter = logging.Formatter('[%(levelname)-10s] (%(threadName)-10s), %(asctime)s, %(message)s') # 
        formatter.datefmt = '%Y/%m/%d %I:%M:%S'
        fileHandler = logging.FileHandler(self.logPath, mode='w')
        fileHandler.setFormatter(formatter)
        self.post_log.addHandler(fileHandler)

        try:
            #post_cfg_fname = path.join(self.data_root, "post_cfg.ini")
            if post_cfg_fname is None:
                post_cfg_fname = path.join(os.path.dirname(os.path.abspath(__file__)),'post_cfg.ini')
            cp = configparser.ConfigParser()
            cp.read(post_cfg_fname)
            self.post_cfg = cp
        except Exception as e:
            self.post_log.info("Error loading post config (%s), attempting to fallback on defaults" % str(e))
            self.post_cfg = {}

        try:
            if self.post_cfg["PostProcessing"]["ClosePartials"].lower() == "true":
                self.close_partial_json()
        except KeyError:
            pass

    def close_partial_json(self):
        #check for un-closed json files
        self.post_log.info("\tChecking for files that didn't close correctly...")
        temp_f_list = glob(path.join(self.data_root, "*.json_*"))
        if len(temp_f_list) > 0:
            makedirs(path.join(self.data_root, "post", "partial_jsons"), exist_ok=True)
            self.post_log.info("\t\tFound %i, creating backup copy" % len(temp_f_list))
            for f in temp_f_list:
                copy2(f, path.join(self.data_root, "post", "partial_jsons"))

            self.post_log.info("\t\tCombining partial files...")
            jff = JSONFileField()
            jff.closeOpenFiles(self.data_root)
            self.post_log.info("\t\tDone.")
        else:
            self.post_log.info("\t\tNone found.")


    def read_data(self, fname=None, priority=[]):
        self.post_log.info("Reading JSON data...")

        if fname==None:
            fname = self.fname

        try:
            with open(fname) as rdJSON:
                self.runData = json.load(rdJSON)
        except Exception as e:
            self.post_log.info("Error loading JSON data")
            return str(e)

        inst_paths = self.runData["InstrumentPaths"]
        insts = list(self.runData["InstrumentPaths"].keys())

        try:
            priority = self.post_cfg["PostProcessing"]["Priority"].split(',')
        except KeyError:
            self.post_log.warning("Priority not specified in config")

        priority.reverse()
        for p in priority:
            p_stripped = p.strip()
            try:
                insts.remove(p_stripped)
                insts.insert(0,p_stripped)
            except ValueError:
                insts.insert(0,p_stripped)   #add any "non instrument" processing functions
            except Exception:
                pass
        
        self.data = {}

        self.post_log.info("Processing instrument data...")
        handlers = PostHandlers(self.post_cfg["PostHandlerParams"])
        for name in insts:
            formatter = logging.Formatter("[%(levelname)-10s] (%(threadName)-10s), %(asctime)s,        [Post_Processsing]: %(message)s")
            self.log_sh.setFormatter(formatter)
            self.post_log.info("\t%s" % name)
            formatter = logging.Formatter("[%(levelname)-10s] (%(threadName)-10s), %(asctime)s,        [Post_Processsing-" + name + "]: %(message)s")
            self.log_sh.setFormatter(formatter)

            try:
                inst_path = inst_paths[name]
                inst_path = path.join(self.data_root, os.path.split(inst_path)[1]) + ".json"
            except KeyError:
                inst_path = self.data_root

            handler_name = name.replace("-","_")
            if hasattr(handlers, handler_name):
                try:
                    self.post_log.info("Processing instrument data...")
                    self.data[name] = getattr(handlers, handler_name)(inst_path, self.data)
                except FileNotFoundError as e:
                    self.post_log.info("\t\tMissing some data, skipping %s: %s" % (name, str(e)))
                    return str(e)
                except Exception as e:
                    self.post_log.warning("Error processing %s: %s" % (name, str(e)))
            else:
                self.post_log.info("\t\tNo processing function '%s' found, skipping instrument" % handler_name)

        self.post_log.info("Done with post processing.")
        return None


class BatchProcess():

    def __init__(self, top_path, post_config_fname=None):
        self.path_list = sorted(next(os.walk(top_path))[1])
        self.post_config_fname = post_config_fname
        logging.basicConfig(level=logging.INFO)
        logging.info("Found %i paths to batch process:\n%s" % (len(self.path_list), '\n\t'.join(self.path_list)))

    def run_batch(self):
        for p in self.path_list:
            logging.info("Processing %s" % p)
            post = PostProcessing(p, self.post_config_fname)
            post.read_data()
        logging.info("Done processing batch.")

if __name__ == '__main__':
    batch = False
    post_dir = None
    post_config_fname = None
    opts, args = getopt.getopt(sys.argv[1:],"hd:c:b:", ["help", "dir =", "config =", "batch ="])
    for opt, arg in opts:
        if opt in ("-h", "--help", "?", "help"):
            print("MoDaCS Post Processing Module\n\nUsage:\n\tpost_common.py -d <Directory> [-b] [-c <post config file>]\n\n\t<Directory> : Directory containing RunData.json file or nested directories containing RunData.json\n\t-b, --batch : Run post processing on every directory within the directory specified\n\t-c, --config : Use specified post config file (Defualt: './post_config.ini')")
            sys.exit()
        if opt in ("-d"):
            post_dir = arg
        if opt in ("-c", "--config"):
            post_config_fname = arg
        if opt in ("-b", "--batch"):
            batch = True
    
    if post_dir is None:
        print("Error: No directory specified")
        exit()

    if batch:
        bp = BatchProcess(post_dir, post_config_fname)
        bp.run_batch()
    else:
        post = PostProcessing(post_dir, post_config_fname)
        post.read_data()
        logging.info("Done processing batch.")