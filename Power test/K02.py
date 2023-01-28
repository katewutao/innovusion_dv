config={
    "lidar_ip":[
        "172.168.1.10",
        "172.168.1.2",
        "172.168.1.3",
        "172.168.1.4",
        "172.168.1.5",
        "172.168.1.6",
        ],  
    #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
    
    "time_dict":{
        "0:60": 0,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
        "0:49,5:1": 51,
    },
    #"通电时间:断电时间,通电时间:断电时间,通电时间:断电时间":循环次数
    #时间单位为分钟
    
    "data_num_power_off":10,    #断电时空数据数量
    "interval_time":5,          #记录雷达状态的时间间隔
    "timeout_time":5,           #获取雷达连接权限的超时时间
}


from dv import dv_test
if __name__=="__main__":
    dv_test(config)