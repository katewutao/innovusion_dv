import subprocess
import time
import os
import datetime
import sys
import threading


def downlog(ip,time_path):
    save_path=os.path.join(log_path,ip.replace('.','_'))
    save_path=os.path.join(save_path,time_path)
    os.makedirs(save_path)
    #os.makedirs(os.path.join(save_path,'mnt'))
    command1=f"sshpass -p 4920lidar scp -rp root@{ip}:/tmp {save_path}"
    command2=f"sshpass -p 4920lidar scp -rp root@{ip}:/mnt {save_path}"
    cmd1=subprocess.Popen(command1,shell=True)
    cmd2=subprocess.Popen(command2,shell=True)
    
    

def get_promission(ip):
    if 'linux' in sys.platform:
        import pexpect as pect
    else:
        import wexpect as pect
    child = pect.spawn(f'ssh root@{ip}',timeout=1)
    try:
        child.expect('yes',timeout=3)
        child.sendline('yes')
    except:
        pass
    child.expect('password')
    child.sendline('4920lidar')
    child.close()


def set_can(ip):
    command=f'echo "dsp_boot_from can" | nc -nv {ip} 8001'
    os.system(command)
    
    

def get_time():
    times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
    res=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
    return res


def load_config():
    import json
    with open("config.json",'r') as f:
        return json.load(f)


def one_cycle(power_on_time,power_off_time,ip_list,i):
    print(f"[{str(datetime.datetime.now())}]: current circle {i+1}")
    time_path=get_time()
    for ip_num in range(len(ip_list)):
        raw_save_path="result/raw/"+ip_list[ip_num].replace('.','_')+'/'+time_path
        subprocess.Popen(f'python3 capture_raw.py -i {ip_list[ip_num]} -s "{raw_save_path}" -l {9100+ip_num} -ls {8100+ip_num}',shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
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
    time.sleep(power_off_time)


def main(config,log_path):
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    records=[]
    for ip in config["lidar_ip"]:
        try:
            get_promission(ip)
            set_can(ip)
        except:
            pass
        cmd=subprocess.Popen(f"exec python3 oneclient.py --ip {ip} --interval 1",shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE)
        records.append(cmd)
    os.system("python3 lib/set_usbcanfd_env.py demo")
    
    if config["mode"]=="time":
        i=0
        start_time=time.time()
        while time.time()-start_time<config["mode_time"]:
            one_cycle(config["power on time"],config["power off time"],config["lidar_ip"],i)
            i+=1
    else:
        for i in range(config["mode_time"]):
            one_cycle(config["power on time"],config["power off time"],config["lidar_ip"],i)
    for record in records:
        record.kill()


if __name__=="__main__":
    config=load_config()
    log_path="result/log"
    main(config,log_path)
