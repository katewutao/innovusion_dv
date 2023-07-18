#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File: Untitled-1
@Time: 2022/07/08 19:23:04
@Author: ZhuLi.Wu
@Mail: gavin.wu@cn.innovusion.com
'''

import sys
import os
import subprocess as sp

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"[Error] Useage: {sys.argv[0]} local_user_password!!")
        sys.exit(1)
    
    # install libusb-1.0-0
    install_cmd = f"echo {sys.argv[1]} | sudo -S apt-get install libusb-1.0-0"
    install_ret = os.system(install_cmd)
    try:
        assert not install_ret
    except AssertionError:
        print("[ERROR]Install driver fail.")
        sys.exit(1)
    if not install_ret:
        cmd = "lsusb | grep '3068:0009' |grep -v grep |awk '{print$2,$4}'"
        sub = sp.Popen(cmd, shell=True, stdout=sp.PIPE, encoding='utf-8')
        sub.wait()
        ret_id = sub.communicate()[0]
        try:
            assert ret_id
        except AssertionError:
            print("[ERROR]Get USBCANFD device fail.")
            sys.exit(1)
        bus_id, device_id = ret_id.strip(':\n').split()

        # modify USBCANFD device permission
        modify_cmd = f"echo {sys.argv[1]} | sudo -S chmod 666 /dev/bus/usb/{bus_id}/{device_id}"
        modify_ret = os.system(modify_cmd)

    