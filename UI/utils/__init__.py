import platform,subprocess,os,sys,datetime,re,time
import requests,socket
import pandas as pd

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




def extend_pcs_log_size(util_path,ip,size=200000):
    if not os.path.exists(util_path):
        print(f"Can't find {util_path}")
        return
    save_cfg_file = "1.cfg"
    save_restart_bash="restart_inno_pc_server.sh"
    command=f'"{util_path}" {ip} download_internal_file PCS_ENV "{save_cfg_file}"'
    if os.path.exists(save_cfg_file):
        os.remove(save_cfg_file)
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if not os.path.exists(save_cfg_file):
        print(f"Can't get {ip} PCS_ENV")
        return
    with open(save_cfg_file,"r") as f:
        pcs_env=f.read()
    
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
    ret=re.search("(LOG_OPTION.*?)\s*=.*(--log-file-max-size-k\s+\d+\.?\d*)",pcs_env)
    if ret:
        pcs_env=pcs_env.replace(ret.group(2),f"--log-file-max-size-k {size}").replace(ret.group(1),ret_bash.group(1))
    else:
        print(f"{ip} pcs_env not have LOG_OPTION")
        return
    with open(save_cfg_file,"w") as f:
        f.write(pcs_env)
    command=f'"{util_path}" {ip} upload_internal_file PCS_ENV "{save_cfg_file}"'
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if "succe" in res[0]:
        print(f"{ip} extend log size {size}Kb success")
    else:
        print(f"{ip} extend log size fail")
    os.remove(save_cfg_file)
    



def open_broadcast(util_path,ip,udp_port=8010):
    if not os.path.exists(util_path):
        print(f"Can't find {util_path}")
        return
    save_cfg_file = "1.cfg"
    command=f'"{util_path}" {ip} download_internal_file PCS_ENV "{save_cfg_file}"'
    if os.path.exists(save_cfg_file):
        os.remove(save_cfg_file)
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if not os.path.exists(save_cfg_file):
        print(f"Can't get {ip} PCS_ENV")
        return
    with open(save_cfg_file,"r") as f:
        pcs_env=f.read()
    pcs_env_lines = pcs_env.split("\n")
    pcs_env = "UDP_IP=eth0\n"
    for pcs_env_line in pcs_env_lines:
        ret=re.search("^\s*?(UDP_PORT.*)=(\d+)",pcs_env_line)
        if ret:
            pcs_env += f"{ret.group(1)}={udp_port}\n"
        else:
            ret=re.search("^\s*?(UDP_IP)",pcs_env_line)
            if not ret and pcs_env_line != "":
                pcs_env += f"{pcs_env_line}\n"
    with open(save_cfg_file,"w") as f:
        f.write(pcs_env)
    command=f'"{util_path}" {ip} upload_internal_file PCS_ENV "{save_cfg_file}"'
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if "succe" in res[0]:
        print(f"{ip} set broadcast success")
    else:
        print(f"{ip} set broadcast fail")
    os.remove(save_cfg_file)
    

def reboot_lidar(ip):
    print(f"reboot lidar {ip}")
    while True:
        if get_curl_result(f"http://{ip}:8010/command/?set_reboot=1",1)[1]:
            break
    time.sleep(10)

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

def download_file(url,filename):
    print(f"download {filename} start")
    try:
        response = requests.get(url)
    except:
        print(f"download {filename} failed")
        return
    response.raise_for_status()
    with open(filename,"wb") as f:
        f.write(response.content)
    print(f"download {filename} success")
    
def csv_write(file, list1):
    if not os.path.exists(file):
        str1 = ""
    else:
        str1 = '\n'
    str1+=",".join(map(str,list1))
    with open(file, 'a', newline='\n') as f:
        f.write(str1)

def get_current_date():
    start_time=f"{datetime.datetime.now()}"
    ret=re.findall("\d+",start_time)
    start_time=f"{ret[0].zfill(4)}{ret[1].zfill(2)}{ret[2].zfill(2)}T{ret[3].zfill(2)}{ret[4].zfill(2)}{ret[5].zfill(2)}"
    return start_time


def send_tcp(command,ip,port=8001,wait=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if wait:
        sock.settimeout(5)
    res = ""
    try:
        sock.connect((ip, port))
    except:
        print(f"connect {ip} {port} fail")
        sock.close()
        return res
    sock.sendall(command.encode())
    if wait:
        first_recv = True
        while True:
            try:
                response = sock.recv(1024).decode()
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
            res = sock.recv(1024).decode()
        except:
            pass
    sock.close()
    return res

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


if __name__=="__main__":
    # extend_pcs_log_size("./innovusion_lidar_util","172.168.1.10",size=200000)
    # open_broadcast("./lidar_util/innovusion_lidar_util","172.168.1.10")
    # command = 'mfg_rd "CustomerSN"'
    # t= time.time()
    # s = send_tcp(command,"172.168.1.10",8088)
    # print(time.time()-t)
    
    
    command = "http://172.168.1.10:8010/command/?get_sdk_version"
    
    while True:
        res = []
        res.append(send_tcp('scanh_tran STR051ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR052ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR053ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR054ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR055ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR056ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR108ND',"172.168.1.10",8001).strip("\n"))
        res.append(send_tcp('scanh_tran STR109ND',"172.168.1.10",8001).strip("\n"))
        print(datetime.datetime.now(),res)