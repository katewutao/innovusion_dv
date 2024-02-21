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
    "Rel Test Name": "",
    "Rel CP code": "",
    "Rel Leg": "",
    "FPGA_temp": "T0=",
    "Adc_temp": "T1=",
    "Tboard_temp": "T2=",
    "Tlaser_temp": "Tlaser=",
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