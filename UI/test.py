import subprocess
import requests
def get_command_result(command):
    cmd = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    res = cmd.communicate()
    cmd.kill()
    return res[0]

def get_curl_result(command,timeout=0.2):
    excute_flag=False
    try:
        request=requests.get(command,timeout=timeout)
        res=request.text
        request.close()
        excute_flag=True
    except Exception as e:
        res=""
    return res,excute_flag

get_curl_result('http://127.0.0.1:8600/command/?set_raw_data_save_path="./100"')


# lidar_util/inno_pc_client" --lidar-ip 10.42.0.91 --lidar-port 8010 --lidar-udp-port 9600 udp-port 9100 --tcp-port 8600
# http://localhost:8600/command/?set_raw_data_save_path=/home/demo/Documents/UI/1111/raw/10_42_0_91/2023_10_23_18_17_04/1
# http://localhost:8600/command/?set_faults_save_raw=ffffffffffffffff
# http://localhost:8600/command/?set_save_raw_data=8100