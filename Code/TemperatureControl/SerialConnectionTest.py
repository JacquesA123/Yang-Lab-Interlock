import serial
import sys

PORT = '/dev/tty.usbserial-B0049PNY'  # Replace with your actual device name
BAUDRATE = 9600

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=1)
    if ser.is_open:
        print(f"✅ Port {PORT} opened successfully.")
        ser.close()
        print(f"✅ Port {PORT} closed successfully.")
    else:
        print(f"❌ Port {PORT} could not be opened.")
except serial.SerialException as e:
    print(f"❌ Serial error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
