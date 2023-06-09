#!/usr/bin/python3

# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-03-22 16:48:51
#  * @modify date 2022-11-15 13:36:53
#  * @desc [description]
#  */


import argparse
import time
import os
import pandas as pd
import subprocess
import datetime,platform

# polygon speed,Motor DC bus voltage,Motor RMS current,Motor speed control err,Galvo FPS,Galvo RMS current,Galvo frame counter,Galvo position control err,laser current,unit current,

search_keys={
    "TimeStamp": "",
    "FPGA_temp": "T0",
    "Adc_temp": "T1",
    "Tboard_temp": "T2",
    "Tlaser_temp": "Tlaser",
    "det_A temp": "A=",
    "det_B temp": "B=",
    "det_C temp": "C=",
    "det_D temp": "D=",
    "Laser module temperature": "temperature=",
    "Seed Temperature": "seed temperature=",
    "Pump Laser Current": "LASER current",
    "Laser Current": "laser current:",
    "Polygon Speed": "polygon speed:",
    "Galvo_FPS": "Galvo FPS:",
    "SQI": "get-sqi\""
}

record_header=",".join(search_keys.keys())


def extract(search_keys, st):
    import re
    res=[]
    for key in search_keys.keys():
        if search_keys[key]!="":
            if re.search("^CH([A|B|C|D])_",key) and re.search("intensity$",search_keys[key]):
                ret=re.search(search_keys[key]+".*?(\d+).*?(\d+).*?(\d+).*?(\d+)",st)
                CH_idx=ord(re.search("^CH([A|B|C|D])_",key).group(1))-ord("A")
                if ret:
                    res.append(ret.group(CH_idx+1))
                else:
                    res.append(-100)
            else:
                ret=re.search(search_keys[key]+".*?(-?\d+\.?\d*)",st)
                if ret:
                    res.append(ret.group(1))
                else:
                    res.append(-100)
    return res

def csv_write(file, lis):
    if not os.path.exists(file):
        str1 = ""
    else:
        str1 = '\n'
    for i in range(len(lis)):
        str1+=f'{lis[i]},'
    str1=str1[:-1]
    with open(file, 'a', newline='\n') as f:
        f.write(str1)

def get_command_result(command,save_log):
    cmd = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.8)
    if cmd.poll() is not None:
        res = str(cmd.stdout.read())
        res1 = 'success'
    else:
        res = ''
        res1 = 'failed'
    cmd.kill()
    # write_log(save_log, command, res1)
    return res



def one_record(ip,save_log,SN,CustomerSN):
    global search_keys
    command = f'curl http://{ip}:8088/get-all-status'
    res = get_command_result(command,save_log)
    temp = [f" {datetime.datetime.now()}"]
    temp+=extract(search_keys, res)
    return temp