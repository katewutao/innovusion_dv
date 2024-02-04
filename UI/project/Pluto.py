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
from utils import *




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



def one_record(ip,save_log,SN,CustomerSN):
    global search_keys
    command = f'http://{ip}:8088/get-all-status'
    res = get_curl_result(command,3)[0]
    if res=="":
        print(f"{ip} can't connect")
        return None
    temp = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",SN,CustomerSN,"","",""]
    temp+=extract(search_keys, res)
    return temp
