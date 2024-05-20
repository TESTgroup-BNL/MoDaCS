import ctypes

ctypes.CDLL("/usr/local/lib/libusb-1.0.so", mode = ctypes.RTLD_GLOBAL)
tc = ctypes.cdll.LoadLibrary('./ici9000Pythonlib_v2.so') 
tc.loadCal.argtypes = [ctypes.c_char_p]
tc.startCam()
tc.loadCal("./Cal".encode())
tc.stopCam()