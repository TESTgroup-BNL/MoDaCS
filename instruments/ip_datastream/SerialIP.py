import serial, socket

target_IP = "10.1.1.158"
target_port = 10000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

ser = serial.Serial('/dev/ttyACM0')  # open serial port
print "Connected to " + ser.name          # check which port was really used

try:
    while(True):
        data = ser.readline()
        print(data)
        sock.sendto(data, (target_IP, target_port))
except Exception as e:
    raise e
finally:
    ser.close()
    sock.close()