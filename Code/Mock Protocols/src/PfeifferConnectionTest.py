# Check connection to gauge and pump

import PfiefferVacuumProtocol as pvp
import serial
import RealPfeifferTC110 as rpt
import PfeifferTC110OfficialTest as TC_test

# Open the serial port with a 1 second timeout (timeout time is the amount of time it will wait before moving onto the next line of code)
# If "COM1" doesn’t work, you need to find which COM port is assigned to your USB-to-RS485 adapter.
s = serial.Serial("/dev/tty.usbserial-BG000M8V", baudrate=9600, timeout=1)

# Detect gauges and store their addresses in a list
gauges = {}
# If detected, print the addresses. Else, print("unable to detect gauge ")
# for addr in [0, 22, 32, 100, 111, 121, 122, 123, 131, 132, 133, 200, 211, 221, 222, 223, 231, 232, 233]:
#     try:
#         gauge_type = pvp.read_gauge_type(s, addr)
#         print(f"Detected: {gauge_type} at address: {addr}")
#         gauges.update({gauge_type, addr})
#     except:
#         print(f"unable to detect gauge at address: {addr}")

address = 122
gauge_type = pvp.read_gauge_type(s, address)
print(f"Detected: {gauge_type} at address: {address}")
# gauges.update({gauge_type, 122})
# print(gauges)

# # Detect Vacuum Pump

# Create the pump
try:
    pump = rpt.TC110()
    print(pump)
except:
    print("unable to create pump")

# # If detected, print the address. Else, print("unable to detect pump status")
# # If not working, might need to add another test where I scan all the addresses to see if I get a pump response
# try:
#     pump_status = pump.get_status()
# except:
#     print("unable to get pump status")

# try:
#     TC110_test = TC_test.TestTC110()
# except:
#     print("TC110 test failed")