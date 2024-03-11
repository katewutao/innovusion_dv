config={
    "lidar_ip":[
        "172.168.1.75",
        "172.168.1.76",
        "172.168.1.77",
        "172.168.1.78",
        "172.168.1.79",
        "172.168.1.80",
        ],  
    #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
    "channel": 2, #继电器的通道
    
    "time_dict":'''{
        "1:1": 10000,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
    }''',
    #"上电时间:下电时间:电源电压,上电时间:下电时间:电源电压,上电时间:下电时间:电源电压":循环次数
    #时间单位为分钟
    #电源电压单位V，不设默认为13.5V
}
