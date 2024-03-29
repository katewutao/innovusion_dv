# /**
#  * @author katewutao
#  * @email [kate.wu@cn.seyond.com]
#  * @create date 2023-05-05 10:12:54
#  * @modify date 2024-02-28 16:11:33
#  * @desc [DV test main function]
#  */
import os
import sys
import time
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import userpage
import subprocess
import re,threading
import platform
import datetime
import traceback
import inspect
import pandas as pd
import requests
import shutil,json,importlib
from common.auto_update_sdk import down_sdk
from utils.excel_format import ExcelFormat
import math
from threading import Thread
import sys
import builtins
from utils import *
from utils.ConvertPcd import *
from utils.plot_data import *
sys.path.append(".")

pointcloud_config = {}
pow_status=[0,0]
spec_df = pd.DataFrame(columns=["LL", "UL"])
 
builtins.print_origin=print
def rewrite_print(log_path):
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    def print_res(*args, **kwargs):
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        msg = ' '.join(map(str, args))  # Convert all arguments to strings and join them with spaces
        builtins.print_origin(f"[{current_date}] {msg}", **kwargs)
        builtins.print_origin(f"[{current_date}] {msg}", **kwargs, file=open(log_path, "a"))
    return print_res
 
 
def set_tbw_value(tbw_obj):
    def set_value(values,row_idx):
        global spec_df
        ip = tbw_obj.item(row_idx, 0).text()
        for idx,value in enumerate(values):
            column_name=tbw_obj.horizontalHeaderItem(idx).text()
            new_item=QtWidgets.QTableWidgetItem(f"{value}")
            # new_item.setForeground(QtGui.QColor(0,0,0))
            new_item.setBackground(QtGui.QColor(255,255,255))
            ret=re.search("^-?\d+\.?\d*$",str(value))
            if ret:
                value_float=float(value)
                if column_name in spec_df.index:
                    if not pd.isna(spec_df.loc[column_name,"LL"]) and value_float<spec_df.loc[column_name,"LL"]:
                        print(f"{ip} {column_name} is {value_float},below LL {spec_df.loc[column_name,'LL']}")
                        # new_item.setForeground(QtGui.QColor(255,0,0))
                        new_item.setBackground(QtGui.QColor(255,0,0))
                    elif not pd.isna(spec_df.loc[column_name,"UL"]) and value_float>spec_df.loc[column_name,"UL"]:
                        print(f"{ip} {column_name} is {value_float},above UL {spec_df.loc[column_name,'UL']}")
                        # new_item.setForeground(QtGui.QColor(255,0,0))
                        new_item.setBackground(QtGui.QColor(255,0,0))
            tbw_obj.setItem(row_idx,idx+1,new_item)
    return set_value
 


def time_limited(timeout):
    def decorator(function):
        def decorator2(*args, **kwargs):
            class TimeLimited(Thread):
                def __init__(self, _error=None, ):
                    Thread.__init__(self)
                    self.error = _error
                    self.result = None

                def run(self):
                    try:
                        self.result = function(*args, **kwargs)
                    except Exception as e:
                        self.error = e
            t = TimeLimited()
            t.setDaemon(True)
            t.start()
            t.join(timeout)
            if t.error:
                raise t.error
            if t.is_alive():
                # print(f"{function.__name__} time out")
                pass
            return t.result
        return decorator2
    return decorator



def ping(ip,time_interval=3,sleep_time=1):
    res = False
    respon=None
    try:
        respon=requests.get(f"http://{ip}",timeout=time_interval)
        res = True
    except:
        print(f"{ip} ping failed")
        time.sleep(sleep_time)
    if respon:
        respon.close()
    return res
    

def downlog(ip,log_path,time_path,wait_time=8):
    save_path=os.path.join(log_path,"log",ip.replace('.','_'),time_path)
    os.makedirs(save_path)
    if not ping(ip,1):
        print(f"{ip} is not connect, download log failed") 
        return
    command1=f"exec sshpass -p 4920lidar scp -rp root@{ip}:/tmp '{save_path}'"
    command2=f"exec sshpass -p 4920lidar scp -rp root@{ip}:/mnt '{save_path}'"
    cmd1=subprocess.Popen(command1,shell=True)
    cmd2=subprocess.Popen(command2,shell=True)
    try:
        cmd1.wait(wait_time)
    except:
        cmd1.kill()
        print(f"{ip} download tmp timeout")
    try:
        cmd2.wait(wait_time)
    except:
        cmd2.kill()
        print(f"{ip} download mnt timeout")
    kill_subprocess(f"scp -rp root@{ip}")
    for root,_,files in os.walk(save_path):
        for file in files:
            ret=re.search("\.txt",file)
            if not ret or ".md" in file:
                os.remove(os.path.join(root,file))
    print(f"{ip} download log success")


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
    print(f"power is not PY or DH")
    return False

def set_power_status(power_voltage,power_on=True):
        import power
        while True:
            try:
                pow=power.Power()
                if power_on:
                    pow.power_on()
                else:
                    pow.power_off()
                break
            except:
                if power_on:
                    print(f"power on failed")
                else:
                    print(f"power off failed")
                time.sleep(2)
        if isinstance(power_voltage,type(None)):
            return
        last_timestamp = time.time()
        while True:
            try:
                print(f"start set voltage")
                pow=power.Power()
                print(f"init power")
                pow.set_voltage(power_voltage)
                print(f"set {power_voltage}V")
                voltage=pow.PowerStatus()[0]
                print(f"voltage is {voltage}")
                if abs(voltage-power_voltage)<0.3:
                    break
            except:
                current_timestamp=time.time()
                if current_timestamp-last_timestamp>3:
                    last_timestamp=current_timestamp
                    print(f"set power voltage failed, {power_voltage}V")
                time.sleep(2)
    
def ping_sure(ip,interval_time):
    while True:
        if ping(ip,interval_time):
            break
        else:
            print(f"{ip} is not connect")
    print(f' lidar {ip} has connected')    
    

def get_circle_time(dict_config):
    times=[]
    if isinstance(dict_config,dict):
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
    elif isinstance(dict_config,str):
        dict_config=dict_config.split("\n")
        for one_line in dict_config:
            temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*):?(\d+\.?\d*)?",one_line)
            temp_circle=re.search('''(".+"|'.+').*?(\d+)''',one_line)
            if len(temp_times)>0 and temp_circle:
                circle = int(temp_circle.group(2))
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
                times+=temp_times*circle        
    return times



def set_lidar_mode(ip,lidar_type,can_mode):
    if can_mode=="Robin":
        boot_name="lidar_boot_from"
    else:
        boot_name="dsp_boot_from"
    command=f'echo "{boot_name} {lidar_type}" | nc -nv {ip} 8001 -w1'
    cmd=subprocess.Popen(command,shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)
    res=cmd.communicate()
    if re.search(f"boot from.+{lidar_type}",res[0]):
        print(f"{ip} set {lidar_type} mode success")
        if can_mode=="Robin":
            LidarTool.reboot_lidar(ip)
        return True
    else:
        print(f"{ip} set {lidar_type} mode fail")
        return False


def cancle_can(ip_list,can_mode="Default"):
    set_power_status(None,True)
    print(f"start set lidar power mode")
    subprocess.Popen(f'python3 can_run.py -c {can_mode}',shell=True)
    for ip in ip_list:
        ping_sure(ip,3)
        while True:
            if set_lidar_mode(ip,"power",can_mode):
                break
    os.system(f"python3 can_cancle.py -c {can_mode}")
    print(f"all lidar cancle can mode success")
    
    
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
            
