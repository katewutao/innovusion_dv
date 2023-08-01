import numpy as np
import pandas as pd
import subprocess,time,re,datetime

def main():
    command="curl --connect-timeout 2 172.168.1.10:8088/get-all-status"
    cmd=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        cmd.wait(2)
        res=str(cmd.stdout.read())
    except:
        res=""
    cmd.kill()
    return res

#get current time,and convert to string,format "yearmonthdayThourminutesecond"
def current_time():
    now = datetime.datetime.now()
    now = now.strftime("%Y%m%dT%H%M%S")
    return now

key="(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.*\s([A-Z]+[A-Z_0-9]+).+(?:has|have)\sbeen\s(set|heal)"
str1="2021-12-19 19:50:21.101 [ERROR] 907 fault_manager.cpp INNO_LIDAR_IN_FAULT_OVERHEAT1(39) has been set internally. current temperature: 960, threshold: 950"
ret=re.search(key,str1)
if ret:
    print(ret.groups())