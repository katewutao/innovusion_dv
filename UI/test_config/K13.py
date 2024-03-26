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
    "relay unit":2, #记录仪的单元
    "relay channel":[
        1,
        2,
        3
        ],
    #记录仪的通道,格式为(1-15)之间的正整数,以,隔开,数量和ip的数量保持一致,对应关系为顺序一对一对应
    
    "time_dict":'''{
        "65:1": 20,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
    }''',
    #"上电时间:下电时间:电源电压,上电时间:下电时间:电源电压,上电时间:下电时间:电源电压":循环次数
    #时间单位为分钟
    #电源电压单位V，不设默认为13.5V
}
