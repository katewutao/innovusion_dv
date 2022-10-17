#!/usr/bin/python3

# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-03-22 16:48:51
#  * @modify date 2022-05-05 11:29:29
#  * @desc [description]
#  */


import argparse
import time
import os
import pandas as pd
import subprocess
import datetime

# polygon speed,Motor DC bus voltage,Motor RMS current,Motor speed control err,Galvo FPS,Galvo RMS current,Galvo frame counter,Galvo position control err,laser current,unit current,

save_path = os.path.join(os.getcwd(),'result')



parse = argparse.ArgumentParser()
parse.add_argument('--ip', type=str, required=True, help='lidar ip address')
parse.add_argument('--interval','-i', type=float, required=True,
                   help='record time interval')
arg = parse.parse_args()
record_head = ['time', 'T0', 'T1', 'T2', 'Tlaser', 'Txadc', 'A=', 'B=', 'C=', 'D=', 'SP: ', 'polygon speed:', 'Motor DC bus voltage:', 'Motor RMS current:', 'Motor speed control err:',
               'Galvo FPS:', 'Galvo RMS current:', 'Galvo frame counter:', 'Galvo position control err:', 'laser current:', 'unit current:', 'LASER current', 'temperature']


def extract(key, st):
    import re
    key=f'{key}.*?([-+]?\d+\.?\d*)'
    ret=re.search(key,st)
    if ret:
        if '.' in ret.group(1):
            return float(ret.group(1))
        else:
            return int(ret.group(1))
    return -100
    
def get_sn():
    print(f'now start get {arg.ip} SN')
    command=f'curl {arg.ip}:8010/command/?get_sn'
    res=get_command_result(command)
    while res=='':
        res=get_command_result(command)
    print(f'ip {arg.ip} SN is {res}')
    return res


def get_command_result(command):
    cmd = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.08)
    if cmd.poll() is not None:
        res = str(cmd.stdout.read())
    else:
        res = ''
    cmd.kill()
    if res[:2]=="b'" and res[-1]=="'":
        res=res[2:-1]
    return res


def csv_write(file, lis):
    if not os.path.exists(file):
        record = "time,temp_T0,temp_T1,temp_T2,Tlaser,Txadc,temp_A,temp_B,temp_C,temp_D,motor speed,polygon speed,Motor DC bus voltage,Motor RMS current,Motor speed control err,Galvo FPS,Galvo RMS current,Galvo frame counter,Galvo position control err,laser current,unit current,LASER current,laser temp"
        with open(file, 'w', newline='\n') as f:
            f.write(record)
    flag=0
    for i in range(1,len(lis)):
        if lis[i]!=-100:
           flag=1
           break
    if flag: 
        with open(file, 'a', newline='\n') as f:
            str1 = ''
            for i in range(len(lis)):
                if i != len(lis)-1:
                    str1 = str1+str(lis[i])+','
                else:
                    str1 = str1+str(lis[i])
            f.write('\n'+str1)

def dv_one(ip,save_path):
    command = f'curl http://{ip}:8088/get-all-status'
    res = get_command_result(command)
    temp = [str(datetime.datetime.now())]
    for i in range(1, len(record_head)):
        temp.append(extract(record_head[i], res))
    csv_write(save_path, temp)


if not os.path.exists(save_path):
    os.makedirs(save_path)

save_path=os.path.join(save_path,f'{get_sn()}.csv')

while True:
    t = time.time()
    dv_one(arg.ip,save_path)
    sleep_time = arg.interval-time.time()+t
    if sleep_time > 0:
        time.sleep(sleep_time)
