import os
import argparse
import subprocess
import select
import re
import datetime


def main(args):
    util_dir="./"
    util_path=os.path.join(util_dir,"inno_pc_client")
    command=f"{os.path.abspath(util_path)} --lidar-ip {args.ip} --lidar-port {args.lidar_port} --lidar-udp-port {args.lidar_udp_port}"
    print(command)
    cmd=subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    poll_obj=select.poll()
    poll_obj.register(cmd.stderr,select.POLLIN)
    while True:
        if poll_obj.poll(0):
            stderr=cmd.stderr.readline().decode("utf-8")
            ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sset",stderr)
            if ret:
                print("\033[0;31;40m", f"[{datetime.datetime.now()}] {args.ip} {ret.group(2)} has been set", "\033[0m")
        stdout=cmd.stdout.readline().decode("utf-8")
        ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sheal",stdout)
        if ret:
            print("\033[1;32m", f"[{datetime.datetime.now()}] {args.ip} {ret.group(2)} has been heal", "\033[0m")
        

if __name__=="__main__":
    parses=argparse.ArgumentParser()
    parses.add_argument("--ip","-i",type=str,required=True)
    parses.add_argument("--lidar-port","-lp",type=str,default="8010")
    parses.add_argument("--lidar-udp-port","-lup",type=str,default="8010")
    args=parses.parse_args()
    main(args)
