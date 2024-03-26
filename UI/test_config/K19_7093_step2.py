config={
    "lidar_ip":[
        "172.168.1.7",
        "172.168.1.8",
        "172.168.1.9",
        "172.168.1.10",
        "172.168.1.11",
        "172.168.1.12",
        ],  
    #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
    "relay unit":2, #记录仪的单元
    "relay channel":[
        1,
        2,
        3
        ],
    #记录仪的通道,格式为英文输入法的双引号,内为通道,以,隔开
    
    "time_dict":'''{
        "0:30": 1,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
        "0:1437,2:1": 1,
        "0:30": 1,
        "0:1437,2:1": 9,
    }''',
    #"上电时间:下电时间:电源电压,上电时间:下电时间:电源电压,上电时间:下电时间:电源电压":循环次数
    #时间单位为分钟
    #电源电压单位V，不设默认为13.5V
}
