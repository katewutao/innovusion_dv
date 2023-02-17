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
import datetime

# polygon speed,Motor DC bus voltage,Motor RMS current,Motor speed control err,Galvo FPS,Galvo RMS current,Galvo frame counter,Galvo position control err,laser current,unit current,

save_path = os.getcwd()+'/result/'
record_keys = ['time', 'T0', 'T1', 'T2', 'Tlaser', 'Txadc', 'A=', 'B=', 'C=', 'D=', 'SP: ', 'LASER current','pump voltage=','temperature=','seed temperature=','polygon speed:', 'Motor DC bus voltage:', 'Motor RMS current:', 'Motor speed control err:',
               'Galvo FPS:', 'Galvo RMS current:', 'Galvo frame counter:', 'Galvo position control err:', 'laser current:', 'unit current:', 'temperature', 'pump_st', 'alarm','get-ref-intensity','get-fpga-intensity','vol', 'curr']
record_header = "time,temp_board,temp_adc1,temp_adc2,Temp_laser,Temp_fpga,temp_A,temp_B,temp_C,temp_D,motor speed,Pump_laser_current,pump_voltage,laser_module_temperature,seed_temperature,polygon_speed,Motor_DC_bus_voltage,Motor_RMS_current,Motor_speed_control_err,Galvo_FPS,Galvo_RMS_current,Galvo_frame_counter,Galvo_position_control_err,laser_module_current,unit_current,laser_temp,pump_st,alarm,CHA_ref,CHB_ref,CHC_ref,CHD_ref,CHA_fpga,CHB_fpga,CHC_fpga,CHD_fpga,vol,curr"

def extract(keys, st):
    import re
    res=[]
    for i in range(len(keys)):
        if "intensity" not in keys[i]:
            ret=re.search(keys[i]+".*?(-?\d+\.?\d*)",st)
            if ret and "." in ret.group(1):
                res.append(float(ret.group(1)))
            elif ret and "." not in ret.group(1):
                res.append(int(ret.group(1)))
            else:
                res.append(-100)
        else:
            ret=re.search(keys[i]+".*?(\d+).*?(\d+).*?(\d+).*?(\d+)",st)
            if ret:
                for j in range(4):
                    res.append(int(ret.group(j+1)))
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

if __name__=="__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument('--ip', type=str, required=True, help='lidar ip address')
    parse.add_argument('--interval', type=float, required=True,
                    help='record time interval')
    arg = parse.parse_args()
    ip_name=arg.ip.replace('.', '_')
    save_log=os.path.join(save_path,f"testlog_{ip_name}.txt")
    save_csv=os.path.join(save_path,f"record_{ip_name}.csv")
    power_csv=os.path.join(save_path,'pow_status.csv')
    if not os.path.exists(save_csv):
        file = open(save_csv, 'w', newline='\n')
        file.write(record_header)
        file.close()
    command = f'curl http://{arg.ip}:8088/get-all-status'
    while True:
        t=time.time()
        res = get_command_result(command,save_log)
        temp = [datetime.datetime.now()]
        temp+=extract(record_keys[1:-2], res)
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
