# /**
#  * @author katewutao
#  * @email [kate.wu@cn.innovuison.com]
#  * @create date 2023-05-05 10:12:54
#  * @modify date 2023-05-17 10:12:54
#  * @desc [description]
#  */
import os
import sys
import time
import typing
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
import shutil,json,importlib
from auto_update_sdk import down_sdk
import ctypes,inspect,select,math
from threading import Thread

pow_status=[0,0]

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
 
 
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

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
                print(f"[{datetime.datetime.now()}] {function.__name__} time out")
            return t.result
        return decorator2
    return decorator

def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            sig = inspect.signature(func)
            num_args = len(sig.parameters)
            if num_args == len(args):
                result = func(*args)
            else:
                instance = args[0]
                result = func(instance, **kwargs)
            return result
        except Exception as e:
            traceback.print_exc()
            print(f"Error occurred while executing {func.__name__}: {e}")
            return None
    return wrapper

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
    command1=f"sshpass -p 4920lidar scp -rp root@{ip}:/tmp '{save_path}'"
    command2=f"sshpass -p 4920lidar scp -rp root@{ip}:/mnt '{save_path}'"
    cmd1=subprocess.Popen(command1,shell=True)
    cmd2=subprocess.Popen(command2,shell=True)
    cmd1.wait()
    cmd2.wait()

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
    while not flag:
        print(f'[{datetime.datetime.now()}] please connect lidar {ip}')
        flag=ping(ip,interval_time)
    print(f'[{datetime.datetime.now()}] lidar {ip} has connected')    
    
def get_promission(ip,time_out):
    if 'windows' not in platform.platform().lower():
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
    cmd=subprocess.Popen(command,shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)
    res=cmd.communicate()
    if "dsp boot from can: OK" in res[0]:
        print(f"[{datetime.datetime.now()}] {ip} set can mode success")
        return True
    else:
        print(f"[{datetime.datetime.now()}] {ip} set can mode fail")
        set_can(ip)


def set_power(ip):
    command=f'echo "dsp_boot_from power" | nc -nv {ip} 8001'
    cmd=subprocess.Popen(command,shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE,universal_newlines=True)
    res=cmd.communicate()
    
    if "dsp boot from power: OK" in res[0]:
        print(f"[{datetime.datetime.now()}] {ip} set power mode success")
        return True
    else:
        print(f"[{datetime.datetime.now()}] {ip} set power mode fail")
        set_power(ip)


def cancle_can(ip_list):
    os.system("python3 ./power.py")
    os.system("python3 lib/set_usbcanfd_env.py demo")
    print(f"[{datetime.datetime.now()}] start set lidar power mode")
    subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
    for ip in ip_list:
        ping_sure(ip,0.5)
        set_power(ip)
    os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk -F ' ' '{print $2}'|xargs kill -9")
    print(f"[{datetime.datetime.now()}] all lidar cancle can mode success")
    
    
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


