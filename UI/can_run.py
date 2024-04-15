#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File: run.py
@Time: 2023/05/19 10:35:47
@Author: ZhuLi.Wu
@Mail: gavin.wu@cn.innovusion.com
'''

import os
import socket
import threading
import json
import subprocess as sp
import time
from core import usbcanfd_controller as usbcanfd
from common import python_logging



def tcp_server(conf):
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock_tcp.bind(('127.0.0.1', 10001))
    sock_tcp.listen(1)
    
    is_exit = False
    while True:
        sock, addr = sock_tcp.accept()
        while True:
            recv_data = sock.recv(1024)
            if not recv_data:
                break
            if 'EXIT_CAN' in recv_data.decode('utf-8'):
                logger.info(f"Recv signal: {recv_data} from {addr}")
                sock.send('Done\n'.encode('utf-8'))
                is_exit = True
                break
            else:
                sock.send('Invalid Command\n'.encode('utf-8'))
        sock.close()

        if is_exit:
            break
    sock_tcp.close()


class USBCAN():
    def __init__(self, conf_file):
        if type(conf_file)==str:
            conf_file = open(conf_file, 'r', encoding='utf-8')
            self.conf = json.load(conf_file)
            conf_file.close()
        elif type(conf_file)==dict:
            self.conf=conf_file
        self.tx_ch = self.conf['device']['tx_ch']
        self.rx_ch = self.conf['device']['rx_ch']
        self.cantype = self.conf['frame']['type']
        self.baud_rate = self.conf['frame']['Baud rate']

    def run_usbcan(self, hostname=None, r=None, wait = False):
        self.usbcan = usbcanfd.USBCANFD(**self.conf)
        if not self.usbcan.open_device():
            return
        # usbcanfd.get_deviceInfo()
        self.usbcan.reset_CAN(self.tx_ch)
        self.usbcan.reset_CAN(self.rx_ch)
        self.usbcan.set_reference(self.tx_ch)
        self.usbcan.set_reference(self.rx_ch)
        self.usbcan.init_CAN(self.tx_ch,self.baud_rate)
        self.usbcan.init_CAN(self.rx_ch,self.baud_rate)
        self.usbcan.start_CAN(self.tx_ch)
        self.usbcan.start_CAN(self.rx_ch)
        if self.cantype == 'canfd':
            th1 = threading.Thread(target=self.usbcan.receive_frame_FD, args=(self.rx_ch, hostname, r))
            th2 = threading.Thread(target=self.usbcan.transmit_frame_FD, args=(self.tx_ch,))
        elif self.cantype == 'can':
            th1 = threading.Thread(target=self.usbcan.receive_frame, args=(self.rx_ch,))
            th2 = threading.Thread(target=self.usbcan.transmit_frame, args=(self.tx_ch,))
        else:
            logger.error('Invalid CAN type.')
            return False
        th1.start()
        th2.start()
        if wait:
            th1.join()
            th2.join()
            self.stop_usbcan()
        return True


    def stop_usbcan(self):
        self.usbcan.exit_send.value = False
        self.usbcan.exit_recv.value = True
        
        self.usbcan.reset_CAN(self.tx_ch)
        self.usbcan.reset_CAN(self.rx_ch)
        self.usbcan.close_device()


def load_conf(file):
    try:
        with open(file, 'r') as ff:
            return json.load(ff)

    except Exception as e:
        logger.error('Load configuration fail.')
        return False


def set_dev_permision(pwd):
    # install libusb-1.0-0
    install_cmd = f"echo {pwd} | sudo -S apt-get install libusb-1.0-0"
    install_ret = os.system(install_cmd)
    try:
        assert not install_ret
    except AssertionError:
        logger.error("Install driver fail.")
        return False
    else:
        cmd = "lsusb | grep '3068:0009' |grep -v grep |awk '{print$2,$4}'"
        sub = sp.Popen(cmd, shell=True, stdout=sp.PIPE, encoding='utf-8')
        sub.wait()
        ret_id = sub.communicate()[0]
        try:
            assert ret_id
        except AssertionError:
            logger.error("Get USBCANFD device fail.")
            return False
        else:
            bus_id, device_id = ret_id.strip(':\n').split()

            # modify USBCANFD device permission
            modify_cmd = f"echo {pwd} | sudo -S chmod 666 /dev/bus/usb/{bus_id}/{device_id}"
            os.system(modify_cmd)
            return True


def main(args):
    conf = load_conf('config/CANFD_Config.json')
    if args.can=="Default":
        conf["frame"]["type"]="canfd"  #can or canfd
        conf["frame"]["frame_ID"]="505"
        conf["frame"]["payload"]="0040008000000000"
        conf["frame"]["payload_len"]=8
        conf["frame"]["send_count"]=-1
    elif args.can=="GF":
        conf["frame"]["type"]="canfd"
        conf["frame"]["frame_ID"]="7f9"
        conf["frame"]["payload"]="000011"
        conf["frame"]["payload_len"]=3
        conf["frame"]["send_count"]=5
    elif args.can in ["Robin","FII_Lite"]:
        conf["frame"]["type"]="can"
        conf["frame"]["frame_ID"]="505"
        conf["frame"]["payload_len"]=8
        conf["frame"]["payload"]="0040008000000000"
        conf["frame"]["send_count"]=-1
    elif args.can=="switch": 
        conf["frame"]["type"]="can"
        conf["frame"]["frame_ID"]="701"
        conf["frame"]["payload_len"]=8
        conf["frame"]["payload"]="01"*8
        conf["frame"]["send_count"]=1
        conf['frame']['Baud rate']=250
        conf["device"]["tx_ch"]=1
    if not conf:
        return
    try:
        assert set_dev_permision(conf['user']['pwd'])
    except AssertionError:
        logger.error('Set dev permision Error!')
        return
    
    usbcan = USBCAN(conf)
    if conf["frame"]["send_count"]==-1:
        usbcan.run_usbcan()
        tcp_server(conf)
        usbcan.stop_usbcan()
    else:
        usbcan.run_usbcan(wait=True)
    # Block
        
    

if __name__ == "__main__":
    import argparse
    parse=argparse.ArgumentParser()
    parse.add_argument("--can","-c",type=str,default="Default",help="CAN type")
    parse.add_argument("--can-log","-cl",type=str,default="USBCAN.log",help="CAN type")
    args=parse.parse_args()
    logger = python_logging.my_log(args.can_log, 'w')
    main(args)