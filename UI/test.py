import subprocess
import requests
import pandas as pd
import time
import re
import builtins
import os
import datetime

def get_command_result(command):
    cmd = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res = cmd.communicate()
    cmd.kill()
    return res[0]


builtins.print_origin=print
def rewrite_print():
    def print_res(*args, **kwargs):
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        msg = ' '.join(map(str, args))  # Convert all arguments to strings and join them with spaces
        builtins.print_origin(f"[{current_date}] {msg}", **kwargs)
    return print_res

def set_reboot(ip):
    command = f"http://{ip}:8010/command/?set_reboot=1"
    get_curl_result(command,1)

    
def get_curl_result(command,timeout=0.2):
    excute_flag=False
    try:
        request=requests.get(command,timeout=timeout)
        res=request.text
        request.close()
        excute_flag=True
    except Exception as e:
        res=""
    return res,excute_flag

def ping(ip,time_interval):
    res = False
    respon=None
    try:
        respon=requests.get(f"http://{ip}",timeout=time_interval)
        res = True
    except requests.exceptions.ConnectionError:
        print("sleep 1s")
        time.sleep(1)
    if respon:
        respon.close()
    return res

def ping_sure(ip,interval_time):
    while True:
        if ping(ip,interval_time):
            break
        else:
            print(f"{ip} not connect")
    print(f' lidar {ip} has connected')  

def download_file(url,filename):
    print(f"download {filename} start")
    try:
        response = requests.get(url)
    except:
        print(f"download {filename} failed")
        return
    response.raise_for_status()
    with open(filename,"wb") as f:
        f.write(response.content)
    print(f"download {filename} success")


def download_fw_pcs(ip):
    command_fw=f"http://{ip}:8675/lidar-log.txt"
    command_pcs=f"http://{ip}:8675/inno_pc_server.txt"
    try:
        response = requests.get(command_fw)
        response.raise_for_status()
        res_fw=str(response.content)[2:-1]
    except:
        res_fw=""
    try:
        response = requests.get(command_pcs)
        response.raise_for_status()
        res_pcs=str(response.content)[2:-1]
    except:
        res_pcs=""
    res = (res_fw).split("\\n")
    return res
    
if __name__=="__main__":
    builtins.print=rewrite_print()
    ip = "172.168.1.10"
    i=0
    while True:
        i+=1
        print("start reboot")
        ping_sure(ip,1)
        set_reboot(ip)
        time.sleep(60)
        log = download_fw_pcs(ip)
        with open(f"lidar-log{i}.txt","w") as f:
            f.write("\n".join(log))
        stop_flag = False
        for line in log:
            if re.search("fault id.*from.*26[7|8]",line):
                stop_flag = True
                break
        if stop_flag:
            break
    print("fault has set,test stop")



# print(ping("172.168.1.10",1))
# download_file("http://172.168.1.10:8010/capture/?type=raw_raw&duration=1","1.raw")


# lidar_util/inno_pc_client" --lidar-ip 10.42.0.91 --lidar-port 8010 --lidar-udp-port 9600 --udp-port 9100 --tcp-port 8600
# http://localhost:8600/command/?set_raw_data_save_path=/home/demo/Documents/UI/1111/raw/10_42_0_91/2023_10_23_18_17_04/1
# http://localhost:8600/command/?set_faults_save_raw=ffffffffffffffff
# http://localhost:8600/command/?set_save_raw_data=8100