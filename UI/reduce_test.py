import numpy as np
import pandas as pd
import socket,platform
import subprocess,time,re,datetime
ip_list=["172.168.1.10"]

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

#get current time,and convert to string,format "yearmonthdayThourminutesecond"
def current_time():
    now = datetime.datetime.now()
    now = now.strftime("%Y%m%dT%H%M%S")
    return now
    
def connect_port_nc(ip,port):
    command=f"nc -zv {ip} {port} -w1"    
    cmd=subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    res=cmd.communicate()
    res=str(res)
    if "succeeded" in res:
        return True
    else:
        return False
    
def connect_port(ip,port,time_out=0.5):
    sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.settimeout(time_out)
    try:
        sock.connect((ip,port))
        return True
    except:
        return False
    
def set_can(ip):
    command=f'echo "dsp_boot_from can" | nc -nv {ip} 8001'
    cmd=subprocess.Popen(command,shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)
    res=cmd.communicate()
    if "dsp boot from can: OK" in res[0]:
        print(f"[{datetime.datetime.now()}] {ip} set can mode success")
        return True
    else:
        print(f"[{datetime.datetime.now()}] {ip} set can mode fail")
        set_can(ip)


def connect_all_lidar(ip_list):
    status=True
    for ip in ip_list:
        if ping(ip,0.3):
            if not connect_port(ip,8010):
                print(f"[{datetime.datetime.now()}] lidar {ip} has connected,but port 8010 is not connected")
                status=False
            elif not connect_port(ip,8088):
                print(f"[{datetime.datetime.now()}] lidar {ip} has connected,but port 8088 is not connected")
                status=False
            elif not connect_port(ip,8675):
                print(f"[{datetime.datetime.now()}] lidar {ip} has connected,but port 8675 is not connected")
                status=False
            elif not connect_port(ip,22):
                print(f"[{datetime.datetime.now()}] lidar {ip} has connected,but port 22 is not connected")
                status=False
        else:
            status=False
    return status

while True:
    for ip in ip_list:
        if ping(ip,0.3):
            set_can(ip)
    cmd1=subprocess.Popen("python3 can_run.py",shell=True,stdout=open("CAN.log","a"),stderr=subprocess.STDOUT)
    t=time.time()
    for ip in ip_list:
        while True:
            if ping(ip,0.3):
                print(f"[{datetime.datetime.now()}] lidar {ip} has connected")
                break
    while True:
        if connect_all_lidar(ip_list):
            if time.time()-t>60:
                break
    cmd2=subprocess.Popen("python3 can_cancle.py",shell=True)
    cmd2.wait()
    print(f"[{datetime.datetime.now()}] start sleep 60s")
    time.sleep(60)