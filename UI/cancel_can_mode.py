from main import cancle_can,os,init_power,time

ip_list=[
    "172.168.1.39",
    "172.168.1.40",
    "172.168.1.41",
    "172.168.1.42",
    "172.168.1.43",
    "172.168.1.44",
]
while True:
    if init_power():
        break
os.system("python3 lib/set_usbcanfd_env.py demo")
os.system("python3 ./power.py")
time.sleep(20)
cancle_can(ip_list)