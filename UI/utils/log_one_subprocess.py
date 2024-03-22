import argparse
import os
import pandas as pd
from excel_format import ExcelFormat
import numpy as np
import pandas as pd
import re
import time

def str2timestamp(str1):
    str1=str(str1)
    import re
    key='(\d{4}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2})(\.?\d*)'
    ret=re.search(key,str1)
    if ret:
        deci=0
        if len(ret.group(7))>1:
            deci=float('0'+ret.group(7))
        if '1970' not in ret.group(1):
            return time.mktime(time.strptime(ret.group(1), f'%Y{ret.group(2)}%m{ret.group(3)}%d{ret.group(4)}%H{ret.group(5)}%M{ret.group(6)}%S'))+deci
        else:
            return 0
    return 0

def read_file(file_path):
    with open(file_path,'rb') as f:
        res = str(f.read())[2:-1].replace("\\\\n","\n").replace('\\r\\n','\n').replace("\\n","\n").split('\n')
    return res

class Log_statistic(object):
    def __init__(self,pcs_path=None,fw_path=None,client_log_path=None):
        self.pcs_path = pcs_path
        self.fw_path = fw_path
        self.client_log_path = client_log_path
        self.dict_df = {}
        if pcs_path:
            print(f"{pcs_path} start to analyze")
            self.pcs_log()
        if fw_path:
            print(f"{fw_path} start to analyze")
            self.fw_log()
        if client_log_path:
            print(f"{client_log_path} start to analyze")
            self.client_log()
    
    def pcs_log(self):
        re_keys={
        'PCS WARN':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*(\[\s?WARN\s?\]\s\d*\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'PCS ERROR':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*?(\[.*?ERROR.*?\]\s\d*\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'PCS FATAL':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*?(\[.*?FATAL.*?\]\s\d*\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'PCS CRITI':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*?(\[.*?CRITI.*?\]\s\d*\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'PCS FAULT':'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3})\s(\[.*?\]\s.*?fault_manager.cpp.*\s([A-Z0-9_]+)(\((\d+)\))?.+has.+been\s(set|heal).*)',#1.时间 2.全行 3.关键词 4.(序号) 5.fault 序号 6.set or healed
    }
        self.dict_df['PCS FAULT'] = pd.DataFrame([],columns=['Fault ID','Fault Name','Fault logs','Fault first Set Time','Fault Healed Last Time','Fault Time Span(s)'])
        self.dict_df['PCS ERROR'] = pd.DataFrame([],columns=['Error Source File','Error Log','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['PCS WARN'] = pd.DataFrame([],columns=['Warn Source File','Warn Log','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['PCS FATAL'] = pd.DataFrame([],columns=['Fatal Source File','Fatal Log','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['PCS CRITI'] = pd.DataFrame([],columns=['Critical Source File','Critical Log','First Occurence Time','Last Occurence Time','Occurrence Times'])
        
        res = read_file(self.pcs_path)
        for idx,one_line in enumerate(res):
            for key in re_keys:
                ret = re.search(re_keys[key],one_line)
                if ret:
                    one_res = list(ret.groups())
                    if key!='PCS FAULT':
                        filter_select = self.dict_df[key].loc[(self.dict_df[key].iloc[:,0]==one_res[2])&(self.dict_df[key].iloc[:,1]==one_res[1])]
                        if filter_select.shape[0]==0:
                            self.dict_df[key].loc[self.dict_df[key].shape[0]]=[one_res[2],one_res[1],one_res[0],one_res[0],1]
                        else:
                            self.dict_df[key].loc[filter_select.index[-1],"Last Occurence Time"]=one_res[0]
                            self.dict_df[key].loc[filter_select.index[-1],"Occurrence Times"]=filter_select.iloc[-1,4]+1
                    else:
                        if "set" in one_res[5]:
                            self.dict_df[key].loc[self.dict_df[key].shape[0]]=[one_res[4],one_res[2],one_res[1],one_res[0],"",""]
                        elif "heal" in one_res[5]:
                            filter_select = self.dict_df[key].loc[(self.dict_df[key].iloc[:,0]==one_res[4])&(self.dict_df[key].iloc[:,1]==one_res[2])]
                            if filter_select.shape[0]!=0:
                                self.dict_df[key].loc[filter_select.index[-1],"Fault Healed Last Time"]=one_res[0]
                                self.dict_df[key].loc[filter_select.index[-1],"Fault Time Span(s)"]=str2timestamp(one_res[0])-str2timestamp(filter_select.iloc[-1,3])

    def fw_log(self):
        re_keys={
        'FW ERROR':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*?(\[.*?ERROR.*?\]\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'FW WARN':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*?(\[.*?WARN.*?\]\s([A-z0-9_\.:/]*).*)',   #1:时间 2:全行 3.关键词
        'FW FAULT':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*((fault_id.+)\sfrom .+isr.*)', #1.时间 2.全行 3.关键词
        'Restart count':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3})\s?\[.*?\]\scurrent\srestart\scounter.*?(\d+)' #1:时间 2:重启次数
    }
        self.dict_df['FW ERROR'] = pd.DataFrame([],columns=['Error Source File','Error Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['FW WARN'] = pd.DataFrame([],columns=['Warn Source File','Warn Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['FW FAULT'] = pd.DataFrame([],columns=['Fault Name','Fault logs','Restart Counter','Restart Time','Fault first Set Time','Fault Healed Last Time','Fault Time Span(s)'])
        
        last_restart_time = ""
        last_restart_count = ""
        
        res=read_file(self.fw_path)
        for idx,one_line in enumerate(res):
            for key in re_keys.keys():
                ret = re.search(re_keys[key],one_line)
                if ret:
                    one_res = list(ret.groups())
                    if key=='Restart count':
                        last_restart_time = one_res[0]
                        last_restart_count = one_res[1]
                    elif key=='FW FAULT':
                        self.dict_df[key].loc[self.dict_df[key].shape[0]] = [one_res[2],one_line,last_restart_count,last_restart_time,one_res[1],"",""]
                    else:
                        filter_select = self.dict_df[key].loc[(self.dict_df[key].iloc[:,0]==one_res[2])&(self.dict_df[key].iloc[:,2]==last_restart_count)]
                        if filter_select.shape[0]==0:
                            self.dict_df[key].loc[self.dict_df[key].shape[0]]=[one_res[2],one_line,last_restart_count,last_restart_time,one_res[0],one_res[0],1]
                        else:
                            self.dict_df[key].loc[filter_select.index[-1],"Last Occurence Time"]=one_res[0]
                            self.dict_df[key].loc[filter_select.index[-1],"Occurrence Times"]=filter_select.iloc[-1,6]+1
                            
        
    def client_log(self):
        re_keys={
            'WARN':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*(\[\s?WARN\s?\]\s\d*\s?([A-z0-9_\.:/]*).*)$',   #1:时间 2:全行 3.关键词
            'ERROR':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*(\[.*?ERROR.*?\]\s\d*\s?([A-z0-9_\.:/]*).*)$',   #1:时间 2:全行 3.关键词
            'FATAL':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*(\[.*?FATAL.*?\]\s\d*\s?([A-z0-9_\.:/]*).*)$',   #1:时间 2:全行 3.关键词
            'CRITI':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*(\[.*?CRITI.*?\]\s\d*\s?([A-z0-9_\.:/]*).*)$',   #1:时间 2:全行 3.关键词
            'PCS FAULT':'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{0,3})\s(\[.*?\]\s.*?fault_manager.cpp.*\s([A-Z0-9_]+)(\((\d+)\))?.+has.+been\s(set|heal).*)$',#1.时间 2.全行 3.关键词 4.(序号) 5.fault 序号 6.set or healed
            "FW FAULT":'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3}).*((fault_id.+)\sfrom .+isr.*)', #1.时间 2.全行 3.关键词
            'Restart count':'(\d{4}.\d{2}.\d{2}.*?\d{2}.\d{2}.\d{2}.\d{0,3})\s?\[.*?\]\scurrent\srestart\scounter.*?(\d+)' #1:时间 2:重启次数
        }
        
        self.dict_df['WARN'] = pd.DataFrame([],columns=['Warn Source File','Warn Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['ERROR'] = pd.DataFrame([],columns=['Error Source File','Error Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['FATAL'] = pd.DataFrame([],columns=['Fatal Source File','Fatal Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['CRITI'] = pd.DataFrame([],columns=['Critical Source File','Critical Log','Restart Counter','Restart Time','First Occurence Time','Last Occurence Time','Occurrence Times'])
        self.dict_df['PCS FAULT'] = pd.DataFrame([],columns=['Fault ID','Fault Name','Fault logs','Restart Counter','Restart Time','Fault first Set Time','Fault Healed Last Time','Fault Time Span(s)'])
        self.dict_df['FW FAULT'] = pd.DataFrame([],columns=['Fault Name','Fault logs','Restart Counter','Restart Time','Fault first Set Time','Fault Healed Last Time','Fault Time Span(s)'])
        
        last_restart_time = ""
        last_restart_count = ""
        
        with open(self.client_log_path,"r") as f:
            line_idx = 0
            while True:
                line_idx += 1
                try:
                    one_line = f.readline()
                except:
                    print(f"line {line_idx} read error")
                    continue
                if line_idx%100000==0:
                    print(f"line {line_idx}")
                if not one_line:
                    break
                for key in re_keys.keys():
                    ret = re.search(re_keys[key],one_line)
                    if ret:
                        one_res = list(ret.groups())
                        if key=='Restart count':
                            last_restart_time = one_res[0]
                            last_restart_count = one_res[1]
                        elif key=='FW FAULT':
                            self.dict_df[key].loc[self.dict_df[key].shape[0]] = [one_res[2],one_line,last_restart_count,last_restart_time,one_res[1],"",""]
                        elif key=='PCS FAULT':
                            if "set" in one_res[5]:
                                self.dict_df[key].loc[self.dict_df[key].shape[0]]=[one_res[4],one_res[2],one_res[1],last_restart_count,last_restart_time,one_res[0],"",""]
                            elif "heal" in one_res[5]:
                                filter_select = self.dict_df[key].loc[(self.dict_df[key].iloc[:,0]==one_res[4])&(self.dict_df[key].iloc[:,1]==one_res[2])]
                                if filter_select.shape[0]!=0:
                                    self.dict_df[key].loc[filter_select.index[-1],"Fault Healed Last Time"]=one_res[0]
                                    self.dict_df[key].loc[filter_select.index[-1],"Fault Time Span(s)"]=str2timestamp(one_res[0])-str2timestamp(filter_select.iloc[-1,5])
                        else:
                            filter_select = self.dict_df[key].loc[(self.dict_df[key].iloc[:,0]==one_res[2])&(self.dict_df[key].iloc[:,1]==one_res[1])]
                            if filter_select.shape[0]==0:
                                self.dict_df[key].loc[self.dict_df[key].shape[0]]=[one_res[2],one_res[1],last_restart_count,last_restart_time,one_res[0],one_res[0],1]
                            else:
                                self.dict_df[key].loc[filter_select.index[-1],"Last Occurence Time"]=one_res[0]
                                self.dict_df[key].loc[filter_select.index[-1],"Occurrence Times"]=filter_select.iloc[-1,6]+1


def main(args):
    ls = Log_statistic(pcs_path=args.pcs_path, fw_path=args.fw_path, client_log_path=args.client_path)
    save_folder = os.path.dirname(args.save_path)
    if not os.path.exists(save_folder):
        try:
            os.makedirs(save_folder)
        except:
            pass
    sum_shape = sum([ls.dict_df[key].shape[0] for key in ls.dict_df.keys()])
    if sum_shape == 0:
        return
    writer = pd.ExcelWriter(args.save_path)
    for key in ls.dict_df.keys():
        if ls.dict_df[key].shape[0] == 0:
            continue
        ls.dict_df[key].to_excel(writer, sheet_name=key, index=False)
    writer.close()
    ExcelFormat(args.save_path).format()


if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--fw-path',"-fp", type=str, default=None, help='log file path')
    parser.add_argument('--pcs-path',"-pp",type=str, default=None, help='log file path')
    parser.add_argument('--client-path', "-cp" ,type=str, default=None, help='log file path')
    parser.add_argument('--save-path', "-sp" ,type=str, default=None, help='save file path')
    args = parser.parse_args()
    main(args)