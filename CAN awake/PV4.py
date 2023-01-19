from main import main
import os
from oneclient import save_path

config={
    "lidar_ip":[
        "172.168.1.10",
        "172.168.1.2",
        "172.168.1.3",
        "172.168.1.4",
        "172.168.1.5",
        "172.168.1.6"
        ],
    "time_dict":{
        "0:60,20:32": 10,
        "0:49,5:1": 51
    },
    "data_num_power_off":10,
    "interval_time":5,
    "timeout_time":5
}


if __name__=="__main__":
    log_path=os.path.join(save_path,"log")
    main(config,log_path)