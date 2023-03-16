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

save_path = os.getcwd()+'/result/'
record_keys = ['time','SN','CustomerSN','T0', 'T1', 'T2', 'Tlaser', 'A=', 'B=', 'C=', 'D=', 'SP: ', 'LASER current','pump voltage=','temperature=','seed temperature=','polygon speed:', 'Motor DC bus voltage:', 'Motor RMS current:', 'Motor speed control err:',
               'Galvo FPS:', 'Galvo RMS current:', 'Galvo frame counter:', 'Galvo position control err:', 'laser current:', 'unit current:', 'temperature', 'pump_st', 'alarm','get-ref-intensity','get-fpga-intensity','vol', 'curr']
record_header = "time,SN,CustomerSN,Temp_fpga,temp_adc,temp_board,Temp_laser,temp_A,temp_B,temp_C,temp_D,motor speed,Pump_laser_current,pump_voltage,laser_module_temperature,seed_temperature,polygon_speed,Motor_DC_bus_voltage,Motor_RMS_current,Motor_speed_control_err,Galvo_FPS,Galvo_RMS_current,Galvo_frame_counter,Galvo_position_control_err,laser_module_current,unit_current,laser_temp,pump_st,alarm,CHA_ref,CHB_ref,CHC_ref,CHD_ref,CHA_fpga,CHB_fpga,CHC_fpga,CHD_fpga,vol,curr"


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


def get_command_result(command,save_log):
    cmd = subprocess.Popen(command, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(0.5)
    if cmd.poll() is not None:
        res = str(cmd.stdout.read())
        res1 = 'success'
    else:
        res = ''
        res1 = 'failed'
    cmd.kill()
    write_log(save_log, command, res1)
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



def write_log(txt_path, command, res):
    file_txt = open(txt_path, 'a', encoding='utf-8', newline='\n')
    file_txt.write(f'{datetime.datetime.now()}   {command}   {res}\n')
    file_txt.close()


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


def main(arg):
    while True:
        if ping(arg.ip,1):
            break
    ip_name=arg.ip.replace('.', '_')
    save_log=os.path.join(save_path,f"testlog_{ip_name}.txt")
    save_csv=os.path.join(save_path,f"record_{ip_name}.csv")
    power_csv=os.path.join(save_path,'pow_status.csv')
    if not os.path.exists(save_csv):
        file = open(save_csv, 'w', newline='\n')
        file.write(record_header)
        file.close()
    command = f'curl http://{arg.ip}:8088/get-all-status'
    SN=get_sn(arg.ip)
    CustomerSN=get_customerid(arg.ip)
    while True:
        t=time.time()
        res = get_command_result(command,save_log)
        temp = [datetime.datetime.now(),SN,CustomerSN]
        temp+=extract(record_keys[len(temp):-2], res)
        if res=="":
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
        sleep_time=arg.interval-time.time()+t
        if sleep_time>0:
            time.sleep(sleep_time)




if __name__=="__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument('--ip', type=str, required=True, help='lidar ip address')
    parse.add_argument('--interval', type=float, required=True,
                    help='record time interval')
    args = parse.parse_args()
    main(args)
    
