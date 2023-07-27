import platform,subprocess,os
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