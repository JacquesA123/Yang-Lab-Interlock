#!/usr/bin/env python
import time
import minimalmodbus

__author__  = "Jonas Berg"
__email__   = "pyhys@users.sourceforge.net"
__license__ = "Apache License, Version 2.0"

class Eurotherm3500(minimalmodbus.Instrument):
    def __init__(self, portname, subordinateaddress):
        minimalmodbus.Instrument.__init__(self, portname, subordinateaddress)

    # ---- Read-only functions ----

    def get_pv_loop1(self):
        return self.read_register(289, 1)

    def get_pv_loop2(self):
        return self.read_register(1313, 1)

    def get_pv_module3(self):
        return self.read_register(370, 1)

    def get_pv_module4(self):
        return self.read_register(373, 1)

    def get_pv_module6(self):
        return self.read_register(379, 1)

    def is_manual_loop1(self):
        return self.read_register(273, 1) > 0

    def get_sptarget_loop1(self):
        return self.read_register(2, 1)

    def get_sp_loop1(self):
        return self.read_register(5, 1)

    # def set_sp_loop1(self, value):
    #     self.write_register(24, value, 1)

    def get_sp_loop2(self):
        return self.read_register(1029, 1)

    def get_sprate_loop1(self):
        return self.read_register(35, 1)

    # def set_sprate_loop1(self, value):
    #     self.write_register(35, value, 1)

    def is_sprate_disabled_loop1(self):
        return self.read_register(78, 1) > 0

    # def disable_sprate_loop1(self):
    #     self.write_register(78, 1, 0)

    # def enable_sprate_loop1(self):
    #     self.write_register(78, 0, 0)

    def get_op_loop1(self):
        return self.read_register(85, 1)

    def is_inhibited_loop1(self):
        return self.read_register(268, 1) > 0

    def get_op_loop2(self):
        return self.read_register(1109, 1)

    def get_threshold_alarm1(self):
        return self.read_register(10241, 1)

    def is_set_alarmsummary(self):
        return self.read_register(10213, 1) > 0


########################
## Testing the module ##
########################

if __name__ == '__main__':
    print('TESTING EUROTHERM 3500 MODBUS MODULE')

    a = Eurotherm3500('/dev/tty.usbserial-B0049PNY', 1)
    time.sleep(2)
    a.debug = True

    print('SP1:                    {0}'.format(a.get_sp_loop1()))
    print('SP1 target:             {0}'.format(a.get_sptarget_loop1()))
    print('SP2:                    {0}'.format(a.get_sp_loop2()))
    print('SP-rate Loop1 disabled: {0}'.format(a.is_sprate_disabled_loop1()))
    print('SP1 rate:               {0}'.format(a.get_sprate_loop1()))
    print('OP1:                    {0}%'.format(a.get_op_loop1()))
    print('OP2:                    {0}%'.format(a.get_op_loop2()))
    print('Alarm1 threshold:       {0}'.format(a.get_threshold_alarm1()))
    print('Alarm summary:          {0}'.format(a.is_set_alarmsummary()))
    print('Manual mode Loop1:      {0}'.format(a.is_manual_loop1()))
    print('Inhibit Loop1:          {0}'.format(a.is_inhibited_loop1()))
    print('PV1:                    {0}'.format(a.get_pv_loop1()))
    print('PV2:                    {0}'.format(a.get_pv_loop2()))
    print('PV module 3:            {0}'.format(a.get_pv_module3()))
    print('PV module 4:            {0}'.format(a.get_pv_module4()))
    print('PV module 6:            {0}'.format(a.get_pv_module6()))

    print('DONE!')
