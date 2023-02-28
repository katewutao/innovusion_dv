#!/usr/bin/python3

import argparse
import os
import subprocess
import time,datetime,select
import sys
import re
from oneclient import save_path



def ping(ip,time_interval):
    if 'linux' in sys.platform:
        cmd=subprocess.Popen(f'exec ping -c 1 {ip}',shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(time_interval)
        if cmd.poll() is not None:
            res = cmd.stdout.read().decode('utf-8')
        else:
            res = ''
        cmd.kill()
        if "100%" in res or res=='':
            return False
        else:
            return True
    else:
        cmd=subprocess.Popen(f'ping -n 1 -w 100 {ip}',shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd.wait()
        res = cmd.stdout.read()
        cmd.kill()
        if b"100%" in res:
            return False
        else:
            return True


def newest_folder(A,B):
    newest_path=os.path.join(A,str(B))
    return newest_path

def check_raw(file_list):
    key="sn\d+-\d+.*\.inno_raw$"
    for file in file_list:
        if re.match(key,file):
            return True
    return False

def delete_util_log(log_path):
    log_path=os.path.abspath(log_path)
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except:
            pass


def get_cmd_print(cmd,poll_obj,fault_log_path):
    if poll_obj.poll(0):
        stderr=cmd.stderr.readline().decode("utf-8")
        ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sset",stderr)
        if ret:
            str1=f"[{datetime.datetime.now()}] {args.ip} {ret.group(2)} has been set"
            with open(fault_log_path,"a") as f:
                f.write(str1+"\n")
            print("\033[0;31;40m",str1, "\033[0m")
    stdout=cmd.stdout.readline().decode("utf-8")
    ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sheal",stdout)
    if ret:
        str1=f"[{datetime.datetime.now()}] {args.ip} {ret.group(2)} has been heal"
        with open(fault_log_path,"a") as f:
            f.write(str1+"\n")
        print("\033[1;32m",str1, "\033[0m")



def main(args):
    util_dir="lidar_util"
    util_path=os.path.join(util_dir,"inno_pc_client")
    fault_log_path=os.path.join(save_path,"fault")
    if not os.path.exists(fault_log_path):
        os.makedirs(fault_log_path)
    fault_log_path=os.path.join(fault_log_path,args.ip.replace(".","_")+".txt")
    if not os.path.exists(util_path):
        print(f"file {util_path} not exists!")
        return None
    while True:
        if ping(args.ip,0.3):
            break
    if not os.path.exists(args.savepath):
        os.makedirs(args.savepath)
    i=1
    newest_path=newest_folder(args.savepath,i)
    command1=f"{util_path} --lidar-ip {args.ip} --lidar-port 8010 --lidar-udp-port 8010 --tcp-port {args.lidarport} --udp-port {args.lidarport}"
    command2=f"curl localhost:{args.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
    command3=f"curl {args.ip}:8010/command/?set_faults_save_raw=ffffffffffffffff"
    command4=f"curl localhost:{args.lidarport}/command/?set_save_raw_data={args.lisenport}"
    # cmd=subprocess.Popen(command1,shell=True,stdout=open(os.path.join(util_dir,f"{args.ip}_out"),'w'),stderr=open(os.path.join(util_dir,f"{args.ip}_err"),'w'))
    cmd=subprocess.Popen(command1,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    poll_obj=select.poll()
    poll_obj.register(cmd.stderr,select.POLLIN)
    time.sleep(1)
    os.system(command2)
    os.system(command3)
    os.system(command4)
    raw_count=len(os.listdir(args.savepath))
    while True:
        get_cmd_print(cmd,poll_obj,fault_log_path)
        delete_util_log(os.path.join(util_dir,f"{args.ip}_out"))
        delete_util_log(os.path.join(util_dir,f"{args.ip}_err"))
        delete_util_log(os.path.join(util_dir,"inno_pc_client.log"))
        delete_util_log(os.path.join(util_dir,"inno_pc_client.log.err"))
        delete_util_log(os.path.join(util_dir,"inno_pc_client.log.1"))
        delete_util_log(os.path.join(util_dir,"inno_pc_client.log.2"))
        if not os.path.exists(newest_path):
            print(f"inno_pc_client boot failed!")
            return None
        if check_raw(os.listdir(newest_path)):
            if i>=raw_count:
                print(f"record raw data to {os.path.abspath(newest_path)}")
            i+=1
            newest_path=newest_folder(args.savepath,i)
            command2=f"curl localhost:{args.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
            os.system(command2)
            os.system(command3)

if __name__=="__main__":
    parses=argparse.ArgumentParser()
    parses.add_argument('--ip','-i',type=str,required=True)
    parses.add_argument('--savepath','-s',type=str,required=True)
    parses.add_argument('--lidarport','-l',type=str,required=True)
    parses.add_argument('--lisenport','-ls',type=str,required=True)
    args=parses.parse_args()
    main(args)