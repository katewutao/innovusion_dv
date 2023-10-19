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