import subprocess
import time
import os
import datetime
import sys
import threading
import re
import pandas as pd
from oneclient import record_header,csv_write,save_path


def downlog(ip,time_path):
    save_path=os.path.join(log_path,ip.replace('.','_'))
    save_path=os.path.join(save_path,time_path)
    os.makedirs(save_path)
    #os.makedirs(os.path.join(save_path,'mnt'))
    command1=f"sshpass -p 4920lidar scp -rp root@{ip}:/tmp {save_path}"
    command2=f"sshpass -p 4920lidar scp -rp root@{ip}:/mnt {save_path}"
    cmd1=subprocess.Popen(command1,shell=True)
    cmd2=subprocess.Popen(command2,shell=True)

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
        temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*)",key)
        for i in range(len(temp_times)):
            temp_times[i]=list(temp_times[i])
            for j in range(len(temp_times[i])):
                temp_times[i][j]=float(temp_times[i][j])*60
        times+=temp_times*dict_config[key]
    return times


def set_can(ip):
    command=f'echo "dsp_boot_from can" | nc -nv {ip} 8001'
    os.system(command)
    
def cancle_can(ip_list):
    can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    for ip in ip_list:
        command=f'echo "dsp_boot_from power" | nc -nv {ip} 8001'
        os.system(command)
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
    
    

def get_time():
    times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
    res=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
    return res


def load_config():
    import json
    with open("config.json",'r') as f:
        return json.load(f)


def one_cycle(power_on_time,power_off_time,ip_list,i,data_num_power_off,interval_time):
    print(f"[{str(datetime.datetime.now())}]: current circle {i}")
    t=time.time()
    time_path=get_time()
    for ip_num in range(len(ip_list)):
        raw_save_path="result/raw/"+ip_list[ip_num].replace('.','_')+'/'+time_path
        subprocess.Popen(f'python3 capture_raw.py -i {ip_list[ip_num]} -s "{raw_save_path}" -l {9100+ip_num} -ls {8100+ip_num}',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    records=[]
    for ip in ip_list:
        cmd=subprocess.Popen(f"exec python3 oneclient.py --ip {ip} --interval {interval_time}",shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        records.append(cmd)
    if power_on_time>=2:
        time.sleep(power_on_time-2)
    threads=[]
    for ip in ip_list:
        thread=threading.Thread(target=downlog,args=(ip,time_path,))
        thread.start()
        threads.append(thread)
    for temp_thread in threads:
        temp_thread.join()
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
    os.system("ps -ef|grep capture_raw.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
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
        t0=(power_on_time+power_off_time-(time.time()-t))/(data_num_power_off-i)
        if t0>0:
            time.sleep(t0)


def main(config,log_path):
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    for ip in config["lidar_ip"]:
        ping_sure(ip,0.5)
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
        one_cycle(time_one[0],time_one[1],config["lidar_ip"],i,config["interval_time"],config["data_num_power_off"])
        i+=1 
    cmd_pow.kill()
    cancle_can(config["lidar_ip"])

if __name__=="__main__":
    config=load_config()
    log_path="result/log"
    main(config,log_path)
