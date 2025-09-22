import minimalmodbus
import time

# Initialize instrument
for i in range(100):
    eurotherm = minimalmodbus.Instrument('/dev/tty.usbserial-B0049PNY', i)  # port name, slave address
    
    # Configure Modbus settings
    eurotherm.serial.baudrate = 19200
    eurotherm.serial.parity   = minimalmodbus.serial.PARITY_NONE
    eurotherm.serial.stopbits = 1
    eurotherm.serial.timeout  = 0.2  # seconds
    
    eurotherm.mode = minimalmodbus.MODE_RTU
    
    try:
        # Read register 1 (PV Loop1), 1 decimal place
        raw_value = eurotherm.read_register(4, 1)  # register, number of decimals
        print(f"✅ Temperature (PV1): {raw_value:.1f} °C")
    
    except Exception as e:
        print(f"❌ Error reading from Eurotherm: {e}")
