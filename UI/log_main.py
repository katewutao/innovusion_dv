# /**
#  * @author katewutao
#  * @email [kate.wu@cn.innovuison.com]
#  * @create date 2023-10-31 13:34:58
#  * @modify date 2023-10-31 13:34:58
#  * @desc [analyze_log]
#  */
from utils import *
import re
import pandas as pd
import argparse
import os
from utils.excel_format import ExcelFormat
import time
import platform
import builtins

builtins.print_origin=print
def print_res(*args, **kwargs):
    current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    msg = ' '.join(map(str, args))  # Convert all arguments to strings and join them with spaces
    builtins.print_origin(f"[{current_date}] {msg}", **kwargs)
builtins.print=print_res


fw_file_name="fw.txt"
pcs_file_name="pcs.txt"

def merge_lidar_log(folder):
    global fw_file_name,pcs_file_name
    pcs_str1=""
    fw_str1=""
    pcs_list=[]
    fw_list=[]
    for file in os.listdir(folder):
        if 'lidar-log.' in file and '.txt' in file:
            fw_list.append(file)
        if 'inno_pc_server.' in file and '.txt' in file:
            pcs_list.append(file)
    pcs_list=sorted(pcs_list)
    fw_list=sorted(fw_list)
    for file in pcs_list:
        with open(os.path.join(folder,file),"rb") as f:
            pcs_str1+=str(f.read())[2:-1]
    for file in fw_list:
        with open(os.path.join(folder,file),"rb") as f:
            fw_str1+=str(f.read())[2:-1]
    with open(os.path.join(folder,fw_file_name),"w") as f:
        f.write(fw_str1)
    with open(os.path.join(folder,pcs_file_name),"w") as f:
        f.write(pcs_str1)


def get_fault_count(df_dict_res):
    df_fault_count = pd.DataFrame()
    if "PCS FAULT" in df_dict_res.keys():
        df_fault = df_dict_res["PCS FAULT"]
        for index in df_fault.index:
            fault_name = f'{df_fault.loc[index,"Fault Name"]}({df_fault.loc[index,"Fault ID"]})'
            ret = re.search("(\d+\.\d+\.\d+\.\d+)",df_fault.loc[index,"log path"])
            if ret:
                ip = ret.group(1)
                if ip not in df_fault_count.columns:
                    df_fault_count.insert(df_fault_count.shape[1],ip,[0]*df_fault_count.shape[0])
                if fault_name not in df_fault_count.index:
                    df_fault_count.loc[fault_name] = [0]*df_fault_count.shape[1]
                df_fault_count.loc[fault_name,ip] += 1
    if "FW FAULT" in df_dict_res.keys():
        df_fault = df_dict_res["FW FAULT"]
        for index in df_fault.index:
            fault_name = f'{df_fault.loc[index,"Fault Name"]}'
            ret = re.search("(\d+\.\d+\.\d+\.\d+)",df_fault.loc[index,"log path"])
            if ret:
                ip = ret.group(1)
                if ip not in df_fault_count.columns:
                    df_fault_count.insert(df_fault_count.shape[1],ip,[0]*df_fault_count.shape[0])
                if fault_name not in df_fault_count.index:
                    df_fault_count.loc[fault_name] = [0]*df_fault_count.shape[1]
                df_fault_count.loc[fault_name,ip] += 1
    return df_fault_count
    


def main(args):
    global fw_file_name,pcs_file_name
    if not os.path.exists(args.folder):
        return
    save_folder = args.output_folder
    result_path = os.path.join(save_folder,"result.xlsx")
    fault_count_path = os.path.join(save_folder,"fault_count.xlsx")
    command_path = os.path.join(save_folder,"config.csv")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    excel_list = []
    commands = []
    aim_path = []
    rm_file_list = []
    if "windows" in platform.platform().lower():
        python_version = "python"
    else:
        python_version = "python3"
    if args.client:
        for root,_ ,files in os.walk(args.folder):
            if os.path.basename(root)=="client_log" or os.path.basename(os.path.dirname(root))=="client_log":
                for file in files:
                    if not file.endswith(".txt"):
                        continue
                    aim_path.append(os.path.join(root,file))
    elif args.lidar_log:
        for root,_ ,files in os.walk(args.folder):
            list_dir = os.listdir(root)
            if "tmp" in list_dir and "mnt" in list_dir:
                tmp_dir = os.path.join(root,"tmp")
                aim_path.append(tmp_dir)
                merge_lidar_log(tmp_dir)
    else:
        return
    aim_path = sorted(aim_path,key=lambda x: os.path.getctime(x))
    for idx,log_path in enumerate(aim_path):
        xlsx_path = os.path.join(save_folder,f"{idx}.xlsx")
        excel_list.append(xlsx_path)
        if args.client:
            commands.append(f'{python_version} one_subprocess.py -cp "{log_path}" -sp "{xlsx_path}"')
        else:
            rm_file_list.append([os.path.join(log_path,fw_file_name),os.path.join(log_path,pcs_file_name)])
            commands.append(f'python one_subprocess.py -fp "{rm_file_list[-1][0]}" -pp "{rm_file_list[-1][1]}" -sp "{excel_list[-1]}"')
        print(commands[-1])
    commands = commands[args.start_idx:]
    multi_cmd(commands,args.max_thread_counter,command_path)
    if len(rm_file_list)>0:
        for rm_file in rm_file_list:
            for file in rm_file:
                os.remove(file)
    df_dict_res = {}
    for idx,excel in enumerate(excel_list):
        if not os.path.exists(excel):
            continue
        df = pd.read_excel(excel,sheet_name=None)
        for key in df.keys():
            df[key].insert(df[key].shape[1],"log path",[aim_path[idx]]*df[key].shape[0])
            if key not in df_dict_res.keys():
                df_dict_res[key] = df[key]
            else:
                df_dict_res[key] = pd.concat([df_dict_res[key],df[key]],ignore_index=True)
        if args.rm_result:
            try:
                os.remove(excel)
            except:
                pass
    if len(df_dict_res.keys())==0:
        return
    writer = pd.ExcelWriter(result_path)
    for key in df_dict_res.keys():
        if df_dict_res[key].shape[0] <= 300000:
            df_dict_res[key].to_excel(writer, sheet_name=key, index=False)
        else:
            df_dict_res[key].to_csv(os.path.join(save_folder,f"{key}.csv"),index=False)
    writer.close()
    # ExcelFormat(result_path).format()
    df_fault_count = get_fault_count(df_dict_res)
    if df_fault_count.shape[0]>0:
        df_fault_count.to_excel(fault_count_path,index=True,index_label="fault name/ip")
        # ExcelFormat(fault_count_path).format()
    

if __name__=="__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("--folder", "-f", type=str, default=r"Y:\Testing\1.Project\2.NIO\2.Falcon_G\10.PV2\监控数据\Leg9 L03\75%\client_log", help="log file path")
    parse.add_argument("--client", "-c" ,action="store_true")
    parse.add_argument("--lidar-log", "-ll" , action="store_true")
    parse.add_argument("--output-folder", "-o" ,type=str, default="./analyze_result")
    parse.add_argument("--max-thread-counter", "-mtc" ,type=int, default=6)
    parse.add_argument("--start-idx", "-si" ,type=int, default=0)
    parse.add_argument("--rm-result", "-r" ,action="store_true")
    args = parse.parse_args()
    t=time.time()
    main(args)
    print(f"total time: {time.time()-t}s")