def kill_client():
    command="exec ps -ef|grep inno_pc_client|grep -v grep|awk '{print $2}'|xargs kill -9"
    # print(command)
    print(f"[{datetime.datetime.now()}] kill client")
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
                if isinstance(temp,list) and len(temp)==2:
                    pow_status=temp
            except:
                try:
                    pow=power.Power()
                except:
                    print(f"retry get power output value")
    
    @handle_exceptions
    def pause(self):
        print(f"[{datetime.datetime.now()}] power monitor pause")
        self.thread_run=False
    
    @handle_exceptions
    def resume(self):
        print(f"[{datetime.datetime.now()}] power monitor continue")
        self.thread_run=True
        
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"[{datetime.datetime.now()}] try finish monitor power")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        print(f"[{datetime.datetime.now()}] finish monitor power success")
        
        
        
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
    

    def get_customerid(self):
        import socket
        customerid = 'null'
        command = 'mfg_rd "CustomerSN"\n'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, 8002))
        s.settimeout(1)
        s.sendall(command.encode())
        try:
            data=s.recv(1024)
            lst = data.decode('ascii').split('\n')
            for s in lst:
                ret=re.search('CustomerSN.*?:\s*[\'|"](.+)[\'|"]',s)
                if ret:
                    customerid=ret.group(1)
                    break
        except Exception as e:
            print(e)
            customerid=self.get_customerid()
        return customerid 


    def get_sn(self):
        command=f"curl {self.ip}:8010/command/?get_sn"
        cmd = subprocess.Popen(command, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
        
        res=cmd.communicate()
        SN=res[0]
        if SN=="":
            return self.get_sn()
        return SN 

    def csv_write(self,file, lis):
        if not os.path.exists(file):
            str1 = ""
        else:
            str1 = '\n'
        for i in range(len(lis)):
            str1+=f'{lis[i]},'
        str1=str1[:-1]
        with open(file, 'a', newline='\n') as f:
            f.write(str1)

    @handle_exceptions
    def run(self):
        while True:
            if ping(self.ip,1) or self.isInterruptionRequested():
                break
        ip_name=self.ip.replace('.', '_')
        save_log=os.path.join(self.record_folder,f"testlog_{ip_name}.txt")
        save_csv=os.path.join(self.record_folder,f"record_{ip_name}.csv")
        if not os.path.exists(save_csv):
            file = open(save_csv, 'w', newline='\n')
            file.write(self.record_header)
            file.close()
        SN=self.get_sn()
        CustomerSN=self.get_customerid()
        global pow_status
        while True:
            if self.isInterruptionRequested():
                break
            t=time.time()
            temp=self.record_func(self.ip,save_log,SN,CustomerSN)
            if isinstance(temp,type(None)):
                continue
            temp+=pow_status
            self.csv_write(save_csv, temp)
            self.sigout_set_tbw_value.emit(temp,self.row_idx)
            sleep_time=self.interval-time.time()+t
            if sleep_time>0:
                time.sleep(sleep_time)
    
    @handle_exceptions  
    def stop(self):
        print(f"[{datetime.datetime.now()}] {self.ip} start finish record lidar status")
        t=time.time()
        while self.isRunning():
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        print(f"[{datetime.datetime.now()}] {self.ip} finish record thread success")



class MonitorFault(QThread):
    sigout_fault_info = pyqtSignal(str,int)
    def __init__(self,ip,faultpath,savepath,row_idx,lidarport,lidarudpport,lisenport):
        super(MonitorFault,self).__init__()
        self.ip=ip
        self.faultpath=faultpath
        self.savepath=savepath
        self.lidarport=lidarport
        self.lidarudpport=lidarudpport
        self.lisenport=lisenport
        self.row_idx=row_idx
        
    def newest_folder(self,A,B):
        newest_path=os.path.join(A,str(B))
        return newest_path

    def check_raw(self,file_list):
        key="sn\d+-\d+.*\.inno_raw$"
        for file in file_list:
            if re.match(key,file):
                return True
        return False

    def delete_util_log(self,log_path):
        log_path=os.path.abspath(log_path)
        if os.path.exists(log_path):
            try:
                os.remove(log_path)
            except:
                pass

    @time_limited(1)
    def get_cmd_print(self,poll_obj,fault_log_path):
        if poll_obj.poll(0):
            stderr=self.cmd.stderr.readline()
            ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sset",stderr)
            if ret:
                str1=f"[{datetime.datetime.now()}] {self.ip} {ret.group(2)} has been set"
                with open(fault_log_path,"a") as f:
                    f.write(str1+"\n")
                print(str1)
                ret_fault=re.search("IN_FAULT_([A-Z_0-9]+)",ret.group(2))
                if ret_fault:
                    self.sigout_fault_info.emit(ret_fault.group(1),self.row_idx)
        stdout=self.cmd.stdout.readline()
        ret=re.search("(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3}).+?fault_manager.cpp.+?\s([A-Z_0-9]+).+?has\sbeen\sheal",stdout)
        if ret:
            str1=f"[{datetime.datetime.now()}] {self.ip} {ret.group(2)} has been heal"
            with open(fault_log_path,"a") as f:
                f.write(str1+"\n")
            print(str1)

    @handle_exceptions
    def run(self):
        util_dir="lidar_util"
        util_path=os.path.join(util_dir,"inno_pc_client")
        fault_log_path=os.path.join(self.faultpath,"fault")
        if not os.path.exists(fault_log_path):
            try:
                os.makedirs(fault_log_path)
            except:
                pass
        fault_log_path=os.path.join(fault_log_path,self.ip.replace(".","_")+".txt")
        if not os.path.exists(util_path):
            print(f"[{datetime.datetime.now()}] file {util_path} not exists!")
            return None
        while True:
            if ping(self.ip,1) or self.isInterruptionRequested():
                break
        if not os.path.exists(self.savepath):
            try:
                os.makedirs(self.savepath)
            except:
                pass
        i=1
        newest_path=self.newest_folder(self.savepath,i)
        command1=f"exec {util_path} --lidar-ip {self.ip} --lidar-port 8010 --lidar-udp-port {self.lidarudpport} --tcp-port {self.lidarport}"
        command2=f"curl localhost:{self.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
        command3=f"curl localhost:{self.lidarport}/command/?set_faults_save_raw=ffffffffffffffff"
        command4=f"curl localhost:{self.lidarport}/command/?set_save_raw_data={self.lisenport}"
        raw_count=len(os.listdir(self.savepath))
        print(f"[{datetime.datetime.now()}] {self.ip} inno_pc_client start boot")
        last_client_fail_time=time.time()
        while True:
            if self.isInterruptionRequested():
                # print(f"[{datetime.datetime.now()}] recieve interruption request")
                break
            if not os.path.exists(newest_path):
                current_time=time.time()
                if current_time-last_client_fail_time>3:
                    last_client_fail_time=current_time
                    print(f"[{datetime.datetime.now()}] {self.ip} inno_pc_client boot failed!")
                if hasattr(self,"cmd"):
                    self.cmd.kill()
                self.cmd=subprocess.Popen(command1,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
                poll_obj=select.poll()
                poll_obj.register(self.cmd.stderr,select.POLLIN)
                time.sleep(1)
                self.cmd2=subprocess.Popen(command2,shell=True)
                self.cmd3=subprocess.Popen(command3,shell=True)
                self.cmd4=subprocess.Popen(command4,shell=True)
                try:
                    self.cmd2.wait(0.5)
                except:
                    self.cmd2.kill()
                try:
                    self.cmd3.wait(0.5)
                except:
                    self.cmd3.kill()
                try:
                    self.cmd4.wait(0.5)
                except:
                    self.cmd4.kill()
                continue
            self.get_cmd_print(poll_obj,fault_log_path)
            self.delete_util_log(os.path.join(util_dir,f"{self.ip}_out"))
            self.delete_util_log(os.path.join(util_dir,f"{self.ip}_err"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.err"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.1"))
            self.delete_util_log(os.path.join(util_dir,"inno_pc_client.log.2"))
            if self.check_raw(os.listdir(newest_path)):
                if i>=raw_count:
                    print(f"[{datetime.datetime.now()}] record raw data to {os.path.abspath(newest_path)}")
                i+=1
                newest_path=self.newest_folder(self.savepath,i)
                command2=f"curl localhost:{self.lidarport}/command/?set_raw_data_save_path='{newest_path}'"
                self.cmd2=subprocess.Popen(command2,shell=True)
                self.cmd3=subprocess.Popen(command3,shell=True)
                self.cmd2.wait()
                self.cmd3.wait()
    
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"[{datetime.datetime.now()}] {self.ip} try finish monitor fault")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        if hasattr(self,"cmd"):
            self.cmd.kill()
        for i in range(2,5):
            if hasattr(self,f"cmd{i}"):
                try:
                    getattr(self,f"cmd{i}").kill()
                except:
                    pass
        print(f"[{datetime.datetime.now()}] {self.ip} finish monitor fualt success")
        




class TestMain(QThread):
    sigout_test_finish = pyqtSignal(str)
    sigout_set_empty=pyqtSignal(list,int)
    sigout_schedule=pyqtSignal(int,int)
    def __init__(self,ip_list,record_folder,record_header,times,set_table_value,report_fault,csv_write_func,record_func,txt_record_interval,txt_off_counter,txt_timeout,cb_lidar_mode):
        super(TestMain,self).__init__()
        self.csv_write_func=csv_write_func
        self.txt_record_interval=txt_record_interval
        self.cb_lidar_mode=cb_lidar_mode
        self.set_table_value=set_table_value
        self.save_folder=record_folder
        self.ip_list=ip_list
        self.txt_timeout=txt_timeout
        self.record_header=record_header
        self.txt_off_counter=txt_off_counter
        self.times=times
        self.record_func=record_func
        self.report_fault=report_fault
    
    @handle_exceptions
    def one_cycle(self,power_one_time,ip_list,i,data_num_power_off,log_path):
        import power
        print(f"[{str(datetime.datetime.now())}] current circle {i}")
        self.power_monitor.pause()
        last_timestamp=time.time()
        while True:
            try:
                print(f"[{datetime.datetime.now()}] start set voltage")
                pow=power.Power()
                print(f"[{datetime.datetime.now()}] init power")
                pow.power_on()
                print(f"[{datetime.datetime.now()}] power on")
                pow.set_voltage(power_one_time[2])
                print(f"[{datetime.datetime.now()}] set {power_one_time[2]}V")
                voltage=pow.PowerStatus()[0]
                print(f"[{datetime.datetime.now()}] voltage is {voltage}")
                if abs(voltage-power_one_time[2])<0.1:
                    break
            except:
                current_timestamp=time.time()
                if current_timestamp-last_timestamp>3:
                    last_timestamp=current_timestamp
                    print(f"[{datetime.datetime.now()}] set power voltage failed, {power_one_time[2]}V")
                time.sleep(2)
        t=time.time()
        time_path=get_time()
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cmd_can=subprocess.Popen(f'exec python3 usbcanfd_controler.py',shell=True)
        self.power_monitor.resume()
        self.records=[]
        self.monitors=[]
        if power_one_time[0]>2:
            for ip_num,ip in enumerate(ip_list):
                print(f"[{datetime.datetime.now()}] start add record {ip}")
                record_thread=one_lidar_record_thread(ip,float(self.txt_record_interval.text()),self.save_folder,self.record_header,ip_num,self.record_func)
                record_thread.sigout_set_tbw_value.connect(self.set_table_value)
                record_thread.start()
                self.records.append(record_thread)
                print(f"[{datetime.datetime.now()}] start add record success {ip}")
                raw_save_path=os.path.join(log_path,"raw",ip.replace(".","_"),time_path)
                monitor_thread=MonitorFault(ip,log_path,raw_save_path,ip_num,9100+ip_num,8600+ip_num,8100+ip_num)
                monitor_thread.sigout_fault_info.connect(self.report_fault)
                monitor_thread.start()
                self.monitors.append(monitor_thread)
                print(f"[{datetime.datetime.now()}] start add fault monitor success {ip}")
            time.sleep(power_one_time[0]-2)
        threads=[]
        for ip in ip_list:
            thread=threading.Thread(target=downlog,args=(ip,log_path,time_path,))
            thread.start()
            threads.append(thread)
        for temp_thread in threads:
            temp_thread.join()
        for monitor in self.monitors:
            if monitor.isRunning():
                monitor.stop()
        for record in self.records:
            if record.isRunning():
                record.stop()
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cmd_can.kill()
            self.kill_cmd_can=subprocess.Popen("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk '{print $2}'|xargs kill -9",shell=True)
            self.kill_cmd_can.wait()
        else:
            self.power_monitor.pause()
            while True:
                try:
                    pow=power.Power()
                    pow.power_off()
                    break
                except:
                    print(f"[{datetime.datetime.now()}] power off failed")
                    time.sleep(2)
            self.power_monitor.resume()
        kill_client()
        print(f"[{datetime.datetime.now()}] start sleep")
        for i in range(data_num_power_off):
            temp_pow=pow_status
            for row_idx,ip in enumerate(ip_list):
                if self.cb_lidar_mode.currentText()=="CAN":
                    temp=[str(datetime.datetime.now())]+[-100]*(self.record_header.count(",")-2)+temp_pow
                else:
                    temp=[str(datetime.datetime.now())]+[-100]*(self.record_header.count(","))
                self.sigout_set_empty.emit(temp,row_idx)
                self.csv_write_func(os.path.join(self.save_folder,'record_'+ip.replace('.','_')+'.csv'),temp)
            t0=(power_one_time[0]+power_one_time[1]-(time.time()-t))/(data_num_power_off-i)
            if t0>0:
                time.sleep(t0)

    @handle_exceptions
    def run(self):
        kill_client()
        os.system("ps -ef|grep 'python3 power_client.py'|grep -v grep|awk '{print $2}'|xargs kill -9")
        if self.txt_record_interval.text().strip()=="":
            print(f"[{datetime.datetime.now()}] please input record interval time")
            return None
        if self.txt_off_counter.text().strip()=="":
            print(f"[{datetime.datetime.now()}] please input power off empty data number")
            return None
        print(f"[{datetime.datetime.now()}] get inno_pc_client permission")
        os.system('echo demo|sudo -S chmod 777 lidar_util/inno_pc_client')
        while not init_power():
            pass
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
        os.system("python3 ./power.py")
        for idx,ip in enumerate(self.ip_list):

            ping_sure(ip,0.5)
            while True:
                try:
                    down_sdk(ip)
                    get_promission(ip,float(self.txt_timeout.text()))
                    if self.cb_lidar_mode.currentText()=="CAN":
                        set_can(ip)
                    break
                except Exception as e:
                    print(e)
            
            record_file=os.path.join(self.save_folder,'record_'+ip.replace('.','_')+'.csv')
            if not os.path.exists(record_file):
                with open(record_file,"w",newline="\n") as f:
                    f.write(self.record_header)
        if self.cb_lidar_mode.currentText()=="CAN":
            os.system("python3 lib/set_usbcanfd_env.py demo")
        self.power_monitor=Power_monitor()
        self.power_monitor.start()
        i=1
        for time_one in self.times:
            self.sigout_schedule.emit(i,len(self.times))
            self.one_cycle(time_one,self.ip_list,i,int(self.txt_off_counter.text()),self.save_folder)
            i+=1 
        self.power_monitor.stop()
        if self.cb_lidar_mode.currentText()=="CAN":
            cancle_can(self.ip_list)
        import power
        pow=power.Power()
        pow.power_off()
        rm_empty_folder(self.save_folder)
        self.sigout_test_finish.emit("done")
    
    @handle_exceptions
    def stop(self):
        if hasattr(self,"records"):
            for record in self.records:
                try:
                    record.stop()
                    record.wait()
                except:
                    pass
        if hasattr(self,"monitors"):
            for monitor in self.monitors:
                try:
                    monitor.stop()
                    monitor.wait()
                except:
                    pass
        if self.cb_lidar_mode.currentText()=="CAN":
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
        try:
            self.power_monitor.stop()
        except:
            pass
        self.terminate()
        kill_client()
        if self.cb_lidar_mode.currentText()=="CAN":
            os.system("ps -ef|grep usbcanfd_controler.py|grep -v grep|awk '{print $2}'|xargs kill -9")
        print(f"[{datetime.datetime.now()}] Test has been stop")

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

        
class MainCode(QMainWindow,userpage.Ui_MainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        userpage.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        self.project_folder="./project"
        self.test_folder="./test_config"

        self.cb_project.currentIndexChanged.connect(self.project_changed)
        self.cb_test_name.currentIndexChanged.connect(self.test_name_changed)
        self.btn_start.clicked.connect(self.test_main)
        self.btn_cancle_can.clicked.connect(self.cancle_can_mode)
        self.btn_stop.clicked.connect(self.test_stop)
        self.init_select_item()
    
        
        IntValidator = QIntValidator(0,100000)
        DoubleValidator = QDoubleValidator(0,100000,3,notation=QtGui.QDoubleValidator.StandardNotation)
        self.txt_timeout.setValidator(DoubleValidator)
        self.txt_record_interval.setValidator(DoubleValidator)
        self.txt_off_counter.setValidator(IntValidator)
        
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

    def write(self, info):
        self.txt_log.insertPlainText(info)
        if len(info):
            self.txt_log.setText(info)
            QtWidgets.qApp.processEvents(
                QtCore.QEventLoop.ExcludeUserInputEvents | QtCore.QEventLoop.ExcludeSocketNotifiers)
            self.stdoutbak.write(info)

    def normalOutputWritten(self, text):
        self.txt_log.append(text.strip('\n'))
        self.cursor=self.txt_log.textCursor()
        self.txt_log.moveCursor(self.cursor.End) 
        QtWidgets.QApplication.processEvents()
    
    def init_table(self,row_counter,columns):
        for row_num in range(self.tbw_data.rowCount(),-1,-1):
            self.tbw_data.removeRow(row_num)
        for row_num in range(self.tbw_fault.rowCount(),-1,-1):
            self.tbw_fault.removeRow(row_num)
        self.tbw_data.setColumnCount(len(columns))
        self.tbw_fault.setColumnCount(0)
        for j in range(len(columns)):
            self.tbw_data.setHorizontalHeaderItem(j, QtWidgets.QTableWidgetItem())
            self.tbw_data.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeToContents)
            item = self.tbw_data.horizontalHeaderItem(j)
            item.setText(f"{columns[j]}")
        for i in range(row_counter):
            self.tbw_data.insertRow(i)
            self.tbw_fault.insertRow(i)
            self.tbw_data.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_fault.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for j in range(len(columns)):
                self.tbw_data.setItem(i,j,QtWidgets.QTableWidgetItem(f""))        
    
    def set_table_value(self,values,row_idx):
        for idx,value in enumerate(values):
            self.tbw_data.setItem(row_idx,idx,QtWidgets.QTableWidgetItem(f"{value}"))
    
    
    def report_fault(self,fault,row_idx):
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

        
    def init_select_item(self):
        self.cb_project.clear()
        self.cb_test_name.clear()
        
        for project in os.listdir(self.project_folder):
            ret=re.search("^(.+)\.py",project)
            if ret:
                self.cb_project.addItem(ret.group(1))
        for test_name in os.listdir(self.test_folder):  # may can be json file, but no explain
            ret=re.search("^(.+)\.py",test_name)
            if ret:
                self.cb_test_name.addItem(ret.group(1))
        self.test_name_changed()
        self.project_changed()
    
    @handle_exceptions
    def test_name_changed(self):
        if self.cb_test_name.currentText().strip()!="":
            mata_class=importlib.import_module(f"{self.test_folder.strip('.').strip('/')}.{self.cb_test_name.currentText()}")
            self.test_config=mata_class.config
            self.save_folder=self.cb_test_name.currentText()
            self.read_config()
        
    def project_changed(self):
        if self.cb_project.currentText().strip()!="":
            mata_class=importlib.import_module(f"{self.project_folder.strip('.').strip('/')}.{self.cb_project.currentText()}")
            self.record_header=mata_class.record_header
            self.csv_write_func=mata_class.csv_write
            self.record_func=mata_class.one_record
            self.read_config()

    def read_config(self):
        if getattr(self,"test_config",None):
            self.ip_list=self.test_config["lidar_ip"]
            self.times=get_circle_time(self.test_config["time_dict"])
            self.init_table(len(self.ip_list),self.record_header.split(","))
    
    @handle_exceptions
    def test_main(self):
        self.pgb_test.setValue(0)
        self.test=TestMain(self.ip_list,self.save_folder,self.record_header,self.times,self.set_table_value,self.report_fault,self.csv_write_func,self.record_func,self.txt_record_interval,self.txt_off_counter,self.txt_timeout,self.cb_lidar_mode)
        self.test.sigout_test_finish.connect(self.test_finish)
        self.test.sigout_set_empty.connect(self.set_table_value)
        self.test.sigout_schedule.connect(self.set_schedule)
        self.test.start()
        self.test_set_off()
    
    def test_finish(self,str1):
        self.test_set_on()
        self.save_tbw_fault()
        print(f"[{datetime.datetime.now()}] Test finished")
    
    def test_set_off(self):
        self.cb_lidar_mode.setEnabled(False)
        self.cb_project.setEnabled(False)
        self.cb_test_name.setEnabled(False)
        self.txt_off_counter.setEnabled(False)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(False)
        self.txt_timeout.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_cancle_can.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def test_set_on(self):
        self.cb_lidar_mode.setEnabled(True)
        self.cb_project.setEnabled(True)
        self.cb_test_name.setEnabled(True)
        self.txt_off_counter.setEnabled(True)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(True)
        self.txt_timeout.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_cancle_can.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    @handle_exceptions
    def set_schedule(self,current_counter,sum_counter):
        str1=f"{round(current_counter*100/sum_counter,1)}%"
        # self.lb_schedule.setText(f"Test Schedule: {str1}")
        self.pgb_test.setValue(math.floor(current_counter*10000/sum_counter))
        self.pgb_test.setFormat(str1)
    
    @handle_exceptions
    def test_stop(self):
        self.test.stop()
        self.test_set_on()
    
    def save_tbw_fault(self):
        headers=[]
        for col_idx in range(self.tbw_fault.columnCount()):
            headers.append(self.tbw_fault.horizontalHeaderItem(col_idx).text())
        df=pd.DataFrame([],columns=headers)
        for row_idx in range(self.tbw_fault.rowCount()):
            row=[]
            for col_idx in range(self.tbw_fault.columnCount()):
                if self.tbw_fault.item(row_idx,col_idx)!=None:
                    row.append(int(self.tbw_fault.item(row_idx,col_idx).text()))
                else:
                    row.append(0)
            df.loc[self.ip_list[row_idx],:]=row
        df.to_excel(os.path.join(self.save_folder,"fault_counter.xlsx"),sheet_name="fault",index_label="ip")
        from excel_format import ExcelFormat
        ef=ExcelFormat(os.path.join(self.save_folder,"fault_counter.xlsx"))
        ef.format()
    
    def cancle_can_mode(self):
        cancle_can(self.ip_list)
    
        
    
        
if __name__ == '__main__':
    QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    window = MainCode()
    window.show()
    sys.exit(app.exec_())
