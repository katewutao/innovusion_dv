config={
    "lidar_ip":[
        "172.168.1.10",
        ],  
    #雷达的ip,格式为英文输入法的双引号,内为ip,以,隔开
    
    "time_dict":{
        "0:60":0,
        "6:1:13.5,4:1:14":30,
    },
    #"上电时间:下电时间:电源电压,上电时间:下电时间:电源电压,上电时间:下电时间:电源电压":循环次数
    #时间单位为分钟
    #电源电压单位V，不设默认为13.5V
}