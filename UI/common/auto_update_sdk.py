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
import requests


def get_curl_result(command,timeout=1):
    excute_flag=False
    try:
        request=requests.get(command,timeout=timeout)
        res=request.text
        request.close()
        excute_flag=True
    except Exception as e:
        res=""
    return res,excute_flag

def download_file(url,filename):
    print(f"download {filename} start")
    try:
        response = requests.get(url)
        response.raise_for_status()
    except:
        print(f"download {filename} failed")
        return
    with open(filename,"wb") as f:
        f.write(response.content)
    print(f"download {filename} success")


def ping(ip,time_interval):
    try:
        respon=requests.get(f"http://{ip}",timeout=time_interval)
        if respon.status_code==200:
            return True
    except:
        pass
    return False

def get_sdk_version(ip):
    key = '(release-.*)'
    command = f'http://{ip}:8010/command/?get_sdk_version'
    res,_=get_curl_result(command)
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

def find_path(file_name,folder):
    for root,_,files in os.walk(folder):
        for file in files:
            if file==file_name:
                return os.path.join(root,file)
    return None


def down_sdk_command(util_names,public_path,command,util_folder,rm_sdk):
    download=True
    if not update_sdk(command, public_path):
        print("download sdk fail")
        return
    if not os.path.exists(util_folder):
        os.makedirs(util_folder)
    for filename in util_names.keys():
        filename=util_names[filename]
        down_path=find_path(filename,public_path)
        util_save_path=os.path.join(util_folder,filename)
        if down_path!=None:
            if os.path.exists(util_save_path):
                os.remove(util_save_path)
            shutil.copyfile(down_path,util_save_path)
        if not os.path.exists(util_save_path):
            download=False
            print(f"find {filename} failed")
    if "linux" in platform.platform().lower():
        for filename in util_names.keys():
            filename=util_names[filename]
            file_path=os.path.join(util_folder,filename)
            if os.path.exists(file_path):
                os.system(f'echo demo|sudo -S chmod 777 "{file_path}"')
    if rm_sdk:
        shutil.rmtree(public_path)
    return download

def down_sdk(ip,sdk_version=None,rm_sdk=True):
    print(f"{ip} start download sdk, please wait")
    if sdk_version==None:
        sdk_version = get_sdk_version(ip)
    if sdk_version!=load_sdk_version():
        ret=re.search("(.*)?-arm", sdk_version)
        if ret:
            sdk_version_no_platform=ret.group(1)
            sdk_version_client=sdk_version_no_platform.replace("release","release-client")
            
        else:
            print(f"{ip} can't find sdk version")
            return False
        public_path = './sdk'
        util_folder = "./lidar_util"
        util_names={"inno_pc_client":"",}
        if os.getenv("project")=="Robin":
            util_names={
                "inno_pc_client":"",
                "innovusion_lidar_util":""
                        }
            sdk_version_client = "release-client-sdk-3.0.12"
        else:
            util_names={
                "innovusion_lidar_util":"",
                "get_pcd":"",
                "inno_pc_client":"",
                "inno_pc_server":"",
                }
        if "linux" in platform.platform().lower():
            for filename in util_names.keys():
                util_names[filename]=filename
            command = f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_no_platform}/inno-lidar-sdk-{sdk_version_no_platform}-public.tgz" -o katewutao.tgz'
            command_client=f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_client}/inno-lidar-sdk-{sdk_version_client}-public.tgz" -o katewutao.tgz'
        elif "windows" in platform.platform().lower():
            for filename in util_names.keys():
                util_names[filename]=f"{filename}.exe"
            command = f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_no_platform}/inno-lidar-sdk-{sdk_version_no_platform}-mingw64-public.tgz" -o katewutao.tgz'
            command_client=f'curl "https://s3-us-west-2.amazonaws.com/iv-release/release/TAG/{sdk_version_client}/inno-lidar-sdk-{sdk_version_client}-mingw64-public.tgz" -o katewutao.tgz'
        else:
            return False
        down_flag=True
        if not down_sdk_command(util_names,public_path,command,util_folder,rm_sdk):
            down_flag=down_sdk_command(util_names,public_path,command_client,util_folder,rm_sdk)
        if down_flag:
            write_sdk_version(sdk_version)
        return True
if __name__=="__main__":
    os.environ["project"]="Robin"
    down_sdk("172.168.1.10",None,False)
    # down_sdk("172.168.1.10")