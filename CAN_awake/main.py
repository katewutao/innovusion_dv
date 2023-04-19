#!/usr/bin/python3

# /**
#  * @author katewutao
#  * @email [kate.wu@cn.innovuison.com]
#  * @create date 2023-01-19 09:15:01
#  * @modify date 2023-01-19 09:15:01
#  * @desc [description]
#  */
import subprocess
import time
import os,shutil
import datetime
import sys
import threading
import re
import pandas as pd
from oneclient import record_header,csv_write,save_path
from auto_update_sdk import down_sdk




def get_current_date():
    start_time=f"{datetime.datetime.now()}"
    ret=re.findall("\d+",start_time)
    start_time=f"{ret[0].zfill(4)}{ret[1].zfill(2)}{ret[2].zfill(2)}T{ret[3].zfill(2)}{ret[4].zfill(2)}{ret[5].zfill(2)}"
    return start_time

log_file="python_"+get_current_date()+".log"
rewrite_print=print
def print(*arg,**kwarg):
    rewrite_print(*arg,**kwarg)
    rewrite_print(*arg,**kwarg,file=open(log_file,"a"))



def downlog(ip,log_path,time_path):
    save_path=os.path.join(log_path,ip.replace('.','_'))
    save_path=os.path.join(save_path,time_path)
    os.makedirs(save_path)
    #os.makedirs(os.path.join(save_path,'mnt'))
    command1=f"sshpass -p 4920lidar scp -rp root@{ip}:/tmp '{save_path}'"
    command2=f"sshpass -p 4920lidar scp -rp root@{ip}:/mnt '{save_path}'"
    cmd1=subprocess.Popen(command1,shell=True)
    cmd2=subprocess.Popen(command2,shell=True)
    cmd1.wait()
    cmd2.wait()

def ping(ip,interval_time):
    command=f'ping -c 1 -W 0.15 {ip}'
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


def list_in_str(key_list,str1):
    for key in key_list:
        if key in str1:
            return True
    return False

def init_power():
    import shutil
    cmd=os.popen("lsusb")
    res=cmd.read()
    if os.path.exists("power.py"):
        os.remove("power.py")
    if list_in_str(["FT232","0403:6001","067b:23c3"],res):
        shutil.copyfile(os.path.join(os.getcwd(),"power_DH.py"),os.path.join(os.getcwd(),"power.py"))
        return True 
    elif list_in_str(["HL-340","PL2303","1a86:7523"],res):
        shutil.copyfile(os.path.join(os.getcwd(),"power_PY.py"),os.path.join(os.getcwd(),"power.py"))
        return True
    print("power is not PY or DH")
    return False
    
    
def ping_sure(ip,interval_time):
    flag=ping(ip,interval_time)
    while flag==0:
        print(f'[{datetime.datetime.now()}]please connect lidar {ip}')
        flag=ping(ip,interval_time)
    print(f'[{datetime.datetime.now()}]lidar {ip} has connected')    
    
def get_promission(ip,time_out):
    if 'linux' in sys.platform:
        import pexpect as pect
    else:
        import wexpect as pect
    child = pect.spawn(f'ssh root@{ip}',timeout=time_out)
    try:
        child.expect('yes',timeout=3)
        child.sendline('yes')
    except:
        pass
    child.expect('password')
    child.sendline('4920lidar')
    child.close()


def get_circle_time(dict_config):
    times=[]
    for key in dict_config.keys():
        temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*):?(\d+\.?\d*)?",key)
        for i in range(len(temp_times)):
            temp_times[i]=list(temp_times[i])
            for j in range(len(temp_times[i])):
                if j!=2:
                    temp_times[i][j]=float(temp_times[i][j])*60
                else:
                    if temp_times[i][j]!="":
                        temp_times[i][j]=float(temp_times[i][j])
                    else:
                        temp_times[i][j]=14
        times+=temp_times*dict_config[key]
    return times


def set_can(ip):
    command=f'echo "dsp_boot_from can" | nc -nv {ip} 8001'
    os.system(command)
    
def cancle_can(ip_list):
    print(f"{datetime.datetime.now()}:start set lidar power mode")
    can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    time.sleep(30)
    for ip in ip_list:
        ping_sure(ip,0.5)
        command=f'echo "dsp_boot_from power" | nc -nv {ip} 8001'
        os.system(command)
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
    
def is_empty_folder(path):
    for _,_,files in os.walk(path):
        if len(files)!=0:
            return False
    return True


def rm_empty_folder(path):
    for root,_,_ in os.walk(path):
        if is_empty_folder(root):
            try:
                shutil.rmtree(root)
            except:
                pass

