import platform,subprocess,os,sys,datetime,re

def kill_subprocess(cmd):
    if "windows" in platform.platform().lower():
        command=f'taskkill /f /t /im "{cmd}"'
    else:
        command="ps -ef|grep '"+cmd+"'|grep -v grep|awk '{print $2}'|xargs kill -9"
        # command=f"pgrep -f '{cmd}'|xargs kill"
    os.system(command)
    print(command)
    
def multi_cmd(command_list,max_thread_counter):
    cmds=[]
    for command in command_list:
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

def extend_pcs_log_size(util_path,ip,size=200000):
    if not os.path.exists(util_path):
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] Can't find {util_path}")
        return
    save_cfg_file = "1.cfg"
    save_restart_bash="restart_inno_pc_server.sh"
    command=f'"{util_path}" {ip} download_internal_file PCS_ENV "{save_cfg_file}"'
    if os.path.exists(save_cfg_file):
        os.remove(save_cfg_file)
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if not os.path.exists(save_cfg_file):
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] Can't get {ip} PCS_ENV")
        return
    with open(save_cfg_file,"r") as f:
        pcs_env=f.read()
    
    command=f'sshpass -p 4920lidar scp -rp root@{ip}:/app/pointcloud/restart_inno_pc_server.sh "{save_restart_bash}"'
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    cmd.communicate()
    if not os.path.exists(save_restart_bash):
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] Can't get {ip} restart_inno_pc_server.sh")
        return
    with open(save_restart_bash,"r") as f:
        restart_bash=f.read()
    os.remove(save_restart_bash)
    ret_bash=re.search("{(LOG_OPTION.*?)}",restart_bash)
    if not ret_bash:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {ip} bash not have LOG_OPTION")
        return
    ret=re.search("(LOG_OPTION.*?)\s*=.*(--log-file-max-size-k\s+\d+\.?\d*)",pcs_env)
    if ret:
        pcs_env=pcs_env.replace(ret.group(2),f"--log-file-max-size-k {size}").replace(ret.group(1),ret_bash.group(1))
    else:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {ip} pcs_env not have LOG_OPTION")
        return
    with open(save_cfg_file,"w") as f:
        f.write(pcs_env)
    command=f'"{util_path}" {ip} upload_internal_file PCS_ENV "{save_cfg_file}"'
    cmd=subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res=cmd.communicate()
    if "succe" in res[0]:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {ip} extend log size {size}Kb success")
    else:
        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {ip} extend log size fail")
    os.remove(save_cfg_file)
    os.system(f"curl --connect-timeout 2 -s {ip}:8010/command/?set_reboot=1")


class Logger(object):
    def __init__(self, fileN='Default.log'):
        self.terminal = sys.stdout
        sys.stdout = self
        file_folder = os.path.dirname(fileN)
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        self.log = open(fileN, 'w')

    def write(self, message):
        '''print实际相当于sys.stdout.write'''
        self.terminal.write(message)
        self.log.write(message)

    def reset(self):
        self.log.close()
        sys.stdout = self.terminal

    def flush(self):
        pass

def get_current_date():
    start_time=f"{datetime.datetime.now()}"
    ret=re.findall("\d+",start_time)
    start_time=f"{ret[0].zfill(4)}{ret[1].zfill(2)}{ret[2].zfill(2)}T{ret[3].zfill(2)}{ret[4].zfill(2)}{ret[5].zfill(2)}"
    return start_time



if __name__=="__main__":
    extend_pcs_log_size("./innovusion_lidar_util","172.168.1.10",size=200000)