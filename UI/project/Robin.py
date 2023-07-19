#!/usr/bin/python3

# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-03-22 16:48:51
#  * @modify date 2022-11-15 13:36:53
#  * @desc [description]
#  */


import time
import os
import subprocess
import datetime,platform




search_keys={
    "TimeStamp": "",
    "SN": "",
    "CustomerSN": "",
    "FPGA_temp": "T0.*?(\d+\.?\d*)",
    "Adc_temp": "T1.*?(\d+\.?\d*)",
    "Tboard_temp": "T2.*?(\d+\.?\d*)",
    "Tlaser_temp": "Tlaser.*?(\d+\.?\d*)",
    "det_A temp": "A=.*?(\d+\.?\d*)",
    "det_B temp": "B=.*?(\d+\.?\d*)",
    "det_C temp": "C=.*?(\d+\.?\d*)",
    "det_D temp": "D=.*?(\d+\.?\d*)",
    "Pump Laser Current": "LASER current.*?(\d+\.?\d*)",
    "Pump Voltage": "pump voltage=.*?(\d+\.?\d*)",
    "Laser module temperature": "temperature=.*?(\d+\.?\d*)",
    "Seed Temperature": "seed temperature=.*?(\d+\.?\d*)",
    "Polygon Speed": "polygon speed:.*?(\d+\.?\d*)",
    "Board humidity": "Board humidity.*?(\d+\.?\d*)",
    "Laser Current": "laser current:.*?(\d+\.?\d*)",
    "SQI": "get-sqi\"",
    "Driving Voltage": "",
    "Driving Current": ""
}

record_header=",".join(search_keys.keys())

def extract(search_keys, str1):
    import re
    res=[]
    for key in search_keys.keys():
        if search_keys[key]!="":
            ret=re.search(search_keys[key],str1)
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
    command = f'exec curl -s http://{ip}:8088/get-all-status'
    res = get_command_result(command,save_log)
    if res=="":
        return None
    temp = [f" {datetime.datetime.now()}",SN,CustomerSN]
    temp+=extract(search_keys, res)
    return temp
