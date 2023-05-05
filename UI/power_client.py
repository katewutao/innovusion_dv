import power
import os
import pandas as pd
import datetime

def main(save_path):

    if not os.path.exists(save_path):
        os.mkdir(save_path)
    pow=power.Power()
    while True:
        try:
            df=pd.DataFrame([pow.PowerStatus()])
            df.to_csv(os.path.join(save_path,'pow_status.csv'),header=None,index=None)
        except:
            print(f"[{datetime.datetime.now()}]get power permission")
            os.system('sshpass -p demo sudo python3 ./power.py')
            try:
                pow=power.Power()
            except:   
                continue

if __name__=="__main__":
    import argparse
    parses=argparse.ArgumentParser()
    parses.add_argument("--save-folder","-s",type=str,required=True)
    args=parses.parse_args()
    main(args.save_folder)