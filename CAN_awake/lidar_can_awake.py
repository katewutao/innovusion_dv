import subprocess
import time
import os
import datetime

def set_power(ip):
    command=f'echo "dsp_boot_from power" | nc -nv {ip} 8001'
    os.system(command)

def load_config():
    import json
    with open("config.json",'r') as f:
        return json.load(f)

def main():
    config=load_config()
    can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    time.sleep(20)
    for ip in config["lidar_ip"]:
        set_power(ip)
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")


if __name__=="__main__":
    main()