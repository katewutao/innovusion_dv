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




search_keys={
    "TimeStamp": "",
    "SN": "",
    "CustomerSN": "",
    "Rel Test Name": "",
    "Rel CP code": "",
    "Rel Leg": "",
    "FPGA_temp": "T0",
    "Adc_temp": "T1",
    "Tboard_temp": "T2",
    "Tlaser_temp": "Tlaser",
    "det_A temp": "A=",
    "det_B temp": "B=",
    "det_C temp": "C=",
    "det_D temp": "D=",
    "Pump Laser Current": "LASER current",
    "Pump Voltage": "pump voltage=",
    "Laser module temperature": "temperature=",
    "Seed Temperature": "seed temperature=",
    "Polygon Speed": "polygon speed:",
    "Board humidity": "Board humidity",
    "Laser Current": "laser current:",
    "SQI": "get-sqi\"",
    "Driving Voltage": "",
    "Driving Current": ""
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
                    res.append("NaN")
            else:
                ret=re.search(search_keys[key]+".*?(-?\d+\.?\d*)",st)
                if ret:
                    res.append(ret.group(1))
                else:
                    res.append("NaN")
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
    try: 
        cmd.wait(0.5)
        res = str(cmd.stdout.read())
    except:
        res=""
    cmd.kill()
    return res



def one_record(ip,save_log,SN,CustomerSN):
    global search_keys
    if "windows" not in platform.platform().lower():
        command = f'exec curl -s http://{ip}:8088/get-all-status'
    else:
        command = f'curl -s http://{ip}:8088/get-all-status'
    res = get_command_result(command,save_log)
    if res=="":
        return None
    temp = [f" {datetime.datetime.now()}",SN,CustomerSN,"","",""]
    temp+=extract(search_keys, res)
    return temp