def get_tags():
    cmd = subprocess.Popen("git describe --tags", shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    time.sleep(0.8)
    if not cmd.poll():
        res = cmd.stdout.read()
        if "fatal" not in res:
            return res.strip("\n")
    tags_folder = "./.git/refs/tags"
    if not os.path.exists(tags_folder):
        return ""
    tags = os.listdir(tags_folder)
    if len(tags) == 0:
        return ""
    modify_time = [[tag, os.path.getmtime(
        os.path.join(tags_folder, tag))] for tag in tags]
    modify_time = sorted(modify_time, key=lambda x: x[1], reverse=True)
    tag = modify_time[0][0]
    if not os.path.exists(os.path.join(tags_folder, tag)):
        return ""
    with open(os.path.join(tags_folder, tag), "r") as f:
        tag_content = f.read()
    head_folder = "./.git/HEAD"
    if not os.path.exists(head_folder):
        return ""
    with open(head_folder, "r") as f:
        head_content = f.read()
    ret = re.search("ref:\s?(.+)$", head_content)
    if not ret:
        return tag
    else:
        with open(os.path.join("./.git", ret.group(1)), "r") as f:
            branch_content = f.read()
        if branch_content == tag_content:
            return tag
    return f"{tag}-g{branch_content[:7]}"
            

def get_time():
    times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
    res=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
    return res

def kill_client():
    if "windows" in platform.platform().lower():
        return
    command="exec ps -ef|grep inno_pc_client|grep -v grep|awk '{print $2}'|xargs kill -9"
    # print(command)
    print(f"kill client")
    cmd=subprocess.Popen(command,shell=True)
    time.sleep(1)
    if cmd.poll() is not None:
        return
    else:
        cmd.kill()
        kill_client()


class Power_monitor(QThread):
    def __init__(self):
        super(Power_monitor,self).__init__()
        self.thread_run=True
    
    @handle_exceptions
    def run(self):
        global pow_status
        import power
        pow=power.Power()
        while True:
            while not self.thread_run:
                pass            
            if self.isInterruptionRequested():
                break
            try:
                temp=pow.PowerStatus()
                if isinstance(temp,list) and len(temp)==2 and re.search("^\d+\.?\d*$",str(temp[0])) and re.search("^\d+\.?\d*$",str(temp[1])):
                    pow_status=temp
                else:
                    time.sleep(3)
                    print("power status get failed")
            except:
                time.sleep(3)
                try:
                    print("retry init power")
                    pow=power.Power()
                except:
                    time.sleep(5)
                    print(f"retry get power output value")
            time.sleep(0.2)
    
    @handle_exceptions
    def pause(self):
        print(f"power monitor pause")
        self.thread_run=False
    
    @handle_exceptions
    def resume(self):
        print(f"power monitor continue")
        self.thread_run=True
        
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"try finish monitor power")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        print(f"finish monitor power success")
        
