
time_dict = {
    "0:1440": 1,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
    "0:1434,5:1": 9,
}


interval_time = 5             # 上电时记录时间间隔(s)
data_num_power_off = 10       # 断电时或通电0s空值数量
timeout_time = 5

from dv import dv_test
if __name__=="__main__":
    dv_test(time_dict,interval_time,data_num_power_off,timeout_time)