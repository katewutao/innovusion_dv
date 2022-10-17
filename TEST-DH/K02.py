####first
set_loop_time1="0:60"  ##通电时间:断电时间   ,分隔  单位:分钟
num_e1=0  #大循坏次数

###################last
set_loop_time2="0:49,5:1"  ##通电时间:断电时间   ,分隔  单位:分钟
num_e2=51  #大循坏次数
'''set_loop_time1="0:1,1:1,1:1,1:1"
num_e1=2
set_loop_time2="0:1,1:1"
num_e2=5'''



interval_time=5             # 上电时记录时间间隔(s)
data_num_power_off=10       # 断电时或通电0s空值数量
timeout_time=5

from dv import dv_test
if __name__=="__main__":
    dv_test(set_loop_time1,set_loop_time2,num_e1,num_e2,interval_time,data_num_power_off,timeout_time)