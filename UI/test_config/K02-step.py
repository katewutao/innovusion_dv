config={
    "lidar_ip":[
        "172.168.1.19",
        "172.168.1.20",
        "172.168.1.21",
        "172.168.1.22",
        "172.168.1.23",
        "172.168.1.24",
        ],  
    #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
    
    "time_dict":{
        "0:60": 0,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
        "0:49,5:1": 51,
    },
    #"上电时间:下电时间:电源电压,上电时间:下电时间:电源电压,上电时间:下电时间:电源电压":循环次数
    #时间单位为分钟
    #电源电压单位V，不设默认为13.5V
}