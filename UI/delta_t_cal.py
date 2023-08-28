import os
import pandas as pd
import datetime,time

def str2timestamp(str1):
    str1=str(str1)
    import re
    key='(\d{4}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2}(.+?)\d{1,2})(\.?\d*)'
    ret=re.search(key,str1)
    if ret:
        deci=0
        if len(ret.group(7))>1:
            deci=float('0'+ret.group(7))
        ret2=re.match("(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+).*?(\d+)$",ret.group(1))
        A=ret2.group(1)+(2-len(ret2.group(2)))*'0'+ret2.group(2)+(2-len(ret2.group(3)))*'0'+ret2.group(3)+(2-len(ret2.group(4)))*'0'+ret2.group(4)+(2-len(ret2.group(5)))*'0'+ret2.group(5)+(2-len(ret2.group(6)))*'0'+ret2.group(6)
        if float(A)>=19700101080000:
            return time.mktime(time.strptime(ret.group(1), f'%Y{ret.group(2)}%m{ret.group(3)}%d{ret.group(4)}%H{ret.group(5)}%M{ret.group(6)}%S'))+deci
        elif float(A)<19700101000000:
            return 0
        else:
            return -8*60*60+int(A[8:10])*60*60+int(A[10:12])*60+int(A[12:14])+deci
    return 0

def main(path):
    df=pd.read_csv(path)
    df_filter=df.loc[df["SN"]>0]
    last_time=0
    for i in range(df_filter.shape[0]):
        time_str=df_filter.iloc[i]["time"].strip()
        time_stamp=str2timestamp(time_str)
        if last_time==0:
            last_time=time_stamp
        else:
            delta_t=time_stamp-last_time
            last_time=time_stamp
            if delta_t>6:
                print(df_filter.iloc[i]["time"].strip(),delta_t)
                
if __name__=="__main__":
    main("record_172_168_1_24.csv")