import os
import argparse
import re

def get_commands(ip,mac):
    mac=re.search("\.(\d+)$",ip).group(1)
    commands=[
        f"./innovusion_lidar_util {ip} flash_write 0x02 0X0C",
        f"./innovusion_lidar_util {ip} flash_write 0x1c 0X{mac}",
        f"./innovusion_lidar_util {ip} flash_write 0x1d 0X03",
        f"./innovusion_lidar_util {ip} flash_write 0x1e 0X20",
        f"./innovusion_lidar_util {ip} flash_write 0x1f 0XD5",
        f"./innovusion_lidar_util {ip} flash_write 0x20 0XB3",
        f"./innovusion_lidar_util {ip} flash_write 0x21 0X70",
    ]
    return commands


def excute_commands(commands):
    for command in commands:
        print(command)
        os.system(command)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac","-m", type=str, default="70")
    parser.add_argument("--ip","-i", type=str, default="172.168.1.10")
    args = parser.parse_args()
    commands=get_commands(args.ip,args.mac)
    excute_commands(commands)