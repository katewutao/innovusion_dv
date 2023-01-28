# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-01-06 12:48:58
#  * @modify date 2022-09-13 11:39:05
#  * @desc [DV test main ]
#  */
import pexpect
import pandas as pd
import os
import subprocess
import time
import datetime
import re
from oneclient import record_header,csv_write


def ping(ip,interval_time):
    command='ping -c 1 -W 0.15 '+ip
    cmd=subprocess.Popen('exec '+command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(interval_time)
    if cmd.poll() is not None:
        res=cmd.stdout.read().decode('utf-8')
    else:
        res=''
    cmd.kill()
    if "1 received" in res:
        return 1
    else:
        return 0

def ping_sure(ip,interval_time):
    flag=ping(ip,interval_time)
    while flag==0:
        print(f'[{datetime.datetime.now()}]please connect lidar {ip}')
        flag=ping(ip,interval_time)
    print(f'[{datetime.datetime.now()}]lidar {ip} has connected')


def init_power():
    import shutil
    cmd=os.popen("lsusb")
    res=cmd.read()
    if os.path.exists("power.py"):
        os.remove("power.py")
    if "Future Technology Devices International, Ltd FT232 Serial (UART) IC" in res:
        shutil.copyfile(os.path.join(os.getcwd(),"power_DH.py"),os.path.join(os.getcwd(),"power.py"))
    elif "QinHeng Electronics HL-340 USB-Serial adapter" in res:
        shutil.copyfile(os.path.join(os.getcwd(),"power_PY.py"),os.path.join(os.getcwd(),"power.py"))
    else:
        print("power is not PY or DH")
        return False
    return True


def test(times,interval_time,ip_extract,data_num_power_off):
    import power
    for item in times:
        t=time.time()
        while True:
            try:
                pow.power_on()
                df=pd.DataFrame([pow.PowerStatus()])
                break
            except:
                print(f"[{datetime.datetime.now()}]get power permission")
                os.system('sshpass -p demo sudo python3 ./power.py')
                try:
                    pow=power.Power()
                    pow.power_on()
                    df=pd.DataFrame([pow.PowerStatus()])
                    break
                except:   
                    continue
        print(f"[{datetime.datetime.now()}]power on")
        df.to_csv('result/pow_status.csv',header=None,index=None)
        if item[0]>20:
            command='exec python3 power_client.py'
            cmd_pow=subprocess.Popen(command,stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
            cmds=[]
            for i in range(len(ip_extract)):
                command_record=f'exec python3 oneclient.py --ip {ip_extract[i]} --interval {interval_time}'
                cmd=subprocess.Popen(command_record,shell=True,stdout=subprocess.PIPE)
                cmds.append(cmd)
                command_raw=f'exec python3 capture_raw.py -i {ip_extract[i]} -s "result/raw/{ip_extract[i].replace(".","_")}" -l {9100+i} -ls {8100+i}'
                cmd=subprocess.Popen(command_raw,shell=True,stdout=subprocess.PIPE)
                cmds.append(cmd)
                print(f'[{datetime.datetime.now()}]{ip_extract[i]} is record!!')
            time.sleep(item[0])
            for cmd in cmds:
                cmd.kill()
            print(f"[{datetime.datetime.now()}]record has been terminated")
            cmd_pow.kill()
            cmd_pow.wait()
        else:
            for ip in ip_extract:
                for _ in range(data_num_power_off):
                    temp=[str(datetime.datetime.now())]+[-100]*(record_header.count(","))
                    csv_write(os.getcwd()+'/result/record_'+ip.replace('.','_')+'.csv',temp)
        if not os.path.exists(os.getcwd()+'/result/log'):
            os.mkdir(os.getcwd()+'/result/log')
        for ip in ip_extract:
            times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
            file_name=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
            if not os.path.exists(os.getcwd()+'/result/log/ip_'+ip.replace('.','_')):
                os.mkdir(os.getcwd()+'/result/log/ip_'+ip.replace('.','_'))
            if not os.path.exists(os.getcwd()+'/result/log/ip_'+ip.replace('.','_')+'/'+file_name):
                os.mkdir(os.getcwd()+'/result/log/ip_'+ip.replace('.','_')+'/'+file_name)
            command='cd '+os.getcwd()+'/result/log/ip_'+ip.replace('.','_')+';sshpass -p 4920lidar scp -rp root@'+ip+':/tmp ./'+file_name
            cmd=os.popen(command)
            cmd.read()
            cmd.close()
            command='cd '+os.getcwd()+'/result/log/ip_'+ip.replace('.','_')+';sshpass -p 4920lidar scp -rp root@'+ip+':/mnt ./'+file_name
            cmd=os.popen(command)
            cmd.read()
            cmd.close()
        while True:
            try:    
                pow.power_off()
                break
            except:
                print(f"[{datetime.datetime.now()}]get power permission")
                os.system('sshpass -p demo sudo python3 ./power.py')
                try:
                    pow=power.Power()
                    pow.power_off()
                    break
                except:   
                    continue
        print(f"[{datetime.datetime.now()}]power off")
        for i in range(data_num_power_off):
            for ip in ip_extract:
                temp=[str(datetime.datetime.now())]+[-100]*(record_header.count(","))
                csv_write(os.getcwd()+'/result/record_'+ip.replace('.','_')+'.csv',temp)
            t0=(item[0]+item[1]-time.time()+t)/(data_num_power_off-i)
            if t0>0:
                time.sleep(t0)
        print(f'[{datetime.datetime.now()}]current time is {time.time()-t} s')



def dv_test(dict_config):
    interval_time=dict_config["interval_time"]
    data_num_power_off=dict_config["data_num_power_off"]
    timeout_time=dict_config["timeout_time"]
    ip_extract=dict_config["lidar_ip"]
    dict_config=dict_config["time_dict"]
    while not init_power():
        pass
    import power
    if not os.path.exists(os.getcwd()+'/result'):
        os.mkdir(os.getcwd()+'/result')
    print(f"[{datetime.datetime.now()}]get power permission")
    os.system('sshpass -p demo sudo python3 ./power.py')
    os.system("sshpass -p demo sudo chmod 777 lidar_util/inno_pc_client")
    pow=power.Power()
    pow.power_on()
    time.sleep(15)
    for item in ip_extract:
        ping_sure(item,0.2)
    times=[]
    for key in dict_config.keys():
        temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*)",key)
        for i in range(len(temp_times)):
            temp_times[i]=list(temp_times[i])
            for j in range(len(temp_times[i])):
                temp_times[i][j]=float(temp_times[i][j])*60
        times+=temp_times*dict_config[key]
    for i in range(len(ip_extract)):
        cmd='ssh root@'+ip_extract[i]
        print(f'[{datetime.datetime.now()}]get lidar promission: {cmd}')
        child=pexpect.spawn(cmd)
        try:
            child.expect('yes',timeout=timeout_time)
            child.sendline('yes')
            child.expect('password',timeout=timeout_time)
            child.send('4920lidar')
        except:
            pass
        child.close()
    for ip in ip_extract:
        record_file='result/record_'+ip.replace('.','_')+'.csv'
        if not os.path.exists(record_file):
            with open(record_file,"w",newline="\n") as f:
                f.write(record_header)
    get_current_time=time.time()
    test(times,interval_time,ip_extract,data_num_power_off)
    print(f'[{datetime.datetime.now()}]summary time is {(time.time()-get_current_time)/60} min')
    
if __name__=="__main__":
    time_dict={
    "0:90,2:28,2:28,2:28,2:28,2:28,2:148":0,    #通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
    "0:1,1:1":2,
}
    interval_time=5             # 上电时记录时间间隔(s)
    data_num_power_off=10       # 断电时或通电0s空值数量
    timeout_time=5
    dv_test(time_dict,interval_time,data_num_power_off,timeout_time)