def get_time():
    times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
    res=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
    return res


def load_config():
    import json
    with open("config.json",'r') as f:
        return json.load(f)


def one_cycle(power_one_time,ip_list,i,interval_time,data_num_power_off,log_path):
    from power import Power
    while True:
        try:
            pow=Power()
            pow.set_voltage(power_one_time[2])
            break
        except:
            print(f"{datetime.datetime.now()} set power voltage failed")
    print(f"[{str(datetime.datetime.now())}]: current circle {i}")
    t=time.time()
    time_path=get_time()
    subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    records=[]
    for ip in ip_list:
        cmd=subprocess.Popen(f"exec python3 oneclient.py --ip {ip} --interval {interval_time}",shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        records.append(cmd)
    if power_one_time[0]>2:
        for ip_num in range(len(ip_list)):
            raw_save_path="result/raw/"+ip_list[ip_num].replace('.','_')+'/'+time_path
            subprocess.Popen(f'python3 capture_raw.py -i {ip_list[ip_num]} -s "{raw_save_path}" -l {9100+ip_num} -ls {8100+ip_num} -lup {8600+ip_num}',shell=True)
        time.sleep(power_one_time[0]-2)
    threads=[]
    for ip in ip_list:
        thread=threading.Thread(target=downlog,args=(ip,log_path,time_path,))
        thread.start()
        threads.append(thread)
    for temp_thread in threads:
        temp_thread.join()
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk '{print $2}'|xargs kill -9")
    os.system("ps -ef|grep capture_raw.py|grep -v grep|awk '{print $2}'|xargs kill -9")
    os.system("ps -ef|grep inno_pc_client|grep -v grep|awk '{print $2}'|xargs kill -9")
    print("start sleep")
    for record in records:
        record.kill()
    for i in range(data_num_power_off):
        for ip in ip_list:
            while True:
                try:
                    pow = pd.read_csv(os.path.join(save_path,'pow_status.csv'), header=None).values.tolist()
                    break
                except:
                    pass
            temp=[str(datetime.datetime.now())]+[-100]*(record_header.count(",")-2)+pow[0]
            csv_write(os.path.join(save_path,'record_'+ip.replace('.','_')+'.csv'),temp)
        t0=(power_one_time[0]+power_one_time[1]-(time.time()-t))/(data_num_power_off-i)
        if t0>0:
            time.sleep(t0)


def main(config,log_path):
    print(f"[{datetime.datetime.now()}]get inno_pc_client permission")
    os.system('echo demo|sudo -S chmod 777 lidar_util/inno_pc_client')
    while not init_power():
        pass
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    os.system("python3 ./power.py")
    for ip in config["lidar_ip"]:
        ping_sure(ip,0.5)
        down_sdk(ip)
        try:
            get_promission(ip,config["timeout_time"])
            set_can(ip)
        except:
            pass
        record_file=os.path.join(save_path,'record_'+ip.replace('.','_')+'.csv')
        if not os.path.exists(record_file):
            with open(record_file,"w",newline="\n") as f:
                f.write(record_header)
    os.system("python3 lib/set_usbcanfd_env.py demo")
    command='exec python3 power_client.py'
    cmd_pow=subprocess.Popen(command,stderr=subprocess.PIPE,shell=True)
    times=get_circle_time(config["time_dict"])
    i=1
    for time_one in times:
        one_cycle(time_one,config["lidar_ip"],i,config["interval_time"],config["data_num_power_off"],log_path)
        i+=1 
    cmd_pow.kill()
    cancle_can(config["lidar_ip"])
    os.system("echo demo|sudo -S python3 ./power.py")
    import power
    pow=power.Power()
    pow.power_off()
    rm_empty_folder(save_path)

if __name__=="__main__":
    config={
        "lidar_ip":[
            "172.168.1.10",
            "172.168.1.2",
            "172.168.1.3",
            "172.168.1.4",
            "172.168.1.5",
            "172.168.1.6",
            ],  
        #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
        
        "time_dict":{
            "1:0.5": 10,
        },
        #"CAN唤醒时间:CAN休眠时间:电源电压,CAN唤醒时间:CAN休眠时间:电源电压,CAN唤醒时间:CAN休眠时间:电源电压":循环次数
        #时间单位为分钟
        #电源电压单位V，不设默认为13.5V
        
        "data_num_power_off":10,    #CAN休眠时空数据数量
        "interval_time":5,          #记录雷达状态的时间间隔
        "timeout_time":5,           #获取雷达连接权限的超时时间
    }
    log_path=os.path.join(save_path,"log")
    main(config,log_path)