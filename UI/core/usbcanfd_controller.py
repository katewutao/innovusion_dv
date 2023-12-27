#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File: usbcanfd_controler.py
@Time: 2022/07/06 15:14:57
@Author: ZhuLi.Wu
@Mail: gavin.wu@cn.innovusion.com
'''

import os
from ctypes import *
import time
import platform
import sys
import threading
from multiprocessing import Process, Value, Lock
import logging as logger


if platform.system() in ("Linux", "linux"):
    usbcanfd_lib = cdll.LoadLibrary('./lib/libusbcanfd.so')
else:
    logger.error('OS do not match..')
    sys.exit(1)


RES_ON            = 1  #Resistance setting
RES_OFF           = 0 
CAN_TRES          = 0x18 #Resistance address


class asetConfig(Structure):
    _fields_ = [
        ('tseg1', c_uint8),
        ('tseg2', c_uint8),
        ('sjw', c_uint8),
        ('smp', c_uint8),
        ('brp', c_uint16)
        ]


class bsetConfig(Structure):
    _fields_ = [
        ('tseg1', c_uint8),
        ('tseg2', c_uint8),
        ('sjw', c_uint8),
        ('smp', c_uint8),
        ('brp', c_uint16)
        ]


class ZCANInit(Structure):
    _fields_ = [('clk', c_uint32),
                ('mode', c_uint32),
                ('aset', asetConfig),
                ('bset', bsetConfig)]


class ZCAN_DEV_INF(Structure):
    _fields_ = [
        ('hw_ver', c_uint16),
        ('fw_ver', c_uint16),
        ('dr_ver', c_uint16),
        ('api_ver', c_uint16),
        ('irq', c_uint16),
        ('Channels', c_uint8),
        ('sn', c_uint8),
        ('id', c_uint8),
        ('pad', c_uint16)
    ]


# can/canfd messgae info 
class ZCAN_MSG_INFO(Structure):
    _fields_=[
        ("txm",c_uint,4), # TXTYPE:0 normal,1 once, 2self
        ("fmt",c_uint,4), # 0-can2.0 frame,  1-canfd frame
        ("sdf",c_uint,1), # 0-data frame, 1-remote frame
        ("sef",c_uint,1), # 0-std_frame, 1-ext_frame
        ("err",c_uint,1), # error flag
        ("brs",c_uint,1), # bit-rate switch ,0-Not speed up ,1-speed up
        ("est",c_uint,1), # error state 
        ("pad",c_uint,19)]

# can/canfd msg header
class ZCAN_MSG_HDR(Structure):  
    _fields_=[
        ("ts",c_uint32),  #timestamp
        ("id",c_uint32),  #can-id
        ("info",ZCAN_MSG_INFO),
        ("pad",c_uint16),
        ("chn",c_uint8),  #channel
        ("len",c_uint8)]  #data length


class ZCAN_20_MSG(Structure):
    _fields_ = [
        ('msg_header', ZCAN_MSG_HDR),
        ('dat', c_ubyte*8)
    ]

class ZCAN_FD_MSG(Structure):
    _fields_ = [
        ('msg_header', ZCAN_MSG_HDR),
        ('dat', c_ubyte*64)
    ]

class Resistance(Structure):
    _fields_=[("res",c_uint8)
              ]



ZCAN_DEVICE_TYPE  = c_uint32
ZCAN_DEVICE_INDEX = c_uint32
ZCAN_CHANNEL      = c_uint32
ZCAN_Reserved     = c_uint32

class USBCANFD(object):
    canfd_test    = 1
    USBCANFD_200U =   ZCAN_DEVICE_TYPE(33)
    DEVICE_INDEX  =   ZCAN_DEVICE_INDEX(0)
    CHANNEL_INDEX =   ZCAN_CHANNEL
    Reserved      =   ZCAN_Reserved(0)

    def __init__(self, **kwargs):
        self.tx_ch = kwargs['device']['tx_ch']
        self.rx_ch = kwargs['device']['rx_ch']
        self.send_count = kwargs['frame']['send_count']
        self.device_info = {}
        self.ch_init_config = {}
        self.ch_err_info = {}
        self.ch_status = {}
        self.recv_data = {}
        self.recv_data_FD = {}
        self.len = None
        self.count = kwargs['frame']['frame_count']
        self.attribute_path = ''
        self.attribute_value = None
        self.wait_time = 500
        self.id = int(str(kwargs['frame']['frame_ID']), 16)
        self.payload_len = kwargs['frame']['payload_len']
        # self.data_mazu = (0x00, 0x40, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff)
        self.payload = kwargs['frame']['payload'] if kwargs['frame']['payload'] else '0011223344556677'
        if len(self.payload) < self.payload_len *2:
            self.payload += '0'*(self.payload_len *2 - len(self.payload))

        self.payload = [int(self.payload[i:i+2], 16) for i in range(0, len(self.payload), 2)]
        # self.data_lidar = (0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77)
        self.multi_id = kwargs['frame']['multiFrame_ID']
        self.exit_recv = Value(c_bool, False)
        self.exit_send = Value(c_bool, True)
        self.interval_ms = kwargs['frame']['send_interval']


    @staticmethod
    def check_usbcanFD_dev_status():
        ret = os.popen("lsusb").read()
        if "3068:0009" in ret:
            return True
        else:
            return False

    
    def open_device(self):
        self.device_handle = usbcanfd_lib.VCI_OpenDevice(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.Reserved)
        if self.device_handle == 0:
            logger.error('sts:{}: open device fail!'.format(self.device_handle))
            return False
        else:
            logger.info('sts:{}: open device({}) success!'.format(self.device_handle, USBCANFD.USBCANFD_200U.value))
            return True
    
    def get_deviceInfo(self):
        """
        typedef struct {g
            U16 hwv; /**< hardware version */
            U16 fwv; /**< firmware version */
            U16 drv; /**< driver version */
            U16 api; /**< API version */
            U16 irq; /**< IRQ */
            U8 chn; /**< channels */
            U8 sn[20]; /**< serial number */
            U8 id[40]; /**< card id */
            U16 pad[4];
        }ZCAN_DEV_INF;
        """
        device_info = ZCAN_DEV_INF()
        get_sts = usbcanfd_lib.VCI_ReadBoardInfo(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, byref(device_info))

    # def is_device_online(self):
    #     sts = usbcanfd_lib.VIC_IsDeviceOnLine(self.device_handle)
    #     if sts in ('STATUS_ONLINE', 1, 2):
    #         log.info('Device is online!')
    #     else:
    #         log.warn('Device is not online!')

    def set_value(self):
        set_ret = usbcanfd_lib.VCI_SetValue(self.device_handle, self.attribute_path, self.attribute_value)

    def init_CAN(self, channel, baud_rate=500):
        """
        """
        # CH_init = ZCANInit()
        # CH_init.clk = 60000000  # USBCANFD-200U clock is 60MHz
        # CH_init.mode = 0  # 工作模式，0 表示正常模式（相当于正常节点），1 表示只听模式（只接收，不影响总线）
        # CH_init.aset.tseg1 = 1
        # CH_init.aset.tseg2 = 0
        # CH_init.aset.sjw = 2
        # CH_init.aset.smp = 75  # smp is sample point, not involved in baudrate calculation
        # CH_init.aset.brp = 29
        # CH_init.bset.tseg1 = 1
        # CH_init.bset.tseg2 = 0
        # CH_init.bset.sjw = 2
        # CH_init.bset.smp = 75
        # CH_init.bset.brp = 2

        CH_init = ZCANInit()
        if baud_rate == 500:
            CH_init.clk = 60000000  # USBCANFD-200U clock is 60MHz
            CH_init.mode = 0  # 工作模式，0 表示正常模式（相当于正常节点），1 表示只听模式（只接收，不影响总线）
            CH_init.aset.tseg1 = 10
            CH_init.aset.tseg2 = 2
            CH_init.aset.sjw = 2
            CH_init.aset.smp = 0  # smp is sample point, not involved in baudrate calculation
            CH_init.aset.brp = 7
            CH_init.bset.tseg1 = 10
            CH_init.bset.tseg2 = 2
            CH_init.bset.sjw = 2
            CH_init.bset.smp = 0
            CH_init.bset.brp = 1
        if baud_rate == 250:
            CH_init.clk = 60000000  # USBCANFD-200U clock is 60MHz
            CH_init.mode = 0  # 工作模式，0 表示正常模式（相当于正常节点），1 表示只听模式（只接收，不影响总线）
            CH_init.aset.tseg1 = 5
            CH_init.aset.tseg2 = 0
            CH_init.aset.sjw = 2
            CH_init.aset.smp = 87  # smp is sample point, not involved in baudrate calculation
            CH_init.aset.brp = 29
            CH_init.bset.tseg1 = 5
            CH_init.bset.tseg2 = 0
            CH_init.bset.sjw = 2
            CH_init.bset.smp = 87
            CH_init.bset.brp = 29
            
        self.ch_handle = usbcanfd_lib.VCI_InitCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(CH_init))

        if self.ch_handle == 0:
            logger.error(f'Channel-{channel} init fail!')
            return False
        else:
            logger.info(f'Channel-{channel} init success!')
            return True
        # else:
        #     self.ch0_handle = usbcanfd_lib.VCI_InitCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(0), byref(CH_init))
        #     self.ch1_handle = usbcanfd_lib.VCI_InitCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(1), byref(CH_init))

        #     if self.ch0_handle == 0 or self.ch1_handle == 0:
        #         logger.error(f'sts: [{self.ch0_handle}, {self.ch1_handle}], Channel-{self.ch_index} init fail!')
        #         return False
        #     else:
        #         logger.info(f'sts: [{self.ch0_handle}, {self.ch1_handle}], Channel-{self.ch_index} init success!')
        #         return True

    def set_reference(self, channel):
        Res = Resistance()
        Res.res = RES_ON
        set_ret = usbcanfd_lib.VCI_SetReference(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), CAN_TRES, byref(Res))

        if set_ret == 0:
            logger.error(f'set ch-c{channel} reference fail!')
            return False
        else:
            logger.info(f'set ch-c{channel} reference success!')
            return True
       
    
    def start_CAN(self, channel):
        start_ret = usbcanfd_lib.VCI_StartCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel))
        if start_ret == 0:
            logger.error(f'sts:{start_ret}, Open Channel-{channel} fail!')
            return False
        else:
            logger.info(f'sts:{start_ret},Open Channel-{channel} success!')
            return True

    def reset_CAN(self, channel):
        reset_ret = usbcanfd_lib.VCI_ResetCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel))
        if reset_ret == 0:
            logger.error(f'Reset Channel-{channel} fail!')
            return False
        else:
            logger.info(f'Reset Channel-{channel} success!')
            return True

    def get_recv_num_from_buffer(self):
        return usbcanfd_lib.VCI_ClearBuffer(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        
    def clear_buffer(self):
        clear_ret = usbcanfd_lib.VCI_ClearBuffer(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        if clear_ret == 0:
            logger.error(f'Clear Channel-{self.can_index.value} buffer fail!')
        else:
            logger.info(f'Clear Channel-{self.can_index.value} buffer success!')

    def read_CH_Err(self):
        errInfo_ret = usbcanfd_lib.VCI_ReadChannelErrInfo(self.ch_handle, self.ch_err_info)
    
    def read_CH_Sts(self):
        CH_sts_ret = usbcanfd_lib.VCI_ReadChannelErrInfo(self.ch_handle, self.ch_status)
    
    def transmit_frame(self, channel):  #CAN2.0
        count = 1
        while self.exit_send.value:
            can_20_data = (ZCAN_20_MSG*self.count)()
            for i in range(self.count):
                can_20_data[i].msg_header.ts=0  # 硬件接收时间戳，结构体用于发送时无效，无需填充
                can_20_data[i].msg_header.id=self.id
                can_20_data[i].msg_header.info.txm = 0 #0--normal send, 2--self test
                can_20_data[i].msg_header.info.fmt = 0 #can2.0
                can_20_data[i].msg_header.info.sdf = 0 #data frame
                can_20_data[i].msg_header.info.sef = 0 #std frame
                can_20_data[i].msg_header.info.err = 0
                can_20_data[i].msg_header.info.brs = 0
                can_20_data[i].msg_header.info.est = 0
                can_20_data[i].msg_header.pad      = 0
                can_20_data[i].msg_header.chn      = channel
                can_20_data[i].msg_header.len      = self.payload_len
                for j in range (can_20_data[i].msg_header.len):
                    can_20_data[i].dat[j]=self.payload[j]

            send_CAN_number = usbcanfd_lib.VCI_TransmitFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(can_20_data), self.count)
            # logger.info(f"CH:{channel} send {send_CANFD_number} CANFD frames!")
            # for i in range(send_CAN_number):
            #     logger.info(f"[Tx] FrameID: {hex(can_20_data[i].msg_header.id)}, Data: {list(map(lambda x: hex(x), can_20_data[i].dat))[:8]}")
            time.sleep(self.interval_ms/1000)

            if self.send_count != -1 and count == self.send_count:
                self.exit_send.value = False
                self.exit_recv.value = True
                break
            count += 1


    def receive_frame(self, channel):  # CAN2.0
        while not self.exit_recv.value:
            recv_can_20 = (ZCAN_FD_MSG*self.count)()
            recv_CAN_number = usbcanfd_lib.VCI_ReceiveFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(recv_can_20), self.count, self.wait_time)
            for i in range(recv_CAN_number):
                logger.info(f"[Rx] FrameID: {hex(recv_can_20[i].msg_header.id)}, Data: {list(map(lambda x: hex(x), recv_can_20[i].dat))[:self.payload_len]}")


    def transmit_frame_FD(self, channel):  # CANFD
        count = 1
        while self.exit_send.value:
            canfd_data = (ZCAN_FD_MSG*self.count)()
            for i in range(self.count):
                canfd_data[i].msg_header.ts=0  # 硬件接收时间戳，结构体用于发送时无效，无需填充
                canfd_data[i].msg_header.id=self.id
                canfd_data[i].msg_header.info.txm = 0 #0--normal send, 2--self test
                canfd_data[i].msg_header.info.fmt = 1 #canFD
                canfd_data[i].msg_header.info.sdf = 0 #data frame
                canfd_data[i].msg_header.info.sef = 0 #std frame
                canfd_data[i].msg_header.info.err = 0
                canfd_data[i].msg_header.info.brs = 0
                canfd_data[i].msg_header.info.est = 0
                canfd_data[i].msg_header.pad      = 0
                canfd_data[i].msg_header.chn      = channel
                canfd_data[i].msg_header.len      = self.payload_len
                for j in range (canfd_data[i].msg_header.len):
                    canfd_data[i].dat[j]=self.payload[j]
            send_CANFD_number = usbcanfd_lib.VCI_TransmitFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(canfd_data), self.count)
            logger.info(f"CH:{channel} send {send_CANFD_number} CAN frames!")
            for i in range(send_CANFD_number):
                logger.info(f"[Tx] FrameID: {hex(canfd_data[i].msg_header.id)}, Data: {list(map(lambda x: hex(x), canfd_data[i].dat))[:self.payload_len]}")
            time.sleep(self.interval_ms/1000)

            if self.send_count != -1 and count == self.send_count:
                self.exit_send.value = False
                self.exit_recv.value = True
                break
            count += 1
        os.popen("echo 'EXIT_CAN' | nc -nv -w1 127.0.0.1 10001")
    

    def transmit_multi_frame_FD(self, channel):  # CANFD
        count = 1
        while self.exit_send.value:
            canfd_data = (ZCAN_FD_MSG*len(self.multi_id))()
            for i in range(len(self.multi_id)):
                canfd_data[i].msg_header.ts=0  # 硬件接收时间戳，结构体用于发送时无效，无需填充
                canfd_data[i].msg_header.id=int('%s' % self.multi_id[i], 16)
                canfd_data[i].msg_header.info.txm = 0 #0--normal send, 2--self test
                canfd_data[i].msg_header.info.fmt = 1 #canFD
                canfd_data[i].msg_header.info.sdf = 0 #data frame
                canfd_data[i].msg_header.info.sef = 0 #std frame
                canfd_data[i].msg_header.info.err = 0
                canfd_data[i].msg_header.info.brs = 0
                canfd_data[i].msg_header.info.est = 0
                canfd_data[i].msg_header.pad      = 0
                canfd_data[i].msg_header.chn      = channel
                canfd_data[i].msg_header.len      = self.payload_len
                for j in range (canfd_data[i].msg_header.len):
                    canfd_data[i].dat[j]=self.payload[j]
                # usbcanfd_lib.VCI_TransmitFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(canfd_data), self.count)
            send_CANFD_number = usbcanfd_lib.VCI_TransmitFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(canfd_data), len(self.multi_id))
            logger.info(f"CH:{channel} send {send_CANFD_number} CANFD frames!")
            for i in range(send_CANFD_number):
                logger.info(f"[Tx] FrameID: {hex(canfd_data[i].msg_header.id)}, Data: {list(map(lambda x: hex(x), canfd_data[i].dat))[:self.payload_len]}")
            time.sleep(self.interval_ms/1000)

            if self.send_count != -1 and count == self.send_count:
                self.exit_send.value = False
                self.exit_recv.value = True
                break
            count += 1
        os.popen("echo 'EXIT_CAN' | nc -nv -w1 127.0.0.1 10001")

    def receive_frame_FD(self, channel, hostname=None, redis=None):  #CANFD
        s_time = time.time()
        self_frame = False
        lidar_frame = False
        while not self.exit_recv.value:
            recv_canfd = (ZCAN_FD_MSG*self.count)()
            recv_CANFD_number = usbcanfd_lib.VCI_ReceiveFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX(channel), byref(recv_canfd), self.count, self.wait_time)
            logger.info(f"Total received {recv_CANFD_number} CANFD frames from channel-{channel}!")
            for i in range(recv_CANFD_number):
                logger.info(f"[Rx] FrameID: {hex(recv_canfd[i].msg_header.id)}, Data: {list(map(lambda x: hex(x), recv_canfd[i].dat))[:self.payload_len]}")
                if hex(recv_canfd[i].msg_header.id) == "0x143":
                    lidar_frame = True
                elif hex(recv_canfd[i].msg_header.id) == hex(self.id) or hex(recv_canfd[i].msg_header.id) in self.multi_id:
                    self_frame = True
            if time.time() -s_time > 5:
                if self_frame and lidar_frame:
                    if hostname and redis:
                        redis.hmset(hostname, {'res':'Pass', 'msg':'null', 'ts': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))})
                elif self_frame and not lidar_frame:
                    if hostname and redis:
                        redis.hmset(hostname, {'res':'Fail', 'msg':'recv self-frame, but not recv lidar-frame(0x143)', 'ts': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))})
                elif not self_frame and lidar_frame:
                    if hostname and redis:
                        redis.hmset(hostname, {'res':'Fail', 'msg':'not recv self-frame, recv lidar-frame(0x143)', 'ts': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))})
                elif not self_frame and not lidar_frame:
                    if hostname and redis:
                        redis.hmset(hostname, {'res':'Fail', 'msg':'both not recv self-frame and lidar-frame(0x143)', 'ts': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))})
                    # os.popen("echo 'disconnected' | nc -nv -w1 127.0.0.1 10002")
                    # break
                s_time = time.time()
                self_frame = False
                lidar_frame = False

    def close_device(self):
        ret = usbcanfd_lib.VCI_CloseDevice(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX)
        if ret in ('STATUS_OK', 'OK', 1):
            logger.info('CloseDevice success!')
        else:
            logger.error('CloseDevice fail!')
    

class USBCAN():
    def __init__(self, conf_file):
        import json
        conf_file = open(conf_file, 'r', encoding='utf-8')
        self.conf = json.load(conf_file)
        conf_file.close()
        self.tx_ch = self.conf['device']['tx_ch']
        self.rx_ch = self.conf['device']['rx_ch']
        

    def run_usbcan(self):
        self.usbcan = USBCANFD(**self.conf)
        if not self.usbcan.open_device():
            sys.exit()
        # usbcanfd.get_deviceInfo()
        self.usbcan.reset_CAN(self.tx_ch)
        self.usbcan.reset_CAN(self.rx_ch)
        self.usbcan.set_reference(self.tx_ch)
        self.usbcan.set_reference(self.rx_ch)
        self.usbcan.init_CAN(self.tx_ch)
        self.usbcan.init_CAN(self.rx_ch)
        self.usbcan.start_CAN(self.tx_ch)
        self.usbcan.start_CAN(self.rx_ch)
        
        threading.Thread(target=self.usbcan.receive_frame_FD, args=(self.rx_ch,)).start()
        threading.Thread(target=self.usbcan.transmit_multi_frame_FD, args=(self.tx_ch,)).start()


    def stop_usbcan(self):
        self.usbcan.exit_send.value = False
        self.usbcan.exit_recv.value = True
        
        self.usbcan.reset_CAN(self.tx_ch)
        self.usbcan.reset_CAN(self.rx_ch)
        self.usbcan.close_device()


if __name__ == '__main__':
    # Demo code
    test = USBCAN('config/CANFD_Config.json')
    test.run_usbcan()

    time.sleep(600)

    test.stop_usbcan()