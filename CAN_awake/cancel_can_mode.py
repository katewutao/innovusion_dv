from main import cancle_can,os

ip_list=[
    "172.168.1.39",
    "172.168.1.40",
    "172.168.1.41",
    "172.168.1.42",
    "172.168.1.43",
    "172.168.1.44",
]

os.system("python3 lib/set_usbcanfd_env.py demo")
cancle_can(ip_list)