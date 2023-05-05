#! /usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
# import time
 
 
class logFrame(object):
    def getlogger(self, logname):
        self.logger = logging.getLogger("logger")
        # 判断是否有处理器，避免重复执行
        if not self.logger.handlers:
            # 日志输出的默认级别为warning及以上级别，设置输出info级别
            self.logger.setLevel(logging.DEBUG)
            # 创建一个处理器handler  StreamHandler()控制台实现日志输出
            sh = logging.StreamHandler()
            # 创建一个格式器formatter  （日志内容：当前时间，文件，日志级别，日志描述信息）
            formatter = logging.Formatter(fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(filename)s, %(lineno)s, %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
 
            # 创建一个文件处理器，文件写入日志
            # fh = logging.FileHandler(filename="./{}_log.txt".format(time.strftime("%Y_%m_%d %H_%M_%S",time.localtime())),encoding="utf8", mode='a')
            fh = logging.FileHandler(filename=logname, encoding="utf8", mode='w')
            # 创建一个文件格式器f_formatter
            f_formatter = logging.Formatter(fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] %(filename)s, %(lineno)s, %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
 
            # 关联控制台日志器—处理器—格式器
            self.logger.addHandler(sh)
            sh.setFormatter(formatter)
            # 设置处理器输出级别
            sh.setLevel(logging.INFO)
 
            # 关联文件日志器-处理器-格式器
            self.logger.addHandler(fh)
            fh.setFormatter(f_formatter)
            # 设置处理器输出级别
            fh.setLevel(logging.DEBUG)
 
        return self.logger
 

 
if __name__ == '__main__':
    logger = logFrame()
    log = logger.getlogger()
    log.info("I am right!!!")
    log.debug("I am wrong!!!")