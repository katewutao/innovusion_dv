# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-01-06 12:48:58
#  * @modify date 2022-09-13 11:39:05
#  * @desc [DV test main ]
#  */
import pexpect
import power
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

def test(times,interval_time,ip_extract,data_num_power_off):
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



def dv_test(dict_config,interval_time=5,data_num_power_off=10,timeout_time=5):
    if not os.path.exists(os.getcwd()+'/result'):
        os.mkdir(os.getcwd()+'/result')
    print(f"[{datetime.datetime.now()}]get power permission")
    os.system('sshpass -p demo sudo python3 ./power.py')
    os.system("sshpass -p demo sudo chmod 777 lidar_util/inno_pc_client")
    pow=power.Power()
    pow.power_on()
    time.sleep(15)
    ip=pd.read_csv(os.getcwd()+'/IP_CMD_List.csv').values.tolist()
    ip_extract=[ip[i][2].split('/')[0].split(' ')[1].split(':')[0] for i in range(len(ip))]
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
    "0:90,2:28,2:28,2:28,2:28,2:28,2:148":0,    #????????????:????????????   ,??????  :???????????? ??????:?????? :????????????
    "0:1,1:1":2,
}
    interval_time=5             # ???????????????????????????(s)
    data_num_power_off=10       # ??????????????????0s????????????
    timeout_time=5
    dv_test(time_dict,interval_time,data_num_power_off,timeout_time)