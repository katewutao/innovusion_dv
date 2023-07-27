import numpy as np
import pandas as pd
import subprocess,time

# def main():
#     command="curl --connect-timeout 2 172.168.1.10:8088/get-all-status"
#     cmd=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#     try:
#         cmd.wait(2)
#         res=str(cmd.stdout.read())
#     except:
#         res=""
#     cmd.kill()
#     return res
# while True:
#     print(main())


command="curl --connect-timeout 2 172.168.1.10:8088/get-all-status"
cmd=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
while True:
    print(not cmd.poll())
    time.sleep(1)