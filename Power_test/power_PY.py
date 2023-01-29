#!/usr/bin/python3




# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-03-22 16:48:51
#  * @modify date 2022-03-22 16:48:51
#  * @desc [description]
#  */
import time
import serial
from serial.tools import list_ports
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu
import os

class Power(object):
    def __init__(self):
        self.com = None
        if self.com is None:
            port_lists = list(list_ports.comports())
            for index, i in enumerate(port_lists):
                 if 'Serial' in i.description:
                     self.com = port_lists[int(index)][0]
                     break

    def power_off(self):
        master = modbus_rtu.RtuMaster(serial.Serial(self.com, 9600, 8, 'N', 1))
        master.set_timeout(2.0)
        master.set_verbose(True)
        master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 2016, output_value=[0])  # output off
        result = master.execute(1, cst.READ_INPUT_REGISTERS, 1007, 1)  # get status register
        power = int(result[0]) & 1
        if power == 0:
            #print("The PS output is off normally.")
            time.sleep(8)
            result = master.execute(1, cst.READ_INPUT_REGISTERS, 1000, 2)  # get voltage & current
            vol = float(int(result[0]) / 100)
            cur = float(int(result[1]) / 100)
            #print("The read output voltage is: %.2f and current is：%.2f." % (vol, cur))
        else:
            print("Error! The PS output off failed.")

        #print("Now start waiting after power off......")
        return 0

    def power_on(self):
        #print("Now start waiting before power on......")
        master = modbus_rtu.RtuMaster(serial.Serial(self.com, 9600, 8, 'N', 1))
        master.set_timeout(2.0)
        master.set_verbose(True)

        # set output voltage=13.50V, current=10.00A
        master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 2021, output_value=[1400, 3000])

        result = master.execute(1, cst.READ_HOLDING_REGISTERS, 2001, 2)  # get the vol & current of setting
        vol = float(int(result[0]) / 100)
        cur = float(int(result[1]) / 100)
        #print("The setting voltage is: %.2f and current is：%.2f." % (vol, cur))

        master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 2016, output_value=[65535])  # output on
        result = master.execute(1, cst.READ_INPUT_REGISTERS, 1007, 1)  # get status register
        power = int(result[0]) & 1  # power[0]: 0-output off, 1-output on
        if power == 1:
            #print("The PS output is power on normally.")
            result = master.execute(1, cst.READ_INPUT_REGISTERS, 1000, 2)  # get output voltage & current
            vol = float(int(result[0]) / 100)
            cur = float(int(result[1]) / 100)
            #print("The PS output voltage is: %.2f and current is：%.2f." % (vol, cur))
        else:
            print("Error! The PS output on failed!")

        #print("Now start waiting while PS powers on......")
        return 0
    
    def PowerStatus(self):
        master = modbus_rtu.RtuMaster(serial.Serial(self.com, 9600, 8, 'N', 1))
        master.set_timeout(2.0)
        master.set_verbose(True)
        result = master.execute(1, cst.READ_INPUT_REGISTERS, 1007, 1)  # get status register
        power = int(result[0]) & 1  # power[0]: 0-output off, 1-output on
        if power == 1:
            #print("The PS output is power on normally.")
            result = master.execute(1, cst.READ_INPUT_REGISTERS, 1000, 2)  # get output voltage & current
            # vol = float(int(result[0]) / 100)
            # cur = float(int(result[1]) / 100)
            # print("The PS output voltage is: %.2f and current is：%.2f." % (vol, cur))
        else:
            print("Error! The PS output on failed!")
        return result
if __name__=='__main__':
    pow=Power()
    try:
        os.system('chmod 777 '+pow.com)
    except:
        pass
    #pow.power_off()
    time.sleep(3)
    pow.power_on()
