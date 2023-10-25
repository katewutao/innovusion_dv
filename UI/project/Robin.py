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
from utils import *



search_keys={
    "TimeStamp": "",
    "SN": "",
    "CustomerSN": "",
    "db_vbias_fb": "db_info.*?db_vbias_fb.*?(-?\d+\.?\d*)",
    "db_vbias_set": "db_info.*?db_vbias_set.*?(-?\d+\.?\d*)",
    
    "error_content": '''content(?:'|"):(?:"|')(.+?)"''',
    "error_code": '''err_code(?:'|"):(-?\d+\.?\d*)''',
    "error_level": '''error_info.*?level(?:'|"):(?:"|')(.+?)(?:"|')''',
    "error_type": '''error_info.*?type(?:'|"):(?:"|')(.+?)(?:"|')''',
    
    "laser_5V": "laser_info.*?laser_5V.*?(-?\d+\.?\d*)",
    "laser_pg": "laser_info.*?laser_pg.*?(-?\d+\.?\d*)",
    "trig_rate": "laser_info.*?trig_rate.*?(-?\d+\.?\d*)",
    "trig_rate_fb": "laser_info.*?trig_rate_fb.*?(-?\d+\.?\d*)",
    
    "motor current": "motor.*?current.*?(-?\d+\.?\d*)",
    "fault_status": "fault_status.*?(-?\d+\.?\d*)",
    "hall_status": "hall_status.*?(-?\d+\.?\d*)",
    "polygon_speed": "polygon_speed.*?(-?\d+\.?\d*)",
    
    "voltage_moni": "input_voltage_moni.*?(-?\d+\.?\d*)",
    "vbat_current": "vbat_current.*?(-?\d+\.?\d*)",
    "vbat_voltage": "vbat_voltage.*?(-?\d+\.?\d*)",
    "voltage_0V85": "voltage_0V85.*?(-?\d+\.?\d*)",
    "voltage_0V9": "voltage_0V9.*?(-?\d+\.?\d*)",
    "voltage_1V1": "voltage_1V1.*?(-?\d+\.?\d*)",
    "voltage_1V2": "voltage_1V2.*?(-?\d+\.?\d*)",
    "voltage_1V8": "voltage_1V8.*?(-?\d+\.?\d*)",
    "voltage_3V3": "voltage_3V3.*?(-?\d+\.?\d*)",
    "restart_counter": "restart_counter.*?(-?\d+\.?\d*)",
    
    "det_temp": "temperature.*?det.*?(-?\d+\.?\d*)",
    "fpga_temp": "temperature.*?fpga.*?(-?\d+\.?\d*)",
    "laser_temp": "temperature.*?laser.*?(-?\d+\.?\d*)",
    "pmic_temp1": "temperature.*?pmic_temp1.*?(-?\d+\.?\d*)",
    "pmic_temp2": "temperature.*?pmic_temp2.*?(-?\d+\.?\d*)",

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



def one_record(ip,save_log,SN,CustomerSN):
    global search_keys
    command = f'http://{ip}:8088/get-lidar-status'
    res = get_curl_result(command,3.5)[0]
    if res=="":
        print(f"{ip} can't connect")
        # return None
    temp = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",SN,CustomerSN]
    temp+=extract(search_keys, res)
    return temp



if __name__=="__main__":
    str1='''
        {"db_info":{"db_vbias_fb":10.195,"db_vbias_set":26.577},

        "error_info":{"content":"no error","err_code":0,"level":"warn","type":"none"},

        "laser_info":{"laser_5V":0.0,"laser_pg":-1,"trig_rate":3356,"trig_rate_fb":3356},

        "motor":{"current":0,"fault_status":8,"hall_status":7,"internal_lock":false,"polygon_speed":0},

        "power_info":{"input_voltage_moni":4.9335,"vbat_current":0.333395698051948,"vbat_voltage":13.722432613054133,"voltage_0V85":0.85175,"voltage_0V9":0.916,"voltage_1V1":1.09825,"voltage_1V2":1.19925,"voltage_1V8":1.79625,"voltage_3V3":3.27325},

        "restart_counter":75,

        "temperature":{"det":25,"fpga":83,"laser":27,"pmic_temp1":75.0,"pmic_temp2":74.75},

        "timestamp":8283611613040,

        "uptime":93600}
'''
    t=time.time()
    print(extract(search_keys,str1))
    print(time.time()-t)