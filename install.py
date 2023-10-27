import os
import re

install_app_list=[
    'sshpass',
    'ntpdate',
    'git',
]


remove_app_list=[
    "open-vm-tools",
]


sys_command=[
    'timedatectl set-ntp true',
    'systemctl restart systemd-timesyncd.service',
    'sudo apt-get install open-vm-tools',
    'sudo apt-get install open-vm-tools-desktop',
    'sudo apt-get install libssl-dev openssl',
    'sudo apt-get install libhdf5-dev',
    'sudo apt-get install libxcb-xinerama0',
]


pip_command=[
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ openpyxl",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pandas",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pyserial",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ modbus_tk",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pyqt5==5.15.8",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ pexpect",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ xlrd",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ xlsxwriter",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ redis",
    "pip3 install -i https://mirrors.aliyun.com/pypi/simple/ requests",
]



def get_python_version():
    res=os.popen("python3 --version").read()
    ret=re.search("Python\s?3\.(\d+)",res)
    if ret:
        return int(ret.group(1))
    else:
        return None


def get_ubuntu_verison():
    res=os.popen("echo demo|sudo -S lsb_release -r").read()
    ret=re.search("Release:\s?(\d+)",res)
    if ret:
        return int(ret.group(1))
    else:
        return None
    

def child_print(child):
    space_count=0
    while True:
        res=child.readline().decode("utf-8")
        if res!="":
            print(res)
            space_count=0
        else:
            space_count+=1
        if space_count>1000:
            break

def check_install(app):
    res=os.popen(f"which {app}").read()
    if res!="":
        return True
    return False


def install_app(app,password="demo"):
    import pexpect
    child=pexpect.spawn(f"sudo apt-get install {app}")
    child.expect("password", timeout=2)
    child.sendline(password)
    while True:
        try:
            child.expect("Y/n", timeout=2)
            child.sendline("y")
            child_print(child)
            while True:
                if check_install(app):
                    break
                child.expect("Y/n", timeout=2)
                child.sendline("y")
            break
        except:
            try:
                child.sendline("y")
            except:
                pass
            if check_install(app):
                child_print(child)
                break
    child.close()
    
    
def uninstall_app(app,password="demo"):
    import pexpect
    child=pexpect.spawn(f"sudo apt-get autoremove {app}")
    child.expect("password", timeout=2)
    child.sendline(password)
    while True:
        try:
            child.expect("Y/n", timeout=2)
            child.sendline("y")
            child_print(child)
            while True:
                if not check_install(app):
                    break
                child.expect("Y/n", timeout=2)
                child.sendline("y")
            break
        except:
            try:
                child.sendline("y")
            except:
                pass
            if not check_install(app):
                child_print(child)
                break
    child.close()


def update_apt_get(password="demo"):
    import pexpect
    child=pexpect.spawn(f"sudo apt-get update")
    child.expect("password", timeout=2)
    child.sendline(password)
    while True:
        try:
            child.expect("Y/n", timeout=2)
            child.sendline("y")
            child_print(child)
            break
        except:
            child_print(child)
            break
    
    
if __name__=="__main__":
    #version=get_python_version()    3.6/3.8  6/8
    version=get_ubuntu_verison()
    if version:
        if version>=20:
            for i in range(len(pip_command)):
                pip_command[i]=f"echo demo|sudo -S {pip_command[i]}"
        for item in pip_command:
            os.system(item)
    else:
        print("python3 is not exist!")
    update_apt_get()
    for app in remove_app_list:
        print(f"start remove {app}")
        uninstall_app(app)
        print(f"finished remove {app}") 
    for app in install_app_list:
        if check_install(app):
            print(f"start install {app}")
            install_app(app)
            print(f"finished install {app}")
    for command in sys_command:
        os.system(command)