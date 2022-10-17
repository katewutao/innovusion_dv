#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File: usbcanfd_controler.py
@Time: 2022/07/06 15:14:57
@Author: ZhuLi.Wu
@Mail: gavin.wu@cn.innovusion.com
'''

from ctypes import *
import time
import platform
import sys
from common.python_logging import logFrame

if platform.system() in ("Linux", "linux"):
    usbcanfd_lib = cdll.LoadLibrary('./lib/libusbcanfd.so')
else:
    print('OS do not match..')
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
    _field_ = [
        ('tseg1', c_uint8),
        ('tseg2', c_uint8),
        ('sjw', c_uint8),
        ('smp', c_uint8),
        ('brp', c_uint16)
    ]


class ZCANInit(Structure):
    _fields_ = [('clk', c_uint32), ('mode', c_uint32), ('aset', asetConfig), ('bset', bsetConfig)]


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
    CHANNEL_INDEX =   ZCAN_CHANNEL(0)
    Reserved      =   ZCAN_Reserved(0)

    def __init__(self, *args, **kwargs):
        self.can_index = 0
        self.device_info = {}
        self.ch_init_config = {}
        self.ch_err_info = {}
        self.ch_status = {}
        self.recv_data = {}
        self.recv_data_FD = {}
        self.len = None
        self.count = 2
        self.attribute_path = ''
        self.attribute_value = None
        self.wait_time = 100
        self.id = int(str(kwargs['id']['frame_ID']), 16)
        self.data = (0x00, 0x40, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff)
        self.data_lidar = (0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77)
        self.multi_id = kwargs['id']['multiFrame_ID']


    def open_device(self):
        self.device_handle = usbcanfd_lib.VCI_OpenDevice(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.Reserved)
        if self.device_handle == 0:
            log.error('{}: open device fail!'.format(self.device_handle))
        else:
            log.info('{}: open device({}) success!'.format(self.device_handle, USBCANFD.USBCANFD_200U.value))
    
    def get_deviceInfo(self):
        """
        typedef struct {
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

    def init_CAN(self):
        """
        """
        CH_init = ZCANInit()
        # CH_init.clk = 60000000  # USBCANFD-200U clock is 60MHz
        # CH_init.mode = 0  # 工作模式，0 表示正常模式（相当于正常节点），1 表示只听模式（只接收，不影响总线）
        # CH_init.aset.tseg1 = 1
        # CH_init.aset.tseg2 = 0
        # CH_init.aset.sjw = 0
        # CH_init.aset.smp = 75  # smp is sample point, not involved in baudrate calculation
        # CH_init.aset.brp = 29
        # CH_init.bset.tseg1 = 2
        # CH_init.bset.tseg2 = 0
        # CH_init.bset.sjw = 0
        # CH_init.bset.smp = 80
        # CH_init.bset.brp = 5

        CH_init.clk = 60000000  # USBCANFD-200U clock is 60MHz
        CH_init.mode = 0  # 工作模式，0 表示正常模式（相当于正常节点），1 表示只听模式（只接收，不影响总线）
        CH_init.aset.tseg1 = 1
        CH_init.aset.tseg2 = 0
        CH_init.aset.sjw = 2
        CH_init.aset.smp = 75  # smp is sample point, not involved in baudrate calculation
        CH_init.aset.brp = 29
        CH_init.bset.tseg1 = 1
        CH_init.bset.tseg2 = 0
        CH_init.bset.sjw = 2
        CH_init.bset.smp = 75
        CH_init.bset.brp = 2

        self.ch_handle = usbcanfd_lib.VCI_InitCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, byref(CH_init))
        if self.ch_handle == 0:
            log.error(f'Channel-{self.can_index} init fail!')
        else:
            log.info(f'Channel-{self.can_index} init success!')

    def set_reference(self):
        Res = Resistance()
        Res.res = RES_ON
        set_ret = usbcanfd_lib.VCI_SetReference(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, CAN_TRES, byref(Res))
        if set_ret == 0:
            log.error(f'set reference fail!')
        else:
            log.info(f'set reference success!')
    
    def start_CAN(self):
        start_ret = usbcanfd_lib.VCI_StartCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        if start_ret == 0:
            log.error(f'Open Channel-{self.can_index} fail!')
        else:
            log.info(f'Open Channel-{self.can_index} success!')

    def reset_CAN(self):
        reset_ret = usbcanfd_lib.VCI_ResetCAN(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        if reset_ret == 0:
            log.error(f'Reset Channel-{self.can_index} fail!')
        else:
            log.info(f'Reset Channel-{self.can_index} success!')

    def get_recv_num_from_buffer(self):
        return usbcanfd_lib.VCI_ClearBuffer(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        
    def clear_buffer(self):
        clear_ret = usbcanfd_lib.VCI_ClearBuffer(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX)
        if clear_ret == 0:
            log.error(f'Clear Channel-{self.can_index} buffer fail!')
        else:
            log.info(f'Clear Channel-{self.can_index} buffer success!')

    def read_CH_Err(self):
        errInfo_ret = usbcanfd_lib.VCI_ReadChannelErrInfo(self.ch_handle, self.ch_err_info)
    
    def read_CH_Sts(self):
        CH_sts_ret = usbcanfd_lib.VCI_ReadChannelErrInfo(self.ch_handle, self.ch_status)
    
    def transmit_frame(self):  #CAN2.0
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
            can_20_data[i].msg_header.chn      = 0
            can_20_data[i].msg_header.len      = 8 
            for j in range (can_20_data[i].msg_header.len):
                can_20_data[i].dat[j]=self.data[j]

        send_CAN_number = usbcanfd_lib.VCI_Transmit(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, byref(can_20_data), self.count)
        log.info(f"Total Send {send_CAN_number} CAN frames to channel-{self.can_index}!")

    def receive_frame(self):  # CAN2.0
        recv_can_20 = ZCAN_20_MSG()
        recv_CAN_number = usbcanfd_lib.VCI_Receive(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, byref(recv_can_20), self.count, self.wait_time)
        log.info(f"Total received {recv_CAN_number} CAN frames from channel-{self.can_index}!")

    def transmit_frame_FD(self):  # CANFD
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
            canfd_data[i].msg_header.chn      = 0
            canfd_data[i].msg_header.len      = 32
            for j in range (canfd_data[i].msg_header.len - 24):
                canfd_data[i].dat[j]=self.data_lidar[j]
        send_CANFD_number = usbcanfd_lib.VCI_TransmitFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, byref(canfd_data), self.count)
        log.info(f"Total Send {send_CANFD_number} CANFD frames to channel-{self.can_index}!")

    def receive_frame_FD(self):  #CANFD
        recv_canfd = ZCAN_FD_MSG()
        recv_CANFD_number = usbcanfd_lib.VCI_ReceiveFD(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX, USBCANFD.CHANNEL_INDEX, byref(recv_canfd), self.count, self.wait_time)
        log.info(f"Total received {recv_CANFD_number} CANFD frames from channel-{self.can_index}!")

    def close_device(self):
        ret = usbcanfd_lib.VCI_CloseDevice(USBCANFD.USBCANFD_200U, USBCANFD.DEVICE_INDEX)
        if ret in ('STATUS_OK', 'OK', 1):
            log.info('CloseDevice success!')
        else:
            log.error('CloseDevice fail!')
    

class USBCANFD_Controler(object):
    def __init__(self):
        import json
        json_obj = open('./config/CANFD_Config.json', 'r', encoding='utf-8')
        self.js_cfg = json.load(json_obj)
        logger = logFrame()
        global log
        log = logger.getlogger('./CANFD_MSG.log')
        json_obj.close()
        self.init_usbcanfd()
    
    def init_usbcanfd(self):
        USBCANFD.USBCANFD_200U = c_uint32(self.js_cfg['device']['device_type'])
        USBCANFD.DEVICE_INDEX = c_uint32(self.js_cfg['device']['device_idx'])
        USBCANFD.CHANNEL_INDEX = c_uint32(self.js_cfg['device']['channel'])
        USBCANFD.Reserved = c_uint32(self.js_cfg['device']['reserved'])
        self.usbcanfd = USBCANFD(**self.js_cfg)
        self.usbcanfd.open_device()
        # self.usbcanfd.reset_CAN()
        self.usbcanfd.set_reference()
        self.usbcanfd.init_CAN()
        self.usbcanfd.start_CAN()
        
        
    def start(self):
        if self.js_cfg['can_type']['canfd']:
            if self.js_cfg['loop']['loop_count'] == -1:
                while True:
                    self.usbcanfd.transmit_frame_FD()
                    self.usbcanfd.receive_frame_FD()
                    time.sleep(self.js_cfg['loop']['cycle_time']/1000)
            # return
            for i in range(self.js_cfg['loop']['loop_count']):
                self.usbcanfd.transmit_frame_FD()
                self.usbcanfd.receive_frame_FD()
                time.sleep(self.js_cfg['loop']['cycle_time']/1000)
        elif self.js_cfg['can_type']['can_20']:
            if self.js_cfg['loop']['loop_count'] == -1:
                while True:
                    self.usbcanfd.transmit_frame()
                    self.usbcanfd.receive_frame()
                    time.sleep(self.js_cfg['loop']['cycle_time']/1000)
            for i in range(self.js_cfg['loop']['loop_count']):
                self.usbcanfd.transmit_frame()
                self.usbcanfd.receive_frame()
                time.sleep(self.js_cfg['loop']['cycle_time']/1000)
    

    def close(self):
        self.usbcanfd.reset_CAN()
        self.usbcanfd.close_device()


if __name__ == '__main__':
    # logger = logFrame()
    # log = logger.getlogger('./test.log')
    # usbcanfd = USBCANFD()
    # usbcanfd.open_device()
    # # usbcanfd.get_deviceInfo()
    # usbcanfd.init_CAN()
    # usbcanfd.start_CAN()
    # log.info('CAN/CANFD frames number: {}'.format(usbcanfd.get_recv_num_from_buffer()))
    # # loop send CAN/CANFD frames
    # for i in range(5):
    #     usbcanfd.transmit_frame_FD()
    #     time.sleep(1)

    # usbcanfd.reset_CAN()
    # usbcanfd.close_device()

    test = USBCANFD_Controler()
    test.start()
    test.close()