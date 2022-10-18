#!/usr/bin/python3

# /**
#  * @author katewutao
#  * @email kate.wu@cn.innovusion.com
#  * @create date 2022-03-22 16:48:51
#  * @modify date 2022-03-22 16:48:51
#  * @desc [description]
#  */


import power
import os
import pandas as pd
import datetime

if not os.path.exists(os.getcwd()+'/result'):
    os.mkdir(os.getcwd()+'/result')
pow=power.Power()
while True:
    try:
        df=pd.DataFrame([pow.PowerStatus()])
        df.to_csv(os.getcwd()+'/result/pow_status.csv',header=None,index=None)
    except:
        print(f"[{datetime.datetime.now()}]get power permission")
        os.system('sshpass -p demo sudo python3 ./power.py')
        try:
            pow=power.Power()
        except:   
            continue
