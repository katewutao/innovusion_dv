#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
from serial.tools import list_ports
import serial
import os
from time import sleep

# DEV_COM = "COM3"    # windows
# DEV_COM = "/dev/ttyACM0"    # linux
# BUFFER_LEN = 1024
# remotcmd = '*RST'
# restcmd = '*CLS'
# psoncmd = 'OUTP 1'
# psoffcmd = 'OUTP 0'
# getsncmd = '*IDN?'
# errcmd = 'SYST: ERR?'

# getvolcmd = 'VOLT?'
# getcurcmd = 'CURR?'
# setvolcmd = 'VOLT '
# setcurcmd = 'CURR '



class Power(object):
    def __init__(self, timeout=0.2, stop=1, baudrate=115200, reset=False):
        self.BUFFER_LEN = 1024
        self.remotcmd = '*RST'
        self.restcmd = '*CLS'
        self.psoncmd = 'OUTP 1'
        self.psoffcmd = 'OUTP 0'
        self.getsncmd = '*IDN?'
        self.errcmd = 'SYST: ERR?'
        self.getvolcmd = 'MEASure:VOLTage?'
        self.getcurcmd = 'MEASure:CURRent?'
        self.setvolcmd = 'VOLT '
        self.setcurcmd = 'CURR '
        port_lists = list(list_ports.comports())
        for index, i in enumerate(port_lists):
            if 'Serial' in i.description or 'UART' in i.description:
                port = port_lists[int(index)][0]
                break
        self.port=port
        self.com = serial.Serial(port, timeout=timeout, stopbits=stop, baudrate=baudrate)

    def send(self, cmd):
        if not cmd.endswith("\n"):
            cmd += "\n"
        return self.com.write(cmd.encode())

    def get_result(self, cmd, decode=True):
        self.send(cmd)
        echo = self.com.read(self.BUFFER_LEN)
        if decode:
            try:
                # try to decode to utf8
                echo = echo.decode()
                # try to decode to float
                echo = float(echo)
            except:
                pass
        return echo

    def reset(self):
        #print('reset connection with power')
        self.send(self.restcmd)
        sleep(1)
        self.send(self.remotcmd)
        sleep(1)
        #print('Power connect')

    def close(self):
        return self.com.close()

    def power_on(self):
        self.send(self.psoncmd)
        #print('Set power ON')

    def power_off(self):
        self.send(self.psoffcmd)
        #print('Set power OFF')

    def get_powersts(self):
        cur = self.get_result(self.getcurcmd)
        volt = self.get_result(self.getvolcmd)
        if cur > 0.2 and volt > 0.5:
            sts = True
            #print('Power status is ON')
        else:
            sts = False
            #print('Power status is OFF')
        return sts

    def set_voltage(self, V):
        self.send(self.setvolcmd+str(V))
        #print('Set voltage {}V'.format(V))

    def set_current(self, A):
        self.send(self.setcurcmd + str(A))
        #print('Set max current {}A'.format(A))

    def get_voltage(self):
        volt = self.get_result(self.getvolcmd)
        #print("Power voltage is : {}V".format(volt))
        return volt

    def get_current(self):
        cur = self.get_result(self.getcurcmd)
        #print("Power current is : {}A".format(cur))
        return cur
    def PowerStatus(self):
        return [self.get_voltage(),self.get_current()]


if __name__ == "__main__":
    powerdev = Power()    # reset and set remote mode
    try:
        os.system('chmod 777 '+powerdev.port)
    except:
        pass
    powerdev.power_off()
    powerdev.set_voltage(14)
    powerdev.set_current(360/14)
    sleep(2)
    powerdev.power_on()    # power on