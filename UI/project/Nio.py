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
    "time": "",
    "SN": "",
    "CustomerSN": "",
    "temp_fpga": "T0=",
    "temp_chip": "Chip=",
    "temp_adc": "T1=",
    "temp_board": "T2=",
    "Temp_laser": "Tlaser=",
    "temp_A": "A=",
    "temp_B": "B=",
    "temp_C": "C=",
    "temp_D": "D=",
    "motor speed": "SP: ",
    "Pump_laser_current": "LASER current",
    "pump_voltage": "pump voltage=",
    "laser_module_temperature": "temperature=",
    "seed_temperature": "seed temperature=",
    "polygon_speed": "polygon speed:",
    "Motor_DC_bus_voltage": "Motor DC bus voltage:",
    "Motor_RMS_current": "Motor RMS current:",
    "Motor_speed_control_err": "Motor speed control err:",
    "Galvo_FPS": "Galvo FPS:",
    "Galvo_RMS_current": "Galvo RMS current:",
    "Galvo_frame_counter": "Galvo frame counter:",
    "Galvo_position_control_err": "Galvo position control err:",
    "Board humidity": "Board humidity",
    "laser_module_current": "laser current:",
    "unit_current": "unit current:",
    "laser_temp": "temperature",
    "pump_st": "pump_st",
    "alarm": "alarm",
    "CHA_ref": "get-ref-intensity",
    "CHB_ref": "get-ref-intensity",
    "CHC_ref": "get-ref-intensity",
    "CHD_ref": "get-ref-intensity",
    "CHA_fpga": "get-fpga-intensity",
    "CHB_fpga": "get-fpga-intensity",
    "CHC_fpga": "get-fpga-intensity",
    "CHD_fpga": "get-fpga-intensity",
    "SQI": "get-sqi\"",
    "vol": "",
    "curr": ""
}

record_header=",".join(search_keys.keys())

pointcloud_header = ["Timestamp","PPS"]
channel_max = 4
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
    res = get_curl_result(command,1.5)[0]
    if res=="":
        print(f"{ip} can't connect")
    #     return None
    temp = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}",SN,CustomerSN]
    temp+=extract(search_keys, res)
    return temp

def pointcloud_analyze(df,ip,pcd_save_path):
    res = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"]
    res.append(df.shape[0])
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