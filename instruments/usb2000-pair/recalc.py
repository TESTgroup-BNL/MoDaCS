import sys, getopt, json
import logging
from os import path
from shutil import move
from numpy import interp, asarray



def calcReflectance(wavelengths, refs_avg, intensities, upward_ref_interp):
    upward_interp = interp(wavelengths["Downward"], wavelengths["Upward"], intensities["Upward"])
    reflec = (upward_ref_interp/asarray(refs_avg["Downward"]))*(asarray(intensities["Downward"])/upward_interp)
    return reflec

def doCorrectDark(intensities, darkCurrent, int_time):
    new_intensities = {"Upward": [], "Downward": []}
    try:
        for key, intens in new_intensities.items():
            #print("%s: %i intensities %i dark current" % (key, len(asarray(intensities[key])), len(asarray(darkCurrent[int_time][key]))))         
            new_intensities[key] = list(asarray(intensities[key]) - asarray(darkCurrent[int_time][key]))
    except KeyError:
        print("Dark current data missing for %s; correction not applied." % key)
        return intensities
    return new_intensities
    
def avgSamples(samples):
    temp_list = {}
    for samp in samples:
        for key, samp_dict_item in samp.items():
            try: 
                temp_list[key]
            except Exception:
                temp_list[key] = []
            temp_list[key].append(samp_dict_item)

    samplesAvg = {}
    #Calc new average
    for key in temp_list.keys():
        samplesAvg[key] = [sum(col)/len(col) for col in zip(*temp_list[key])]
    return samplesAvg
    
    
    
if __name__ == '__main__':

    in_path = sys.argv[1]
    logging.basicConfig(level=logging.DEBUG)
    post_log = logging.getLogger("Post_Processing")

    #Read input file
    post_log.info("Opening original file: %s" % in_path)
    with open(in_path, 'r') as in_file:
        raw = json.load(in_file)

    wavelengths = raw["Wavelengths"]
    data = raw["Data"]
    data_out = {}

    post_log.info("\tLoading %i dark current values..." % len(raw["DarkCurrent"]))
    darkCurrent = {}    
    try:
        for dark_intens in raw["DarkCurrent"]:    #Upward and Downward
            darkCurrent[dark_intens[0]] = {"Upward":dark_intens[2]["Upward"], "Downward":dark_intens[2]["Downward"]}
        correctDark = True
    except KeyError:
        correctDark = False

    #Set References
    refs = {} #{"Upward": [], "Downward": []}
    refs_avg = {}
    upward_ref_interp = {}
    refs_temp = raw["References"]

    post_log.info("\tLoading %i references..." % len(refs_temp))
    for ref in refs_temp:
        int_time = ref[0]
        if correctDark:
            r = doCorrectDark(ref[2], darkCurrent, ref[0])   
        else:
            r = ref[2]
        try:
            refs[int_time].append(r)
        except KeyError:
            refs[int_time] = []
            refs[int_time].append(r)

    for int_time, ref in refs.items():              
        refs_avg[int_time] = avgSamples(refs[int_time])
        upward_ref_interp[int_time] = interp(wavelengths["Downward"], wavelengths["Upward"], refs_avg[int_time]["Upward"])


    post_log.info("\tProcessing %i records..." % len(data))
    for n, recNum in enumerate(data):
        if n % 50 == 0:
            post_log.info("\t\t%i%% (%i/%i)" % (round(n/len(data)*100), n, len(data)))

        timestamp = data[str(recNum)][0]
        options = data[str(recNum)][1]["Options"]
        int_time = options["IntegrationTime"]
        
        #Set Intensities
        #post_log.info("\tCorrecting dark currents")
        intensities = {"Upward":data[str(recNum)][1]["Upward"], "Downward":data[str(recNum)][1]["Downward"]}
        if correctDark:
            intensities_corrected = doCorrectDark(intensities, darkCurrent, int_time)

            #Calc Reflectance
            #post_log.info("\tCorrecting reflectance")
            reflec = calcReflectance(wavelengths, refs_avg[int_time], intensities_corrected, upward_ref_interp[int_time])
        else:
            reflec = calcReflectance(wavelengths, refs_avg[int_time], intensities, upward_ref_interp[int_time])

        data_out[recNum] = [timestamp, {"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Reflectance":list(reflec), "Options":options}]
        
    raw["Data"] = data_out
    move(in_path, path.join(path.split(in_path)[0], "post", path.split(in_path)[1]).replace(".json", "_original.json"))
    
    post_log.info("Dumping JSON and saving output... (this might take a minute)")
    with open(in_path, 'a') as out_file:
        json.dump(raw, out_file)

    post_log.info("Recalced file saved: %s" % in_path)