修改通断电时间和循环次数可通过修改config.json文件中的下面部分

"CAN唤醒时间:CAN休眠时间,CAN唤醒时间:CAN休眠时间,CAN唤醒时间:CAN休眠时间":循环次数
时间单位为分钟
time_dict = {
    "0:60,20:32": 10,  # 通电时间:断电时间   ,分隔  :循环次数 单位:分钟 :循环次数
    "0:49,5:1": 51,
}
