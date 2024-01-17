import os
import argparse
import re
import socket
import time

def send_tcp(command,ip,port=8001,wait=False):
    command = command.strip("\n")+"\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if wait:
        sock.settimeout(2)
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


def get_commands(ip,mac=None):
    if mac is None:
        mac=re.search("\.(\d+)$",ip).group(1)
    commands=[
        f'flash_wr 0x02 0x0C',
        f'flash_wr 0x1c 0x{mac}',
        f'flash_wr 0x1d 0x19',
        f'flash_wr 0x1e 0x43',
        f'flash_wr 0x1f 0xE6',
        f'flash_wr 0x20 0xC3',
        f'flash_wr 0x21 0x04',
    ]
    return commands


def excute_commands(commands):
    for command in commands:
        res = send_tcp(command,args.ip,8002)
        print(command,"    ",res.strip("\n"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mac","-m", type=str, default="55")
    parser.add_argument("--ip","-i", type=str, default="172.168.1.10")
    args = parser.parse_args()
    commands=get_commands(args.ip,args.mac)
    excute_commands(commands)