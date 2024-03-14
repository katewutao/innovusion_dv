import os
import platform


conf = \
'''[global]
index-url = http://mirrors.aliyun.com/pypi/simple/
trusted-host = mirrors.aliyun.com
index = https://pypi.tuna.tsinghua.edu.cn/simple/'''


def mian():
    if "windows" in platform.platform().lower():
        folder = os.path.join(os.environ["USERPROFILE"], "pip")
        path = os.path.join(folder, "pip.ini")
    else:
        folder = os.path.join(os.environ["HOME"], ".config", "pip")
        path = os.path.join(folder, "pip.conf")
    print(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(path, "w") as f:
        f.write(conf)
    print("pip config is set successfully!")
    

if __name__ == "__main__":
    mian()