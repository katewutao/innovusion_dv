#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File: run.py
@Time: 2023/05/19 10:35:47
@Author: ZhuLi.Wu
@Mail: gavin.wu@cn.innovusion.com
'''

from can_run import *


def main_close(args):
    conf = load_conf('config/CANFD_Config.json')
    if args.can in ["Default","Robin","FII"]:
        conf["frame"]["send_count"] = 1
        conf["frame"]["type"] = "can"
        conf["frame"]["frame_ID"] = "505"
        conf["frame"]["payload_len"] = 8
        conf["frame"]["payload"] = "0040008000000000"
        os.system("ps -ef|grep can_run.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
        usbcan = usbcanfd.USBCANFD(**conf)
        usbcan.close_device()
        return
    elif args.can=="GF":
        conf["frame"]["type"]="canfd"
        conf["frame"]["frame_ID"]="7f9"
        conf["frame"]["payload"]="000000"
        conf["frame"]["payload_len"]=3
        conf["frame"]["send_count"]=5
    elif args.can=="switch":
        conf["frame"]["type"]="can"
        conf["frame"]["frame_ID"]="701"
        conf["frame"]["payload_len"]=8
        conf["frame"]["payload"]="01"*8
        conf["frame"]["send_count"]=1
        conf['frame']['Baud rate']=250
        conf["device"]["tx_ch"]=1
        time.sleep(5)
    if not conf:
        return
    try:
        assert set_dev_permision(conf['user']['pwd'])
    except AssertionError:
        logger.error('Set dev permision Error!')
        return
    
    usbcan = USBCAN(conf)
    usbcan.run_usbcan()
    if args.can=="switch":
        conf["frame"]["payload"]="0001"*4
        time.sleep(2)
        usbcan = USBCAN(conf)
        usbcan.run_usbcan()
    
    # Block
    # tcp_server(conf)

    # usbcan.stop_usbcan()
    

if __name__ == "__main__":
    import argparse
    parse=argparse.ArgumentParser()
    parse.add_argument("--can","-c",type=str,default="Default",help="CAN type")
    args=parse.parse_args()
    main_close(args)