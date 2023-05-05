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

# polygon speed,Motor DC bus voltage,Motor RMS current,Motor speed control err,Galvo FPS,Galvo RMS current,Galvo frame counter,Galvo position control err,laser current,unit current,

record_keys = ['TimeStamp','SN','CustomerSN','Rel Test Name','Rel CP code','Rel Leg','T0','T1','T2','Tlaser', 'A=', 'B=', 'C=', 'D=', 'LASER current','pump voltage=','temperature=','seed temperature=','polygon speed:','Board humidity','laser current:','vol', 'curr']
record_header = "TimeStamp,SN,CustomerSN,Rel Test Name,Rel CP code,Rel Leg,FPGA_temp,Adc_temp,Tboard_temp,Tlaser_temp,det_A temp,det_B temp,det_C temp,det_D temp,Pump Laser Current,Pump Voltage,Laser module temperature,Seed Temperature,Polygon Speed,Board humidity,Laser Current,Driving Voltage,Driving Current"

def extract(keys, st):
    import re
    res=[]
    for i in range(len(keys)):
        if "intensity" not in keys[i]:
            ret=re.search(keys[i]+".*?(-?\d+\.?\d*)",st)
            if ret:
                res.append(ret.group(1))
            else:
                res.append(-100)
        else:
            ret=re.search(keys[i]+".*?(\d+).*?(\d+).*?(\d+).*?(\d+)",st)
            if ret:
                for j in range(4):
                    res.append(ret.group(j+1))
            else:
                for j in range(4):
                    res.append(-100)
    return res

def ping(ip,time_interval):
    if 'windows' not in platform.platform().lower():
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

def get_command_result(command,save_log):
    cmd = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.8)
    if cmd.poll() is not None:
        res = str(cmd.stdout.read())
        res1 = 'success'
    else:
        res = ''
        res1 = 'failed'
    cmd.kill()
    write_log(save_log, command, res1)
    return res


def write_log(txt_path, command, res):
    file_txt = open(txt_path, 'a', encoding='utf-8', newline='\n')
    file_txt.write(f'{datetime.datetime.now()}   {command}   {res}\n')
    file_txt.close()


def get_customerid(ip):
    customerid = ''
    import socket
    command = 'mfg_rd "CustomerSN"\n'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 8001))
    s.settimeout(1)
    rert = s.sendall(command.encode())
    try:
        data=s.recv(1024)
        lst = data.decode('ascii').split('\n')
        for string in lst:
            if ':' in string:
                # print(string)
                customerid = string.split(':')[1].split('"')[1]
    except Exception as e:
        print(e)
    s.close()
    return customerid 

def get_sn(ip):
    command=f"curl {ip}:8010/command/?get_sn"
    cmd = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    
    res=cmd.communicate()
    SN=res[0]
    
    #SN=cmd.stdout.read()
    
    return SN 


def csv_write(file, lis):
    if not os.path.exists(file):
        flag=0
    else:
        flag=1
    file_read = open(file, 'a', newline='\n')
    str1 = ''
    for i in range(len(lis)):
        str1+=f'{lis[i]},'
    str1=str1[:-1]
    if flag:
        file_read.write('\n'+str1)
    else:
        file_read.write(str1)
    file_read.close()




def one_record(ip,save_log,SN,CustomerSN,power_csv):
    command = f'curl http://{ip}:8088/get-all-status'
    res = get_command_result(command,save_log)
    temp = [f" {datetime.datetime.now()}",SN,CustomerSN]
    temp+=extract(record_keys[len(temp):-2], res)
    if res=="":
        return None
    while 1:
        try:
            pow = pd.read_csv(power_csv, header=None).values.tolist()
            break
        except:
            continue
    temp.append(pow[0][0])
    temp.append(pow[0][1])
    return temp



def main(ip,record_folder,interval,row_counter,func):
    while True:
        if ping(ip,1):
            break
    ip_name=ip.replace('.', '_')
    save_log=os.path.join(record_folder,f"testlog_{ip_name}.txt")
    save_csv=os.path.join(record_folder,f"record_{ip_name}.csv")
    power_csv=os.path.join(record_folder,'pow_status.csv')
    SN=get_sn(ip)
    CustomerSN=get_customerid(ip)
    if not os.path.exists(save_csv):
        file = open(save_csv, 'w', newline='\n')
        file.write(record_header)
        file.close()
    command = f'curl http://{ip}:8088/get-all-status'
    while True:
        t=time.time()
        res = get_command_result(command,save_log)
        temp = [f" {datetime.datetime.now()}",SN,CustomerSN,'','','']
        temp+=extract(record_keys[len(temp):-2], res)
        if -100 in temp:
            continue
        while 1:
            try:
                pow = pd.read_csv(power_csv, header=None).values.tolist()
                break
            except:
                continue
        temp.append(pow[0][0])
        temp.append(pow[0][1])
        csv_write(save_csv, temp)
        func(row_counter,temp)
        sleep_time=interval-time.time()+t
        if sleep_time>0:
            time.sleep(sleep_time)


if __name__=="__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument('--ip', type=str, required=True, help='lidar ip address')
    parse.add_argument('--interval', type=float, required=True,
                    help='record time interval')
    args = parse.parse_args()
    main(args)
