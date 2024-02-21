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
from utils.ConvertPcd import *



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

pointcloud_header = ["Timestamp","PPS"]
channel_max = 32
config = load_pointcloud_yaml()
pointcloud_bds ={}
for area in config.keys():
    for i in range(channel_max):
        pointcloud_header.append(f"INT_{i}_{area}")
    pointcloud_header.append(f"ACC_{area}")
    pointcloud_header.append(f"PRE_{area}")
    pointcloud_bds[area] = {}
    for ip in config[area].keys():
        try:
            pointcloud_bds[area][ip] = {
                    "bds":[config[area][ip]["x_min"],config[area][ip]["x_max"],config[area][ip]["y_min"],config[area][ip]["y_max"],config[area][ip]["z_min"],config[area][ip]["z_max"]],
                    "gt_distance":config[area][ip]["gt_distance"],
                }
        except:
            print(f"pointcloud config error: {area} {ip} format error")


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

def pointcloud_analyze(df,ip,pcd_save_path):
    res = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"]
    res.append(df.shape[0])
    df["channel"] = df["scanline"]-df["facet"]*channel_max
    
    if "intensity" not in df.columns:
        if "elongation" in df.columns:
            df["intensity"] = df["elongation"]
    for area in pointcloud_bds.keys():
        if ip not in pointcloud_bds[area].keys():
            res += ["NaN"]*(channel_max+2)
        else:
            bds = pointcloud_bds[area][ip]["bds"]
            df_bds = PointCloud(df).filter_box(bds)
            if df_bds.shape[0]==0:
                res += ["NaN"]*(channel_max+2)
                continue
            df2pcd(df_bds,os.path.join(pcd_save_path,f"{ip}_{area}.pcd"))
            for i in range(channel_max):
                df_channel = df_bds[df_bds["channel"]==i]
                if df_channel.shape[0]==0 or "intensity" not in df_channel.columns:
                    res.append("NaN")
                else:
                    res.append(round(float(df_channel["intensity"].mean()),3))
            acc = PointCloud().calc_acc(df_bds,pointcloud_bds[area][ip]["gt_distance"])
            pre = PointCloud().calc_pre(df_bds)
            res.append(acc)
            res.append(pre)
    return res




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