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
from oneclient import record_header,record_keys,csv_write


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
        print('please connect lidar %s'%(ip))
        flag=ping(ip,interval_time)
    print('lidar %s has connected'%(ip))

def test(times,num_e,interval_time,ip_extract,data_num_power_off):
    times=times*num_e
    for item in times:
        t=time.time()
        while True:
            try:
                pow.power_on()
                df=pd.DataFrame([pow.PowerStatus()])
                break
            except:
                os.system('sshpass -p demo sudo python3 ./power.py')
                try:
                    pow=power.Power()
                    pow.power_on()
                    break
                except:   
                    continue
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
                print(ip_extract[i]+' is record!!')
            time.sleep(item[0])
            for cmd in cmds:
                cmd.kill()
            print("record has been terminated")
            cmd_pow.kill()
            cmd_pow.wait()
        else:
            for ip in ip_extract:
                for _ in range(data_num_power_off):
                    temp=[time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))]+[-100]*(len(record_keys)-1)
                    #print(temp)
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
                os.system('sshpass -p demo sudo python3 ./power.py')
                try:
                    pow=power.Power()
                    pow.power_off()
                    break
                except:   
                    continue
        for i in range(data_num_power_off):
            for ip in ip_extract:
                # print(os.getcwd()+'/result/record_'+ip.replace('.','_')+'.csv')
                temp=[time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))]+[-100]*(len(record_keys)-1)
                #print(temp)
                csv_write(os.getcwd()+'/result/record_'+ip.replace('.','_')+'.csv',temp)
            t0=(item[0]+item[1]-time.time()+t)/(data_num_power_off-i)
            if t0>0:
                time.sleep(t0)
        print('current time is %.2f s'%((time.time()-t)))



def dv_test(set_loop_time1,set_loop_time2,num_e1,num_e2,interval_time=5,data_num_power_off=10,timeout_time=5):
    if not os.path.exists(os.getcwd()+'/result'):
        os.mkdir(os.getcwd()+'/result')
    os.system('sshpass -p demo sudo python3 ./power.py')
    pow=power.Power()
    pow.power_on()
    time.sleep(15)
    ip=pd.read_csv(os.getcwd()+'/IP_CMD_List.csv').values.tolist()
    ip_extract=[ip[i][2].split('/')[0].split(' ')[1].split(':')[0] for i in range(len(ip))]
    for item in ip_extract:
        ping_sure(item,0.2)

    set_loop_time=set_loop_time1
    num_e=num_e1
    times=set_loop_time.split(',')
    for i in range(len(times)):
        times[i]=times[i].split(':')
    for i in range(len(times)):
        for j in range(len(times[i])):
            times[i][j]=float(times[i][j].strip())*60

    for i in range(len(ip_extract)):
        cmd='ssh root@'+ip_extract[i]
        print(f'get lidar promission: {cmd}')
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
    test(times,num_e,interval_time,ip_extract,data_num_power_off)
    set_loop_time=set_loop_time2
    num_e=num_e2
    time_2=set_loop_time.split(',')
    for i in range(len(time_2)):
        time_2[i]=time_2[i].split(':')
    for i in range(len(time_2)):
        for j in range(len(time_2[i])):
            time_2[i][j]=float(time_2[i][j].strip())*60
    test(time_2,num_e,interval_time,ip_extract,data_num_power_off)
    print('summary time is %.2f min'%((time.time()-get_current_time)/60))
    
if __name__=="__main__":
    ####first
    set_loop_time1="0:90,2:28,2:28,2:28,2:28,2:28,2:148"  ##通电时间:断电时间   ,分隔  单位:分钟
    num_e1=0  #大循坏次数

    ###################last
    set_loop_time2="0:1,1:1"  ##通电时间:断电时间   ,分隔  单位:分钟
    num_e2=2  #大循坏次数
    '''set_loop_time1="0:1,1:1,1:1,1:1"
    num_e1=2
    set_loop_time2="0:1,1:1"
    num_e2=5'''



    interval_time=5             # 上电时记录时间间隔(s)
    data_num_power_off=10       # 断电时或通电0s空值数量
    timeout_time=5
    dv_test(set_loop_time1,set_loop_time2,num_e1,num_e2,interval_time,data_num_power_off,timeout_time)
