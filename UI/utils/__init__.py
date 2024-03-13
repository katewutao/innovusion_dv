import platform
import subprocess
import os
import sys
import datetime
import re
import time
import requests,socket
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA



def kill_subprocess(cmd):
    if "windows" in platform.platform().lower():
        command=f'taskkill /f /t /im "{cmd}"'
    else:
        command="ps -ef|grep '"+cmd+"'|grep -v grep|awk '{print $2}'|xargs kill -9"
        # command=f"pgrep -f '{cmd}'|xargs kill"
    os.system(command)
    print(command)
    
def multi_cmd(command_list,max_thread_counter,conf_file=""):
    cmds=[]
    if conf_file!="" and os.path.exists(conf_file):
        df_config = pd.read_csv(conf_file)
    else:
        df_config = pd.DataFrame(columns=["command"])
    for command in command_list:
        if command in df_config["command"].values:
            continue
        df_config.loc[df_config.shape[0]] = [command]
        cmd=subprocess.Popen(command,shell=True)
        cmds.append(cmd)
        while True:
            cmd_counter=0
            for cmd in cmds:
                if cmd.poll()==None:
                    cmd_counter+=1
            if cmd_counter<max_thread_counter:
                break
    for cmd in cmds:
        cmd.wait()
    if conf_file!="":
        df_config.to_csv(conf_file,index=False)

def load_pointcloud_yaml(path="./config/pointcloud_area.yaml"):
    import yaml
    config = {}
    if not os.path.exists(path):
        print(f"Can't find {path}")
        return config
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config
class PointCloud(object):
    def __init__(self,df=None):
        self.df = df
        
    def filter_box(self, bds):
        df_filter = self.df.loc[(self.df["x"] >= bds[0]) & (self.df["x"] <= bds[1]) & ((self.df["y"] >= bds[2])) & (
            self.df["y"] <= bds[3]) & (self.df["z"] >= bds[4]) & (self.df["z"] <= bds[5])]
        return df_filter
    
    def add_angle_r(self):
        r = np.linalg.norm(self.df[["x", "y", "z"]].values, axis=1).reshape(-1)
        azimuth = np.rad2deg(np.arctan2(self.df["y"].values, self.df["z"].values))
        evelation = np.rad2deg(np.arcsin(self.df["x"].values/r))
        self.df["radius"] = r
        self.df["azimuth"] = azimuth
        self.df["evelation"] = evelation
        return self.df
        
    def filter_fov(self,fov):
        df = self.df.loc[(self.df["azimuth"] >= fov[0]) & (self.df["azimuth"] <= fov[1]) & ((self.df["evelation"] >= fov[2])) & (
            self.df["evelation"] <= fov[3])]
        return df       

    def calc_acc(self,df,gt_distance):
        if df.shape[0]==0:
            return "NaN"
        acc = np.linalg.norm(df[["x", "y", "z"]].values, axis=1).mean()-gt_distance
        return round(float(acc),3)

    def calc_pre(self,df_pc):
        if df_pc.shape[0]<3:
            return "NaN"
        data = df_pc[["x","y","z"]].values
        pca = PCA(n_components=data.shape[1])
        pca.fit(data)
        vector = pca.components_[-1]/np.linalg.norm(pca.components_[-1])
        # vector/=np.linalg.norm(vector)
        d = -vector.dot(pca.mean_)
        # print(self.data,vector,d)
        dist=data@vector+d
        mse=np.abs(dist).mean()
        pre=dist.std()
        return round(float(pre*6),3)
        

def str2timestamp(str1):
    str1=str(str1)
    import re
    key='(\d{4}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2})(\.?\d*)'
    ret=re.search(key,str1)
    if ret:
        deci=0
        if len(ret.group(7))>1:
            deci=float('0'+ret.group(7))
        if '1970' not in ret.group(1):
            return time.mktime(time.strptime(ret.group(1), f'%Y{ret.group(2)}%m{ret.group(3)}%d{ret.group(4)}%H{ret.group(5)}%M{ret.group(6)}%S'))+deci
        else:
            return 0
    return 0
class TimeConvert(object):
    @classmethod
    def time2hms(cls,str1):
        ret=re.search("^(\d+)$",str(str1))
        time_s=int(ret.group(1))
        h=time_s//3600
        m=time_s%3600//60
        s=time_s%60
        h=str(h).zfill(2)
        m=str(m).zfill(2)
        s=str(s).zfill(2)
        return f"{h}:{m}:{s}"
    
    @classmethod
    def hms2time(cls,str1):
        ret=re.search("^(\d+):(\d+):(\d+)$",str1)
        s=int(ret.group(1))*3600+int(ret.group(2))*60+int(ret.group(3))
        return s



