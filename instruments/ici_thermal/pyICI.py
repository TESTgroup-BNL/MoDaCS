import ctypes

class TC():
	def __init__(self):
		self.tc = ctypes.cdll.LoadLibrary('./ici9000Pythonlib_v2.so') 
		self.tc.loadCal.argtypes = [ctypes.c_char_p]
		self.tc.startCam()
		self.tc.loadCal("./Cal".encode())
