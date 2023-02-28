#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-01-05 13:32:52
#  * @modify date 2022-02-25 15:38:15
#  * @desc [description]
#  */

import os
import sys
import re
import time
import subprocess
import shutil
import json
import platform


def ping(ip, time_interval):
    if 'linux' in sys.platform:
        cmd = subprocess.Popen(f'echo "demo"|sudo -S ping -c 1 {ip}',
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        time.sleep(time_interval)
        if cmd.poll() is not None:
            res = cmd.stdout.read().decode('utf-8')
        else:
            res = ''
        cmd.kill()
        if "100%" in res or res == '':
            return False
        else:
            return True
    else:
        cmd = subprocess.Popen(f'echo "demo"|sudo -S ping -n 1 -w 100 {ip}',
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        cmd.wait()
        res = cmd.stdout.read()
        cmd.kill()
        if b"100%" in res:
            return False
        else:
            return True


def get_sdk_version(ip):
    command = f'curl "http://{ip}:8010/command/?get_sdk_version"'
    cmd = os.popen(command)
    res = cmd.read()
    # key = '(release-[0-9.]+-rc[0-9a-zA-Z]+)'
    key = '(release-.*)'
    ret = re.search(key, res)
    if ret:
        return ret.group(1)
    else:
        return ''


def update_sdk(command, save_path):
    if os.path.exists("katewutao.tgz"):
        os.remove("katewutao.tgz")
    os.system(command)
    if os.path.exists(save_path):
        shutil.rmtree(save_path)
    os.makedirs(save_path)
    cmd=subprocess.Popen(f'tar -xvf katewutao.tgz -C {save_path}',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    res=cmd.communicate()
    cmd.wait()
    res=str(res[1],"utf-8")
    if os.path.exists("katewutao.tgz"):
        os.remove("katewutao.tgz")
    if "tar: Error is not recoverable: exiting now" in res:
        return False
    return True

def get_ip():
    ip_list = [
        '10.42.0.91',
        '172.168.1.10',
    ]
    for item in ip_list:
        if ping(item, 0.2):
            return item
    return None

def load_sdk_version():
    sdk_version_file="sdk.version"
    if os.path.exists(sdk_version_file):
        with open(sdk_version_file,"r") as f:
            sdk_version=json.load(f)
            return sdk_version["sdk_version"]
    else:
        return ""

def write_sdk_version(sdk_version):
    sdk_version_file="sdk.version"
    res={"sdk_version":sdk_version}
    str1=json.dumps(res)
    with open(sdk_version_file,"w") as f:
        f.write(str1)


def down_sdk(ip):
    sdk_version = get_sdk_version(ip)
    if sdk_version!=load_sdk_version():
        ret=re.search("(.*)?-arm", sdk_version)
        if ret:
            sdk_version_no_platform=ret.group(1)
        public_path = './scripts/common/sdk'
        #download public
        if "linux" in platform.platform().lower():
            command = f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_no_platform}/inno-lidar-sdk-{sdk_version_no_platform}-public.tgz" -o katewutao.tgz'
            if not update_sdk(command, public_path):
                command = f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_no_platform}/inno-lidar-sdk-{sdk_version}-public.tgz" -o katewutao.tgz'
                update_sdk(command, public_path)
        client_name="inno_pc_client"
        client_path_down=os.path.join(public_path,"apps/pcs/",client_name)
        client_path_current=f"./lidar_util/{client_name}"
        if os.path.exists(client_path_down):
            if os.path.exists(client_path_current):
                os.remove(client_path_current)
            shutil.copyfile(client_path_down,client_path_current)
            if "linux" in platform.platform().lower():
                os.system(f"echo demo|sudo -S chmod 777 {client_path_current}")
            write_sdk_version(sdk_version)
            shutil.rmtree(public_path)