def get_curl_result(command,timeout=0.2):
    excute_flag=False
    try:
        request=requests.get(command,timeout=timeout,)
        res=request.text
        request.close()
        excute_flag=True
    except Exception as e:
        res=""
    return res,excute_flag

def download_file(url,filename=None,time_sleep=0):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except:
        time.sleep(time_sleep)
        if isinstance(filename,str):
            print(f"download {filename} failed")
        return ""
    res = response.content
    if isinstance(filename,str):
        with open(filename,"wb") as f:
            f.write(res)
        print(f"download {filename} success")
    else:
        return res
    
def csv_write(file, list1):
    if not os.path.exists(file):
        str1 = ""
    else:
        str1 = '\n'
    if isinstance(list1, list):
        str1+=",".join(map(str,list1))
    elif isinstance(list1, str):
        str1 += list1
    with open(file, 'a', newline='\n') as f:
        f.write(str1)

def get_current_date():
    start_time=f"{datetime.datetime.now()}"
    ret=re.findall("\d+",start_time)
    start_time=f"{ret[0].zfill(4)}{ret[1].zfill(2)}{ret[2].zfill(2)}T{ret[3].zfill(2)}{ret[4].zfill(2)}{ret[5].zfill(2)}"
    return start_time



def send_tcp(command,ip,port=8001,wait=False,max_length=1024):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command = command.strip("\n")+"\n"
    if wait:
        sock.settimeout(5)
    res = ""
    try:
        sock.connect((ip, port))
    except:
        print(f"connect {ip} {port} fail")
        sock.close()
        time.sleep(3)
        return res
    sock.sendall(command.encode())
    if wait:
        first_recv = True
        while True:
            try:
                response = sock.recv(max_length).decode()
            except:
                break
            if first_recv:
                first_recv = False
                sock.settimeout(3)
            res += response
            if response=="":
                break
    else:
        try:
            res = sock.recv(max_length).decode()
        except:
            pass
    sock.close()
    return res

