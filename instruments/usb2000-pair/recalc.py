import sys, getopt, json

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

    #Read input file
    with open(in_path, 'r') as in_file:
        raw = json.load(in_file)

    wavelengths = raw["Wavelengths"]
    data = raw["Data"]
    refs = raw["References"]
    
    data_out = {}
    
    for recNum in data:
        try:
            darkCurrent = {}
            for dark_intens in raw["DarkCurrent"]:    #Upward and Downward
                darkCurrent[dark_intens[0]] = {"Upward":dark_intens[2]["Upward"], "Downward":dark_intens[2]["Downward"]}
            correctDark = True
        except KeyError:
            correctDark = False

        options = data[str(recNum)][1]["Options"]
        int_time = options["IntegrationTime"]

        #Set References
        refs = {} #{"Upward": [], "Downward": []}
        refs_avg = {}
        refs_temp = raw["References"]

        for ref in refs_temp:

            if ref[0] == int_time:
                if correctDark:
                    r = doCorrectDark(ref[2], darkCurrent, ref[0])   
                else:
                    r = ref[2]
                try:
                    refs[int_time].append(r)
                except KeyError:
                    refs[int_time] = []
                    refs[int_time].append(r)
                        
            refs_avg[int_time] = avgSamples(refs[int_time])
            upward_ref_interp = interp(wavelengths["Downward"], wavelengths["Upward"], refs_avg[int_time]["Upward"])

            

        #Set Intensities
        intensities = {"Upward":data[str(recNum)][1]["Upward"], "Downward":data[str(recNum)][1]["Downward"]}
        if correctDark:
            intensities = doCorrectDark(intensities, darkCurrent, int_time)

        #Calc Reflectance
        reflec = calcReflectance(wavelengths, refs_avg[int_time], intensities, upward_ref_interp)

        data_out[recNum] = {"Downward":intensities["Downward"], "Upward":intensities["Upward"], "Reflectance":list(reflec), "Options":options}
        
raw["Data"] = data_out
with open(in_path+"_recalced", 'a') as out_file:
    json.dump(raw, out_file)