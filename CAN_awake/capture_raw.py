#!/usr/bin/python3

import argparse
import os
import subprocess
import time
import sys
import re

parses=argparse.ArgumentParser()
parses.add_argument('--ip','-i',type=str,required=True)
parses.add_argument('--savepath','-s',type=str,required=True)
parses.add_argument('--lidarport','-l',type=str,required=True)
parses.add_argument('--lisenport','-ls',type=str,required=True)
args=parses.parse_args()


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
    key="sn\d+-\d+-incomplete.inno_raw"
    for file in file_list:
        if re.match(key,file):
            return True
    return False

def delete_util_log(log_path):
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except:
            pass



if __name__=="__main__":
    while True:
        if ping(args.ip,0.3):
            break
    if not os.path.exists(args.savepath):
        os.makedirs(args.savepath)
    i=0
    newest_path=newest_folder(args.savepath,i)
    
    command1=f"exec lidar_util/inno_pc_client --lidar-ip {args.ip} --lidar-port 8010 --lidar-udp-port 8010 --tcp-port {args.lidarport} --udp-port {args.lidarport}"
    command2=f"curl localhost:{args.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
    command3=f"curl {args.ip}:8010/command/?set_faults_save_raw=ffffffffffffffff"
    command4=f"curl localhost:{args.lidarport}/command/?set_save_raw_data={args.lisenport}"
    cmd=subprocess.Popen(command1,shell=True,stdout=open(f"lidar_util/{args.ip}_out",'w'),stderr=open(f"lidar_util/{args.ip}_err",'w'))
    time.sleep(1)
    os.system(command2)
    os.system(command3)
    os.system(command4)
    while 1:
        delete_util_log(f"lidar_util/{args.ip}_out")
        delete_util_log(f"lidar_util/{args.ip}_err")
        delete_util_log(f"lidar_util/inno_pc_client.log")
        delete_util_log(f"lidar_util/inno_pc_client.log.err")
        delete_util_log(f"lidar_util/inno_pc_client.log.1")
        delete_util_log(f"lidar_util/inno_pc_client.log.2")
        if check_raw(os.listdir(newest_path)):
            print(f"record raw data to {os.path.abspath(newest_path)}")
            i+=1
            newest_path=newest_folder(args.savepath,i)
            command2=f"curl localhost:{args.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
            os.system(command2)
            os.system(command3)