class LidarTool(object):
    def __init__(self):
        pass
    
    def get_promission(ip,time_out):
        print(f"{ip} get premission")
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
    
    def get_customerid(ip):
        customerid = 'null'
        command = 'mfg_rd "CustomerSN"'
        s = send_tcp(command,ip,8001)
        if s == "":
            s = send_tcp(command,ip,8002)
        ret=re.search('CustomerSN.*?:\s*[\'|"](.+)[\'|"]',s)
        if ret:
            customerid=ret.group(1)
        return customerid

    def set_network(ip,new_ip):
        ret = re.search("^(\d+\.\d+)",ip)
        if not ret:
            print(f"{ip} is not valid,set network fail")
            return
        ip_key = ret.group(1).replace(".","\.")
        res = os.popen("ip addr show").read()
        ret_ip_cfg = re.findall("inet\s+([0-9\./]+)",res)
        netmask = ""
        for item in ret_ip_cfg:
            ret = re.search(f"^{ip_key}.+/(\d+)",item)
            if ret:
                ffff_count = int(int(ret.group(1))/8)
                netmask = ("255."*ffff_count)[:-1]+".0"*(4-ffff_count)
                break
        if netmask == "":
            print(f"{ip_key} not find in ip config,set network fail")
            return
        new_ip_list = new_ip.split(".")
        netmask_list = netmask.split(".")
        last_ip = "1" if new_ip_list[-1] != "1" else "100"
        command_list = new_ip_list+netmask_list+new_ip_list[:-1]+[last_ip]
        set_command = " ".join(command_list)
        command = f'set_network {set_command}'
        s = send_tcp(command,ip,8001)
        if f"netmask={netmask}" not in s:
            print(f"{ip} set network {netmask} fail")
            return
        else:
            print(f"{ip} set network {netmask} success")
            return

    def open_ptp(ip):
        command = f"set_i_config time ptp_en 1"
        s = send_tcp(command,ip,8001)
        if "done" not in s:
            print(f"{ip} open ptp fail,process set_i_config")
            return
        command = f"get_i_config time"
        s = send_tcp(command,ip,8001)
        if "ptp_en = 1" in s:
            print(f"{ip} open ptp success")
            return
        else:
            print(f"{ip} open ptp fail, process get_i_config")
            return

    def extend_pcs_log_size(util_path,ip,size=2000):
        lidar_port = 8002        
        save_restart_bash="restart_inno_pc_server.sh"
        command=f'sshpass -p 4920lidar scp -rp root@{ip}:/app/pointcloud/restart_inno_pc_server.sh "{save_restart_bash}"'
        cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
        cmd.communicate()
        if not os.path.exists(save_restart_bash):
            print(f"Can't get {ip} restart_inno_pc_server.sh")
            return
        with open(save_restart_bash,"r") as f:
            restart_bash=f.read()
        os.remove(save_restart_bash)
        ret_bash=re.search("{(LOG_OPTION.*?)}",restart_bash)
        if not ret_bash:
            print(f"{ip} bash not have LOG_OPTION")
            return
        cfg = send_tcp("get_i_config pcsenv",ip,lidar_port,max_length=4096)
        ret_cfg = re.search(f"(?:user config)?[\s\S]*{ret_bash.group(1)}\s*=(.*)\n",cfg)
        if ret_cfg:
            log_option = ret_cfg.group(1)
            ret_log_size = re.search("(--log-file-max-size-k\s+\d+)",log_option)
            if ret_log_size:
                log_option = log_option.replace(ret_log_size.group(1),f"--log-file-max-size-k {size}")
            else:
                print(f"{ip} can't find log size")
                return
        else:
            print(f"{ip} can't find {ret_bash.group(1)}")
            return
        command = f"set_i_config pcsenv {ret_bash.group(1)} {log_option}"
        send_tcp(command,ip,lidar_port)
        res = send_tcp("get_i_config pcsenv",ip,lidar_port,max_length=4096)
        if re.search(f"{ret_bash.group(1)}.*--log-file-max-size-k {size}",res):
            print(f"{ip} extend log size success")
        else:
            print(f"{ip} extend log size fail,set i config fail")
        
        
    def open_broadcast(util_path,ip,udp_port=8010):
        lidar_port = 8002
        command = "set_i_config pcsenv UDP_IP eth0"
        send_tcp(command,ip,lidar_port)
        udp_port_names = ["UDP_PORT_DATA","UDP_PORT_MESSAGE","UDP_PORT_STATUS"]
        for udp_port_name in udp_port_names:
            command = f"set_i_config pcsenv {udp_port_name} {udp_port}"
            send_tcp(command,ip,lidar_port)
        cfg = send_tcp("get_i_config pcsenv",ip,lidar_port,max_length=4096)
        for udp_port_name in udp_port_names:
            if not re.search(f"{udp_port_name}.*{udp_port}",cfg):
                print(f"{ip} open broadcast fail")
                return
        print(f"{ip} open broadcast success")
        return
        
    def reboot_lidar(ip):
        print(f"reboot lidar {ip}")
        res = send_tcp("reboot 1",ip,8002)
        if res == "":
            print(f"{ip} reboot fail")
        else:
            print(f"{ip} reboot success")
        time.sleep(10)
        
    def set_pcs(ip,open=True):
        if open:
            res, flag = get_curl_result(f"http://{ip}:8675/v1/pcs/enable?toggle=on",2)
        else:
            res, flag = get_curl_result(f"http://{ip}:8675/v1/pcs/enable?toggle=off",2)
        if flag:
            print(f"{ip} set pcs {open} success")
        else:
            print(f"{ip} set pcs {open} fail")
            
            
    
    
if __name__=="__main__":
    def rp_factor_phase_from_binary_stream(data, ch):
        idx = 0
        rp_factor = np.zeros(16)
        num_str = ''
        for character in data:
            tmp = chr(character)
            if tmp == '\t' or tmp == '\n':
                rp_factor[idx] = float(num_str)
                num_str = ''
                idx = idx + 1
                continue
            num_str = num_str + tmp
        rp_factor = np.reshape(rp_factor, (4, 4))
        current_rp_factor = rp_factor[ch, 2]
        return current_rp_factor

    def read_rp_from_register(ch):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('172.168.1.10', 8001))
        cmd_read_ripple_dist_rp_factor = 'ripple'
        s.sendall(cmd_read_ripple_dist_rp_factor.encode())
        data = s.recv(1024)
        current_dist_rp_factor = rp_factor_phase_from_binary_stream(data, ch)
        s.close()
        return current_dist_rp_factor
    t=time.time()   
    print(read_rp_from_register(0),read_rp_from_register(1),read_rp_from_register(2),read_rp_from_register(3))
    print(time.time()-t)
    t=time.time()
    res = send_tcp("ripple","172.168.1.10",8001)
    print(re.findall("(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*).*\n",res))   
    print(time.time()-t) 
    