class DSP_info_thread(QThread):#TODO
    def __init__(self,ip,record_folder):
        super(DSP_info_thread,self).__init__()
        self.ip=ip
        self.save_folder = os.path.join(record_folder,"DSP")
        self.search_keys = {
            "timestamp":"",
            "Galvo RMS current":"",
            "Galvo frame counter":"",
            "Galvo position control error":"",
            "Galvo zero position offset value":"",
            "Galvo LED DAC value":"",
            "Galvo sensor intensity":""
        }
        self.read_keys = {
            "Galvo RMS current":"scanh_tran STR051ND",
            "Galvo frame counter":"scanh_tran STR052ND",
            "Galvo position control error":"scanh_tran STR053ND",
            "Galvo zero position offset value":"scanh_tran STR054ND",
            "Galvo LED DAC value":"scanh_tran STR055ND",
            "Galvo sensor intensity":"scanh_tran STR056ND",
            "Events 108":"scanh_tran STR108ND",
            "Events 109":"scanh_tran STR109ND",
        }
        self.command = f"http://{ip}" # API time interval = socket time interval, so not using API
    
    def extract_keys(self,res):
        re_list = []
        lens = []
        for item in self.search_keys.items():
            if item[1]=="":
                re_list.append(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
            else:
                ret = re.findall(item[1],res)
                lens.append(len(ret))
                if lens[-1]>0:
                    re_list.append(ret)
                else:
                    print(f"{self.ip} dsp return not exist {item[0]}")
                    return []
        if max(lens)!=min(lens):
            print(f"{self.ip} dsp return format error")
            return []
        return list(zip(*re_list))
    
    def get_socket_result(self):
        res_list = [f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"]
        for item in self.read_keys.items():
            res = send_tcp(item[1],self.ip,8001,False)
            if res == "":
                res = "NaN"
            res_list.append(res.strip("\n"))
        return res_list
    
    @handle_exceptions
    def run(self):
        if not os.path.exists(self.save_folder):
            try:
                os.makedirs(self.save_folder)
            except:
                pass
        self.record_file = os.path.join(self.save_folder,f"{self.ip.replace('.','_')}.csv")
        if not os.path.exists(self.record_file):
            csv_write(self.record_file,["timestamp"]+list(self.read_keys.keys()))
        while True:
            if ping(self.ip,3):
                break
            if self.isInterruptionRequested():
                return
        while True:
            if self.isInterruptionRequested():
                break
            res_list = self.get_socket_result()
            csv_write(self.record_file,res_list)
    
    
    @handle_exceptions
    def run_api(self): #using API
        if not os.path.exists(self.save_folder):
            try:
                os.makedirs(self.save_folder)
            except:
                pass
        self.record_file = os.path.join(self.save_folder,f"{self.ip.replace('.','_')}.csv")
        if not os.path.exists(self.record_file):
            csv_write(self.record_file,[item for item in self.search_keys])
        last_time = -999
        while True:
            if self.isInterruptionRequested():
                break
            res, flag = get_curl_result(self.command)
            if flag:
                re_list = self.extract_keys(res)
                current_max_time = last_time
                for item in re_list:
                    current_time = str2timestamp(item[0])
                    current_max_time = max(current_time,current_max_time)
                    if current_time>last_time:
                        csv_write(self.record_file,item)
    
    
    @handle_exceptions
    def stop(self):
        print(f"{self.ip} start finish Dsp status")
        t=time.time()
        while self.isRunning():
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>6:
                self.terminate()
                break
        print(f"{self.ip} finish Dsp success")
    
    
class one_lidar_record_thread(QThread):
    sigout_set_tbw_value = pyqtSignal(list,int)
    
    def __init__(self,ip,interval,record_folder,record_header,row_idx,record_func):
        super(one_lidar_record_thread,self).__init__()
        self.ip=ip
        self.interval=interval
        self.record_folder=record_folder
        self.row_idx=row_idx
        self.record_header=record_header
        self.record_func=record_func 

    @handle_exceptions
    def run(self):
        while True:
            if ping(self.ip,3):
                break
            if self.isInterruptionRequested():
                return
        ip_name=self.ip.replace('.', '_')
        save_log=os.path.join(self.record_folder,f"testlog_{ip_name}.txt")
        save_csv=os.path.join(self.record_folder,f"record_{ip_name}.csv")
        if not os.path.exists(save_csv):
            csv_write(save_csv,self.record_header)
        while True:
            sn_res=get_curl_result(f"http://{self.ip}:8010/command/?get_sn",1)
            if sn_res[1]:
                sn=sn_res[0]
                break
        while True:
            CustomerSN=LidarTool.get_customerid(self.ip)
            if CustomerSN!=None:
                break
        global pow_status
        while True:
            if self.isInterruptionRequested():
                break
            t=time.time()
            temp=self.record_func(self.ip,save_log,sn,CustomerSN)
            if isinstance(temp,type(None)):
                continue
            temp+=pow_status
            csv_write(save_csv, temp)
            self.sigout_set_tbw_value.emit(temp,self.row_idx)
            sleep_time=self.interval-time.time()+t
            if sleep_time>0:
                time.sleep(sleep_time)
    
    @handle_exceptions  
    def stop(self):
        print(f"{self.ip} start finish record lidar status")
        t=time.time()
        while self.isRunning():
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>6:
                self.terminate()
                break
        print(f"{self.ip} finish record thread success")



class MonitorFault(QThread):
    sigout_fault_info = pyqtSignal(str,int)
    sigout_fault_heal = pyqtSignal(str,int)
    def __init__(self,ip,faultpath,savepath,row_idx,lidar_udp_port,udp_port,tcp_port,raw_port,lidar_port=8010):
        super(MonitorFault,self).__init__()
        self.ip=ip
        self.faultpath=faultpath
        self.savepath=os.path.abspath(savepath)
        self.lidar_udp_port=lidar_udp_port
        self.udp_port=udp_port
        self.tcp_port=tcp_port
        self.raw_port=raw_port
        self.lidar_port=lidar_port
        self.row_idx=row_idx
        self.raw_list = {}
        self.max_raw = 10
        
    def newest_folder(self,A,B):
        newest_path=os.path.join(A,str(B))
        return newest_path
        
    def check_raw(self,folder):
        file_list=os.listdir(folder)
        key="^.*\.inno_raw$"  #"sn\d*-\d+.*\.inno_raw$"
        for file in file_list:
            if re.match(key,file):
                self.raw_list[file] = self.raw_list.get(file, 0) + 1
                if self.raw_list[file]>self.max_raw:
                    try:
                        os.remove(os.path.join(folder,file))
                        print(f"{self.ip} {file} count {self.raw_list[file]},remove success")
                    except:
                        print(f"{self.ip} {file} count {self.raw_list[file]},remove failed")
                return True
        return False

    def delete_util_log(self,log_path):
        log_path=os.path.abspath(log_path)
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except:
                pass
    
    def download_fw_pcs(self):
        print(f"{self.ip} download fw and pcs")
        command_fw=f"http://{self.ip}:8675/download?downloadType=log&downloadName=lidar&currBoot=true&downloadFull=true"
        command_pcs=f"http://{self.ip}:8675/download?downloadType=log&downloadName=sdk&currBoot=true&downloadFull=true"
        res_fw = download_file(command_fw,None,3)
        res_pcs = download_file(command_pcs,None,3)
        if res_fw == "":
            print(f"{self.ip} download fw failed")
            return ""
        if res_pcs == "":
            print(f"{self.ip} download pcs failed")
            return ""
        res = str(res_fw)[2:-1] + str(res_pcs)[2:-1]
        return res.replace("\\n","\n")
        
    def get_cmd_print(self,fault_log_path):
        try:
            stdout=self.cmd.stdout.readline()
        except:
            return None
        fault_key="(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.*\s([A-Z]+[A-Z_0-9]+).+(?:has|have)\sbeen\s(set|heal)"
        ret=re.search(fault_key,stdout)
        if ret:
            str1=f"{self.ip} {ret.group(2)} has been {ret.group(3)}"
            with open(fault_log_path,"a") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}]{str1}\n")
            print(str1)
            ret_fault=re.search("IN_FAULT_([A-Z_0-9]+)",ret.group(2))
            if ret_fault:
                if ret.group(3)=="set":
                    self.sigout_fault_info.emit(ret_fault.group(1),self.row_idx)
                else:
                    self.sigout_fault_heal.emit(ret_fault.group(1),self.row_idx)
        ret=re.search("(fault_id.+)\sfrom .+isr",stdout)
        if ret:
            str1=f"{self.ip} {ret.group(1)} has been set"
            print(str1)
            with open(fault_log_path,"a") as f:
                f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}]{str1}\n")
            self.sigout_fault_info.emit(ret.group(1),self.row_idx)
        return stdout.strip("\n")
    
    @handle_exceptions
    def reboot_cmd(self,command1,command2,command3,command4):
        if hasattr(self,"cmd"):
            self.cmd.kill()
        time.sleep(1)
        print(f"{self.ip} inno_pc_client start boot")
        if self.isInterruptionRequested():
            return
        self.cmd=subprocess.Popen(command1,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
        time.sleep(1)
        if self.isInterruptionRequested():
            return
        get_curl_result(command2,1)
        if self.isInterruptionRequested():
            return
        get_curl_result(command3,1)
        if self.isInterruptionRequested():
            return
        get_curl_result(command4,1)
    
    @handle_exceptions
    def run(self):
        util_dir="lidar_util"
        util_path=os.path.join(util_dir,"inno_pc_client")
        fault_log_path=os.path.join(self.faultpath,"fault")
        client_log_folder=os.path.join(self.faultpath,"client_log",self.ip)
        if not os.path.exists(fault_log_path):
            try:
                os.makedirs(fault_log_path)
            except:
                pass
        if not os.path.exists(client_log_folder):
            try:
                os.makedirs(client_log_folder)
            except:
                pass
        fault_log_path=os.path.join(fault_log_path,self.ip.replace(".","_")+".txt")
        client_log_path=os.path.join(client_log_folder,f"{get_current_date()}.txt")
        if not os.path.exists(util_path):
            print(f"file {util_path} not exists!")
            return None
        while True:
            if ping(self.ip,3):
                break
            if self.isInterruptionRequested():
                return
        if not os.path.exists(self.savepath):
            try:
                os.makedirs(self.savepath)
            except:
                pass
        is_first_write=True
        log_lines_counter = 0
        raw_idx = 1
        newest_path=self.newest_folder(self.savepath,raw_idx)
        command1=f'exec "{util_path}" --lidar-ip {self.ip} --lidar-port {self.lidar_port} --lidar-udp-port {self.lidar_udp_port} --udp-port {self.udp_port} --tcp-port {self.tcp_port}'
        command2=f'http://localhost:{self.tcp_port}/command/?set_raw_data_save_path={newest_path}'
        command3=f'http://localhost:{self.tcp_port}/command/?set_faults_save_raw=ffffffffffffffff'
        command4=f'http://localhost:{self.tcp_port}/command/?set_save_raw_data={self.raw_port}'
        raw_count=len(os.listdir(self.savepath))
        while True:
            if self.isInterruptionRequested():
                break
            if not os.path.exists(newest_path):
                if hasattr(self,"cmd") and self.cmd.poll()==None:
                    get_curl_result(command2,1)
                    if self.isInterruptionRequested():
                        return
                else:
                    self.reboot_cmd(command1,command2,command3,command4)
                continue
            cmd_run_flag=False
            try:
                res=self.get_cmd_print(fault_log_path)
                if self.cmd.poll()==None:
                    if res!=None:
                        cmd_run_flag=True
                        with open(client_log_path,"a") as f:
                            if is_first_write:
                                fw_pcs = self.download_fw_pcs()
                                if fw_pcs!="":
                                    f.write(fw_pcs)
                                    is_first_write=False
                                else:
                                    self.reboot_cmd(command1,command2,command3,command4)
                                    continue
                            f.write(f"{res}\n")
                        log_lines_counter = log_lines_counter + 1
                        if log_lines_counter == 50000:
                            log_lines_counter = 0
                            client_log_path=os.path.join(client_log_folder,f"{get_current_date()}.txt")
                    else:
                        print(f"{self.ip} inno_pc_client can't read outline")
                else:
                    print(f"{self.ip} inno_pc_client is stop")      
            except:
                pass
            if not cmd_run_flag:
                self.reboot_cmd(command1,command2,command3,command4)
                continue
            self.delete_util_log(os.path.join(util_dir,f"{self.ip}_out"))
            self.delete_util_log(os.path.join(util_dir,f"{self.ip}_err"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.err"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.1"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.2"))
            if self.check_raw(newest_path):
                if raw_idx >= raw_count:
                    print(f"record raw data to {os.path.abspath(newest_path)}")
                raw_idx += 1
                newest_path=self.newest_folder(self.savepath,raw_idx)
                command2=f'http://localhost:{self.tcp_port}/command/?set_raw_data_save_path={newest_path}'
                if self.isInterruptionRequested():
                    return
                get_curl_result(command2,1)
                if self.isInterruptionRequested():
                    return
                get_curl_result(command3,1)
    
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"{self.ip} try finish monitor fault")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        if hasattr(self,"cmd"):
            self.cmd.kill()
        print(f"{self.ip} finish monitor fualt success")
        

class PointCloud(QThread):
    sigout_pointcloud = pyqtSignal(list,int)
    
    @handle_exceptions
    def __init__(self,ip,row_idx,report_path,pcd_path,get_pcd_path,interval,record_func,pointcloud_header):
        super(PointCloud,self).__init__()
        self.ip=ip
        self.row_idx=row_idx
        self.report_path=report_path
        self.pcd_path=pcd_path
        self.get_pcd_path=get_pcd_path
        self.record_func=record_func
        self.interval=interval
        self.capture_pcd_path = os.path.join(self.pcd_path,f"{ip.replace('.','_')}.pcd")
        self.capture_pcd_command = f'"{get_pcd_path}" --lidar-ip {ip} --lidar-udp-port 8010 --frame-number 1 --output-filename "{self.capture_pcd_path}"'
        self.get_pcd_out = os.path.join(self.pcd_path,f"{ip}_out.log")
        self.get_pcd_err = os.path.join(self.pcd_path,f"{ip}_err.log") 
        if not os.path.exists(self.pcd_path):
            os.makedirs(self.pcd_path)
        if not os.path.exists(self.report_path):
            os.makedirs(self.report_path)
        self.report_path = os.path.join(self.report_path,f"{ip}.csv")
        if not os.path.exists(self.report_path):
            csv_write(self.report_path,pointcloud_header)
        
    @handle_exceptions
    def run(self):
        while True:
            if ping(self.ip,3):
                break
            if self.isInterruptionRequested():
                return
        LidarTool.set_pcs(self.ip,True)
        while True:
            t=time.time()
            if self.isInterruptionRequested():
                break
            if os.path.exists(self.capture_pcd_path):
                os.remove(self.capture_pcd_path)
            cmd=subprocess.Popen(self.capture_pcd_command,shell=True,stdout=open(self.get_pcd_out,"w"),stderr=open(self.get_pcd_err,"a"))
            cmd.wait()
            if not os.path.exists(self.capture_pcd_path):
                print(f"{self.ip} capture pcd fail")
                continue
            else:
                df = read_pcd(self.capture_pcd_path)
                res = self.record_func(df,self.ip,self.pcd_path)
                self.sigout_pointcloud.emit(res,self.row_idx)
                csv_write(self.report_path,res)
            sleep_time=self.interval-time.time()+t
            if sleep_time>0:
                time.sleep(sleep_time)            
    
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"{self.ip} try finish monitor pointcloud")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        print(f"pointcloud thread finish success")





class TestMain(QThread):
    sigout_test_finish = pyqtSignal(str)
    sigout_lidar_info=pyqtSignal(list,int)
    sigout_pointcloud=pyqtSignal(list,int)
    sigout_schedule=pyqtSignal(int,int)
    sigout_set_fault=pyqtSignal(str,int)
    sigout_heal_fault=pyqtSignal(str,int)
    sigout_plot_data = pyqtSignal(list,str)
    sigout_power=pyqtSignal(bool)
    
    
    def __init__(self,can_mode,relay_channel,ip_list,record_folder,record_header,times,record_func,record_interval,off_counter,timeout,lidar_mode,pointcloud_func,pointcloud_header):
        super(TestMain,self).__init__()
        self.record_interval=record_interval
        self.lidar_mode=lidar_mode
        self.relay_channel = relay_channel
        self.save_folder=record_folder
        self.ip_list=ip_list
        self.timeout=timeout
        self.record_header=record_header
        self.off_counter=off_counter
        self.times=times
        self.record_func=record_func
        self.can_mode=can_mode
        self.pointcloud_func=pointcloud_func
        self.pointcloud_header=pointcloud_header
    
    def send_lidar_info(self,list1,row_idx):
        self.sigout_lidar_info.emit(list1,row_idx)
    
    def set_fault(self,fault,row_idx):
        self.sigout_set_fault.emit(fault,row_idx)
    
    def heal_fault(self,fault,row_idx):
        self.sigout_heal_fault.emit(fault,row_idx)
    
    def send_pointcloud_info(self,res,row_idx):
        self.sigout_pointcloud.emit(res,row_idx)
    
    def send_current_info(self,value,ip):
        self.sigout_plot_data.emit(value,ip)
    
    def run_monitor(self,log_path,time_path):
        self.records=[]
        self.monitors=[]
        self.dsps=[]
        self.pointclouds=[]
        self.currents=[]
        pointcloud_report_path = os.path.join(self.save_folder,"pointcloud")
        pcd_save_folder = os.path.join(self.util_dir,"pcd")
        for ip_num,ip in enumerate(self.ip_list):
            print(f"start add record {ip}")
            record_thread=one_lidar_record_thread(ip,float(self.record_interval),self.save_folder,self.record_header,ip_num,self.record_func)
            record_thread.sigout_set_tbw_value.connect(self.send_lidar_info)
            record_thread.start()
            self.records.append(record_thread)
            print(f"start add record success {ip}")
            raw_save_path=os.path.join(log_path,"raw",ip.replace(".","_"),time_path)
            monitor_thread=MonitorFault(ip,log_path,raw_save_path,ip_num,9600+ip_num,9100+ip_num,8600+ip_num,8100+ip_num,8010)
            monitor_thread.sigout_fault_info.connect(self.set_fault)
            monitor_thread.sigout_fault_heal.connect(self.heal_fault)
            monitor_thread.start()
            self.monitors.append(monitor_thread)
            print(f"start add fault monitor success {ip}")
            if os.getenv("dsp")=="True":
                dsp_thread=DSP_info_thread(ip,self.save_folder)
                dsp_thread.start()
                self.dsps.append(dsp_thread)
                print(f"start add dsp success {ip}")
            if os.getenv("pointcloud")=="True":
                pointcloud_thread=PointCloud(ip,ip_num,pointcloud_report_path,pcd_save_folder,self.get_pcd_path,float(self.record_interval),self.pointcloud_func,self.pointcloud_header)
                pointcloud_thread.sigout_pointcloud.connect(self.send_pointcloud_info)
                pointcloud_thread.start()
                self.pointclouds.append(pointcloud_thread)
                print(f"start add pointcloud success {ip}")
            
    
    def stop_monitor(self):
        if hasattr(self,"monitors"):
            print("start stop monitor fault")
            for monitor in self.monitors:
                if monitor.isRunning():
                    monitor.stop()
        if hasattr(self,"records"):
            print("start stop record")
            for record in self.records:
                if record.isRunning():
                    record.stop()
        if hasattr(self,"dsps"):
            print("start dsp record")
            for dsp_thread in self.dsps:
                if dsp_thread.isRunning():
                    dsp_thread.stop()
        if hasattr(self,"pointclouds"):
            print("start stop pointcloud")
            for pointcloud in self.pointclouds:
                if pointcloud.isRunning():
                    pointcloud.stop()
        if hasattr(self,"currents"):
            print("start stop current")
            for current in self.currents:
                if current.isRunning():
                    current.stop()
    
    @handle_exceptions
    def one_cycle(self,power_one_time,i,data_num_power_off,log_path):
        self.sigout_power.emit(True)
        print(f"current circle {i}")
        t=time.time()
        self.power_monitor.pause()
        set_power_status(power_one_time[2],power_on=True)
        sleep_time = int(power_one_time[0]-time.time()+t)
        print(f"start monitor {sleep_time}s")
        time_path=get_time()
        if os.getenv("relay")=="True":
            os.system("python3 can_run.py -c switch")
            os.environ["resistor"] = "0.1"
        if self.lidar_mode=="CAN":
            self.cmd_can=subprocess.Popen(f'exec python3 can_run.py -c {self.can_mode}',shell=True)
        self.power_monitor.resume()
        if sleep_time>2:
            self.run_monitor(log_path,time_path)
            sleep_time = power_one_time[0]-time.time()+t
            if sleep_time > 0:
                time.sleep(sleep_time)
            threads=[]
            print("start download lidar log")
            for ip in self.ip_list:
                thread=threading.Thread(target=downlog,args=(ip,log_path,time_path,))
                thread.start()
                threads.append(thread)
            for temp_thread in threads:
                temp_thread.join()
            self.stop_monitor()
        self.sigout_power.emit(False)
        if self.lidar_mode=="CAN":
            self.cmd_can.kill()
            self.kill_cmd_can=subprocess.Popen(f'exec python3 can_cancle.py -c {self.can_mode}',shell=True)
            self.kill_cmd_can.wait()
            if os.getenv("relay")=="True":
                os.system("python3 can_cancle.py -c switch")
                os.environ["resistor"] = "7500"
        else:
            self.power_monitor.pause()
            set_power_status(None,power_on=False)
            self.power_monitor.resume()
        kill_client()
        print(f"start sleep {int(power_one_time[0]+power_one_time[1]-(time.time()-t))}s")
        if self.cmd_anlyze_log.poll() is not None:
            print("continue analyse log")
            kill_subprocess("log_main.py")
            self.cmd_anlyze_log = subprocess.Popen(self.analyse_command,shell=True)
        for i in range(data_num_power_off):
            temp_pow=pow_status
            for row_idx,ip in enumerate(self.ip_list):
                csv_save_path = os.path.join(self.save_folder,'record_'+ip.replace('.','_')+'.csv')
                if self.lidar_mode=="CAN":
                    temp=[f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"]+[-100]*(self.record_header.count(",")-2)+temp_pow
                else:
                    temp=[f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"]+[-100]*(self.record_header.count(","))
                self.sigout_lidar_info.emit(temp,row_idx)
                if not os.path.exists(csv_save_path):
                    csv_write(csv_save_path,self.record_header)
                csv_write(csv_save_path,temp)
            t0=(power_one_time[0]+power_one_time[1]-(time.time()-t))/(data_num_power_off-i)
            if t0>0:
                time.sleep(t0)

    @handle_exceptions
    def run(self):
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
        if os.getenv("current")=="True":
            os.environ["resistor"] = "0.1"
            self.current_monitor = Current_monitor(self.ip_list,self.relay_channel,float(self.record_interval),self.save_folder,3)
            self.current_monitor.sigout_plot_data.connect(self.send_current_info)
            self.current_monitor.start()
            print(f"start add current monitor success")
        self.analyse_command = f'python3 utils/log_main.py -f "{os.path.join(self.save_folder,"client_log")}" -c -o "{os.path.join(self.save_folder,"fault_result")}"'
        print(self.analyse_command)
        print(f"start analyse log")
        self.cmd_anlyze_log = subprocess.Popen(self.analyse_command,shell=True)
        self.util_dir="lidar_util"
        if "linux" in platform.platform().lower():
            util_name="innovusion_lidar_util"
            get_pcd_name="get_pcd"
        elif "windows" in platform.platform().lower():
            util_name="innovusion_lidar_util.exe"
            get_pcd_name="get_pcd.exe"
        self.util_path=os.path.join(self.util_dir,util_name)
        self.get_pcd_path=os.path.join(self.util_dir,get_pcd_name)
        kill_client()
        if self.record_interval.strip()=="":
            print(f"please input record interval time")
            return None
        if self.off_counter.strip()=="":
            print(f"please input power off empty data number")
            return None
        print(f"get inno_pc_client permission")
        os.system('echo demo|sudo -S chmod 777 lidar_util/inno_pc_client')
        if self.lidar_mode!="No Power":
            set_power_status(None,power_on=True)
        if self.lidar_mode=="CAN":
            if os.getenv("relay")=="True":
                os.system("python3 can_run.py -c switch")
                os.environ["resistor"] = "0.1"
            os.system("python3 lib/set_usbcanfd_env.py demo")
            subprocess.Popen(f'exec python3 can_run.py -c {self.can_mode}',shell=True)
        for idx,ip in enumerate(self.ip_list):
            ping_sure(ip,3)
            while True:
                try:
                    down_count=0
                    while True:
                        if down_sdk(ip) or down_count>10:
                            break
                        down_count+=1
                    LidarTool.extend_pcs_log_size(self.util_path,ip,2000)
                    LidarTool.open_broadcast(self.util_path,ip,9600+idx)
                    LidarTool.get_promission(ip,float(self.timeout))
                    LidarTool.set_network(ip,ip)
                    LidarTool.open_ptp(ip)
                    if self.lidar_mode=="CAN":
                        while True:
                            if set_lidar_mode(ip,"can",self.can_mode):
                                break
                    break
                except Exception as e:
                    print(e)
            LidarTool.reboot_lidar(ip) 
        if self.lidar_mode!="No Power":
            self.power_monitor=Power_monitor()
            self.power_monitor.start()
            set_power_status(None,power_on=False)
            os.system(f'python3 can_cancle.py -c {self.can_mode}')
            time.sleep(30) # in order to make sure lidar set can mode success
            i=1
            for time_one in self.times:
                self.sigout_schedule.emit(i,len(self.times))
                self.one_cycle(time_one,i,int(self.off_counter),self.save_folder)
                i+=1 
            self.power_monitor.stop()
            if os.getenv("current")=="True":
                self.current_monitor.stop()
            if self.lidar_mode=="CAN":
                if os.getenv("relay")=="True":
                    os.system("python3 can_run.py -c switch")
                    os.environ["resistor"] = "0.1"
                cancle_can(self.ip_list,self.can_mode)
            set_power_status(None,power_on=False)
            rm_empty_folder(self.save_folder)
            print("start continue analyze log")
            kill_subprocess("log_main.py")
            cmd = subprocess.Popen(self.analyse_command + " -r",shell=True)
            cmd.wait()
            self.sigout_test_finish.emit(self.util_path)
        else:
            time_path=get_time()
            self.run_monitor(self.save_folder,time_path)
            while True:
                if self.isInterruptionRequested():
                    break
                time.sleep(5)
        
    
    @handle_exceptions
    def stop(self):
        self.requestInterruption()
        self.stop_monitor()
        if self.lidar_mode=="CAN":
            if hasattr(self,"cmd_can"):
                try:
                    self.cmd_can.kill()
                except:
                    pass
            if hasattr(self,"kill_cmd_can"):
                try:
                    self.kill_cmd_can.kill()
                except:
                    pass
        if hasattr(self,"power_monitor"):
            try:
                self.power_monitor.stop()
            except:
                pass
        if hasattr(self,"current_monitor"):
            try:
                self.current_monitor.stop()
            except:
                pass
        t=time.time()
        while self.isRunning():
            print(f"try finish test")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        kill_client()
        if self.lidar_mode=="CAN":
            os.system(f'exec python3 can_cancle.py -c {self.can_mode}')
        elif self.lidar_mode=="No Power":
            threads=[]
            time_path=get_time()
            print(f"start download log")
            for ip in self.ip_list:
                if ping(ip,0.5):
                    thread=threading.Thread(target=downlog,args=(ip,self.save_folder,time_path,))
                    thread.start()
                    threads.append(thread)
            for temp_thread in threads:
                temp_thread.join()
            print(f"remove empty folder")
            rm_empty_folder(self.save_folder)
            print("start continue analyze log")
            kill_subprocess("log_main.py")
            cmd = subprocess.Popen(self.analyse_command + " -r -mtc 6",shell=True)
            cmd.wait()
            self.sigout_test_finish.emit(self.util_path)
        print(f"Test has been stop")

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

        
class MainCode(QMainWindow,userpage.Ui_MainWindow):
    @handle_exceptions
    def __init__(self):
        QMainWindow.__init__(self)
        userpage.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.log_rows = 0
        self.lb_version.setText(f"Version:  {get_tags()}")
        
        self.project_folder="./project"
        self.test_folder="./test_config"
        self.power_folder="./power"
        self.logo_path = "config/Seyond Black Horizontal RGB.jpg"
        
        self.timer = QTimer()
        
        self.cb_project.currentIndexChanged.connect(self.project_changed)
        self.cb_test_name.currentIndexChanged.connect(self.test_name_changed)
        self.cb_power_type.currentIndexChanged.connect(self.power_changed)
        self.cb_lidar_mode.currentIndexChanged.connect(self.lidar_mode_changed)
        self.btn_start.clicked.connect(self.test_main)
        self.btn_cancle_can.clicked.connect(self.cancle_can_mode)
        self.btn_stop.clicked.connect(self.test_stop)
        self.btn_tool_start.clicked.connect(self.update_mac_adress)
        self.init_select_item()
    
        self.cb_can_mode.setEnabled(False)
        self.lb_logo.setPixmap(QPixmap(self.logo_path))
        
        IntValidator = QIntValidator(0,100000)
        DoubleValidator = QDoubleValidator(0,100000,3,notation=QtGui.QDoubleValidator.StandardNotation)
        self.txt_timeout.setValidator(DoubleValidator)
        self.txt_record_interval.setValidator(DoubleValidator)
        self.txt_off_counter.setValidator(IntValidator)
        
        self.scrollArea_list=[]      
    
        self.action_lidar_status.triggered.connect(self.stackedWidget_currentChanged(0,self.stackedWidget_lidar,self.lb_lidar,"Lidar status"))
        self.action_lidar_pointcloud.triggered.connect(self.stackedWidget_currentChanged(1,self.stackedWidget_lidar,self.lb_lidar,"Lidar pointcloud"))
        self.action_Fault.triggered.connect(self.stackedWidget_currentChanged(0,self.stackedWidget_current,self.lb_current,"Fault Status"))
        self.action_Current.triggered.connect(self.stackedWidget_currentChanged(1,self.stackedWidget_current,self.lb_current,"Current Status"))
        self.action_Mac_Adress.triggered.connect(self.stackedWidget_currentChanged(2,self.stackedWidget_current,self.lb_current,"Update Mac Address"))
        
        self.action_Fault.trigger()
        self.action_lidar_status.trigger()
        
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

    
    def stackedWidget_currentChanged(self,idx,stacked_object,lb_object,label_name):
        def changed_idx():
            stacked_object.setCurrentIndex(idx)
            lb_object.setText(label_name)
        return changed_idx
    
    def write(self, info):
        self.txt_log.insertPlainText(info)
        if len(info):
            self.txt_log.setText(info)
            QtWidgets.qApp.processEvents(
                QtCore.QEventLoop.ExcludeUserInputEvents | QtCore.QEventLoop.ExcludeSocketNotifiers)
            self.stdoutbak.write(info)

    def normalOutputWritten(self, text):
        if self.log_rows>50000:
            self.txt_log.clear()
            self.log_rows=0
        self.txt_log.append(text.strip('\n'))
        self.cursor=self.txt_log.textCursor()
        self.txt_log.moveCursor(self.cursor.End) 
        QtWidgets.QApplication.processEvents()
        self.log_rows+=1
    
    @handle_exceptions
    def update_mac_adress(self):
        ip = self.txt_lidar_ip.text()
        mac_adress = self.txt_mac_adress.text()
        new_ip = self.txt_lidar_ip_new.text()
        if not re.search("^\d+\.\d+\.\d+\.\d+$",ip):
            print(f"please input correct ip")
            return
        if not re.search("^([A-Fa-f0-9]{2}[:\s]{1}){5}[A-Fa-f0-9]{2}$",mac_adress):
            print(f"please input correct mac adress")
            return
        if not ping(ip,1):
            print(f"{ip} can't connect")
            return
        LidarTool.update_mac_adress(ip,mac_adress)
        if not re.search("^\d+\.\d+\.\d+\.\d+$",new_ip):
            print(f"new ip format error, not update")
        else:
            LidarTool.set_network(ip,new_ip)
    
    @handle_exceptions
    def clear_scroll_area(self,scroll_area):
        if scroll_area.widget()==None:
            return
        scroll_contents = scroll_area.widget()
        # 清空内容小部件中的子控件
        for child_widget in scroll_contents.findChildren(QWidget):
            child_widget.setParent(None)
            child_widget.deleteLater()
        # 移除内容小部件
        scroll_area.takeWidget()
    
    
    @handle_exceptions
    def init_plot_widget(self):
        self.widget_plot_dict = {}
        global widget_width,widget_height
        self.clear_scroll_area(self.scrollArea_current)
        widget_counts=len(self.ip_list)
        self.scrollArea_contents_current.setMinimumSize(widget_width+30,widget_height*widget_counts)
        for idx,ip in enumerate(self.ip_list):
            qwidget=QtWidgets.QWidget(self.scrollArea_contents_current)
            qwidget.setGeometry(QtCore.QRect(10, widget_height*idx, widget_width-30, widget_height))
            self.widget_plot_dict[ip] = Plot_Widget(qwidget,f"{ip}")
        self.scrollArea_current.setWidget(self.scrollArea_contents_current)
    
    @handle_exceptions
    def update_test_time(self):
        time_s=TimeConvert.hms2time(self.lb_test_time.text())
        time_s+=1
        hms=TimeConvert.time2hms(time_s)
        self.lb_test_time.setText(hms)
    
    
    @handle_exceptions
    def init_table(self,row_counter,columns_status,columns_pointcloud):
        columns_status=["Lidar_IP"]+list(columns_status)
        columns_pointcloud=["Lidar_IP"]+list(columns_pointcloud)
        
        for row_num in range(self.tbw_data.rowCount(),-1,-1):
            self.tbw_data.removeRow(row_num)
        for row_num in range(self.tbw_fault.rowCount(),-1,-1):
            self.tbw_fault.removeRow(row_num)
        for row_num in range(self.tbw_pointcloud.rowCount(),-1,-1):
            self.tbw_pointcloud.removeRow(row_num)    
            
        self.tbw_data.setColumnCount(len(columns_status))
        self.tbw_pointcloud.setColumnCount(len(columns_pointcloud))
        self.tbw_fault.setColumnCount(1)
        
        for j in range(len(columns_status)):
            self.tbw_data.setHorizontalHeaderItem(j, QtWidgets.QTableWidgetItem())
            self.tbw_data.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeToContents)
            item = self.tbw_data.horizontalHeaderItem(j)
            item.setText(f"{columns_status[j]}")
        for j in range(len(columns_pointcloud)):
            self.tbw_pointcloud.setHorizontalHeaderItem(j, QtWidgets.QTableWidgetItem())
            self.tbw_pointcloud.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeToContents)
            item = self.tbw_pointcloud.horizontalHeaderItem(j)
            item.setText(f"{columns_pointcloud[j]}")
        
        
        
        self.tbw_fault.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
        self.tbw_fault.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        item = self.tbw_fault.horizontalHeaderItem(0)
        item.setText("Lidar_IP")
        
        
        for i in range(row_counter):
            self.tbw_data.insertRow(i)
            self.tbw_fault.insertRow(i)
            self.tbw_pointcloud.insertRow(i)
            self.tbw_data.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_pointcloud.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_fault.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_fault.setItem(i,0,QtWidgets.QTableWidgetItem(self.ip_list[i]))
            for j in range(len(columns_status)):
                if j==0:
                    cell_value=self.ip_list[i]
                else:
                    cell_value=""
                self.tbw_data.setItem(i,j,QtWidgets.QTableWidgetItem(cell_value))
            for j in range(len(columns_pointcloud)):
                if j==0:
                    cell_value=self.ip_list[i]
                else:
                    cell_value=""
                self.tbw_pointcloud.setItem(i,j,QtWidgets.QTableWidgetItem(cell_value))
        
    
    @handle_exceptions
    def report_fault(self,fault,row_idx):
        self.set_fault(fault,row_idx)
        for col_idx in range(self.tbw_fault.columnCount()):
            if  self.tbw_fault.horizontalHeaderItem(col_idx).text()==fault:
                if self.tbw_fault.item(row_idx,col_idx)!=None:
                    last_fault_count=self.tbw_fault.item(row_idx,col_idx).text()
                    if re.search("\d+",last_fault_count):
                        self.tbw_fault.setItem(row_idx,col_idx,QtWidgets.QTableWidgetItem(f"{int(last_fault_count)+1}"))
                        
                        return
                self.tbw_fault.setItem(row_idx,col_idx,QtWidgets.QTableWidgetItem(f"{1}"))
                return
        last_max_col=self.tbw_fault.columnCount()
        self.tbw_fault.setColumnCount(last_max_col+1)
        self.tbw_fault.setHorizontalHeaderItem(last_max_col, QtWidgets.QTableWidgetItem())
        self.tbw_fault.horizontalHeader().setSectionResizeMode(last_max_col, QHeaderView.ResizeToContents)
        item = self.tbw_fault.horizontalHeaderItem(last_max_col)
        item.setText(f"{fault}")
        self.tbw_fault.setItem(row_idx,last_max_col,QtWidgets.QTableWidgetItem(f"{1}"))
        
    @handle_exceptions
    def set_fault(self,fault,row_idx):
        fault_name_width=185
        if fault not in self.scrollArea_list:
            self.scrollArea_list.append(fault)
            self.scrollArea_fault.takeWidget()
            self.scrollArea_contents_fault.setMinimumSize(fault_name_width+19+40*len(self.ip_list),20+30*len(self.scrollArea_list))
            label=QtWidgets.QLabel(self.scrollArea_contents_fault)
            label.setGeometry(QtCore.QRect(10,30*len(self.scrollArea_list)-10,fault_name_width,21))
            label.setText(fault)
            setattr(self,f"lb_{fault}",label)            
            for idx,ip in enumerate(self.ip_list):
                label=QtWidgets.QLabel(self.scrollArea_contents_fault)
                label.setGeometry(QtCore.QRect(fault_name_width+19+40*idx, 30*len(self.scrollArea_list)-10, 21, 21))
                label.setText("")
                label.setStyleSheet("border-radius:10px;background-color:rgb(0, 0, 0)")
                setattr(self,f"lb_{fault}_{idx}",label)
            self.scrollArea_fault.setWidget(self.scrollArea_contents_fault)
        getattr(self,f"lb_{fault}_{row_idx}").setStyleSheet("border-radius:10px;background-color:rgb(255, 0, 0)")

    @handle_exceptions
    def heal_fault(self,fault,row_idx):
        if fault in self.scrollArea_list:
            getattr(self,f"lb_{fault}_{row_idx}").setStyleSheet("border-radius:10px;background-color:rgb(115, 210, 22)")
    
    def init_select_item(self):
        self.cb_project.clear()
        self.cb_test_name.clear()
        for project in sorted(os.listdir(self.project_folder)):
            ret=re.search("^(.+)\.py",project)
            if ret:
                self.cb_project.addItem(ret.group(1))
        for test_name in sorted(os.listdir(self.test_folder)):  # may can be json file, but no explain
            ret=re.search("^(.+)\.py",test_name)
            if ret:
                self.cb_test_name.addItem(ret.group(1))
        for power_type in sorted(os.listdir(self.power_folder)):
            ret=re.search("^power_(.+)\.py$",power_type)
            if ret:
                self.cb_power_type.addItem(ret.group(1))
    
    @handle_exceptions
    def power_changed(self):
        print(f"current power is {self.cb_power_type.currentText()},please ensure has connect!")
        os.environ["power_type"]=self.cb_power_type.currentText()
        if os.path.exists("power.py"):
            os.remove("power.py")
        shutil.copyfile(os.path.join(self.power_folder,f"power_{self.cb_power_type.currentText()}.py"),os.path.join(os.getcwd(),"power.py"))
    
    def lidar_mode_changed(self):
        if self.cb_lidar_mode.currentText()=="No Power":
            self.cb_power_type.setEnabled(False)
        else:
            self.cb_power_type.setEnabled(True)
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cb_can_mode.setEnabled(True)
        else:
            self.cb_can_mode.setEnabled(False)
        os.environ["lidar_mode"]=self.cb_lidar_mode.currentText()
            
    
    def power_status(self,mode):
        if mode:
            self.lb_power_status.setStyleSheet("border-radius:10px;background-color:rgb(115, 210, 22)")
        else:
            self.lb_power_status.setStyleSheet("border-radius:10px;background-color:rgb(255, 0, 0)")
    
    @handle_exceptions
    def test_name_changed(self):
        if self.cb_test_name.currentText().strip()!="":
            cfg_file = os.path.join(self.test_folder,f"{self.cb_test_name.currentText()}.py")
            os.environ["test_name"]=self.cb_test_name.currentText()
            try:
                with open(cfg_file,"r",encoding="utf-8") as f:
                    exec(f.read())
                exec("self.test_config=config")
            except Exception as e:
                print(f"read test config error:{e}")
            self.save_folder=self.cb_test_name.currentText()
            self.read_config()
    
    @handle_exceptions
    def project_changed(self):
        if self.cb_project.currentText().strip()!="":
            os.environ["project"]=self.cb_project.currentText()
            mata_class=importlib.import_module(f"{self.project_folder.strip('.').strip('/')}.{self.cb_project.currentText()}")
            self.record_header=mata_class.record_header
            self.record_func=mata_class.one_record
            self.pointcloud_func=mata_class.pointcloud_analyze
            self.pointcloud_header=mata_class.pointcloud_header
            self.read_config()

    def read_config(self):
        if hasattr(self,"test_config"):
            self.ip_list=self.test_config["lidar_ip"]
            if "channel" in self.test_config.keys():
                self.relay_channel = self.test_config["channel"]
            else:
                self.relay_channel = 1
            self.init_plot_widget()
            self.times=get_circle_time(self.test_config["time_dict"])
            self.init_table(len(self.ip_list),self.record_header.split(","),self.pointcloud_header)
        self.scrollArea_contents_fault = QtWidgets.QWidget()
        self.scrollArea_contents_fault.setGeometry(QtCore.QRect(0, 0, 485, 795))
        self.scrollArea_contents_fault.setObjectName("scrollAreaWidgetContents")
        self.scrollArea_fault.setWidget(self.scrollArea_contents_fault)
        self.scrollArea_list=[]
    
    def plot_figure_data(self,value,ip):
        self.widget_plot_dict[ip].updateData(value)
    
    @handle_exceptions
    def test_main(self):
        os.environ["test_finished"] = "False"
        if self.txt_off_counter.text().strip()=="":  #setReadOnly(True)
            print(f"please input power off empty data number")
            return        
        if self.txt_record_interval.text().strip()=="":  #setReadOnly(True)
            print(f"please input record interval time")
            return
        if self.txt_timeout.text().strip()=="":  #setReadOnly(True)
            print(f"please input timeout")
            return
        self.btn_start.setEnabled(False)
        self.pgb_test.setValue(0)
        self.lb_test_time.setText("00:00:00")
        self.timer.start(1000)
        self.timer.timeout.connect(self.update_test_time)
        print(f"{self.lb_version.text()},Lidar mode:{self.cb_lidar_mode.currentText()}, Powers:{self.cb_power_type.currentText()}, Project:{self.cb_project.currentText()},Test name:{self.cb_test_name.currentText()},CAN mode:{self.cb_can_mode.currentText()},Off counter:{self.txt_off_counter.text()},Interval:{self.txt_record_interval.text()}s,Relay:{self.relay.isChecked()},DSP:{self.dsp.isChecked()},pointcloud:{self.cb_pointcloud.isChecked()},Timeout:{self.txt_timeout.text()}s")
        os.environ["relay"]=str(self.relay.isChecked())
        os.environ["dsp"]=str(self.dsp.isChecked())
        os.environ["pointcloud"]=str(self.cb_pointcloud.isChecked())
        os.environ["current"]=str(self.cb_current.isChecked())
        self.test=TestMain(self.cb_can_mode.currentText(),self.relay_channel,self.ip_list,self.save_folder,self.record_header,self.times,self.record_func,self.txt_record_interval.text(),self.txt_off_counter.text(),self.txt_timeout.text(),self.cb_lidar_mode.currentText(),self.pointcloud_func,self.pointcloud_header)
        self.test.sigout_test_finish.connect(self.test_finish)
        self.test.sigout_lidar_info.connect(set_tbw_value(self.tbw_data))
        self.test.sigout_pointcloud.connect(set_tbw_value(self.tbw_pointcloud))
        self.test.sigout_schedule.connect(self.set_schedule)
        self.test.sigout_heal_fault.connect(self.heal_fault)
        self.test.sigout_set_fault.connect(self.report_fault)
        self.test.sigout_power.connect(self.power_status)
        self.test.sigout_plot_data.connect(self.plot_figure_data)
        self.test.start()
        self.test_set_off()
    
    @handle_exceptions
    def test_finish(self,util_path):
        self.save_tbw_fault()
        if hasattr(self,"timer"):
            self.timer.stop()
            try:
                self.timer.timeout.disconnect(self.update_test_time)
            except:
                pass
        print(f"recover udp port")
        if self.cb_lidar_mode.currentText()!="No Power":
            print("power on")
            set_power_status(None,power_on=True)
        for idx,ip in enumerate(self.ip_list):
            while True:
                if ping(ip,3):
                    break   
                else:
                    print(f"ping {ip} failed in recover network")
                if os.getenv("test_finished") == "True":
                    return
            LidarTool.open_broadcast(util_path,ip,8010)
        if self.cb_lidar_mode.currentText()!="No Power":
            print("power off")
            set_power_status(None,power_on=False)
        self.test_set_on()
        print(f"Test finished")
    
    def test_set_off(self):
        self.cb_lidar_mode.setEnabled(False)
        self.cb_project.setEnabled(False)
        self.cb_test_name.setEnabled(False)
        self.cb_power_type.setEnabled(False)
        self.cb_can_mode.setEnabled(False)
        self.txt_off_counter.setEnabled(False)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(False)
        self.txt_timeout.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_cancle_can.setEnabled(False)
        self.relay.setEnabled(False)
        self.dsp.setEnabled(False)
        self.cb_pointcloud.setEnabled(False)
        self.cb_current.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def test_set_on(self):
        self.cb_lidar_mode.setEnabled(True)
        self.cb_project.setEnabled(True)
        self.cb_test_name.setEnabled(True)
        if self.cb_lidar_mode.currentText()!="No Power":
            self.cb_power_type.setEnabled(True)
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cb_can_mode.setEnabled(True)
        self.txt_off_counter.setEnabled(True)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(True)
        self.txt_timeout.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_cancle_can.setEnabled(True)
        self.relay.setEnabled(True)
        self.dsp.setEnabled(True)
        self.cb_pointcloud.setEnabled(True)
        self.cb_current.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    @handle_exceptions
    def set_schedule(self,current_counter,sum_counter):
        str1=f"{round(current_counter*100/sum_counter,1)}%"
        # self.lb_schedule.setText(f"Test Schedule: {str1}")
        self.pgb_test.setValue(math.floor(current_counter*10000/sum_counter))
        self.pgb_test.setFormat(str1)
    
    @handle_exceptions
    def test_stop(self):
        self.btn_stop.setEnabled(False)
        os.environ["test_finished"] = "True"
        if hasattr(self,"test"):
            self.test.stop()
        if hasattr(self,"timer"):
            self.timer.stop()
            try:
                self.timer.timeout.disconnect(self.update_test_time)
            except:
                pass
        self.test_set_on()
    
    @handle_exceptions
    def save_tbw_fault(self):
        headers=[]
        for col_idx in range(self.tbw_fault.columnCount()):
            headers.append(self.tbw_fault.horizontalHeaderItem(col_idx).text())
        df=pd.DataFrame([],columns=headers)
        for row_idx in range(self.tbw_fault.rowCount()):
            row=[]
            for col_idx in range(self.tbw_fault.columnCount()):
                if self.tbw_fault.item(row_idx,col_idx)!=None:
                    if col_idx!=0:
                        row.append(int(self.tbw_fault.item(row_idx,col_idx).text()))
                    else:
                        row.append(self.tbw_fault.item(row_idx,col_idx).text())
                else:
                    row.append(0)
            df.loc[self.ip_list[row_idx],:]=row
        df.to_excel(os.path.join(self.save_folder,"fault_counter.xlsx"),sheet_name="fault",index=None)
        ef=ExcelFormat(os.path.join(self.save_folder,"fault_counter.xlsx"))
        ef.format()
    
    def cancle_can_mode(self):
        cancle_can(self.ip_list,self.cb_can_mode.currentText())
    
        
    
        
if __name__ == '__main__':
    log_folder="./python_log"
    log_file=os.path.join(log_folder,get_current_date()+".log")
    builtins.print=rewrite_print(log_file)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    window = MainCode()
    window.show()
    sys.exit(app.exec_())

