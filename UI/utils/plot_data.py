
from PyQt5.QtCore import Qt, QTimer
import sys
import time
import math
import inspect
import traceback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import numpy as np
import os
from utils import *

widget_height=130
widget_width=490


def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            sig = inspect.signature(func)
            num_args = len(sig.parameters)
            if num_args == len(args):
                result = func(*args)
            else:
                instance = args[0]
                result = func(instance, **kwargs)
            return result
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error occurred while executing {func.__name__}: {e}")
            return None
    return wrapper

class Current_monitor(QThread):
    sigout_plot_data = pyqtSignal(list,str)
    
    @handle_exceptions
    def __init__(self,ip_list,relay_unit,relay_channels,sleep_time,save_foler,timeout):
        super(Current_monitor,self).__init__()
        self.ip_list = ip_list
        self.relay_unit = relay_unit
        self.relay_channels = relay_channels
        self.sleep_time = sleep_time
        self.save_foler = os.path.join(save_foler,"current")
        self.timeout = timeout
        self.plot_length = 100
        self.command_start = ":STARt"
        self.command_stop = ":STOP"
        if not os.path.exists(self.save_foler):
            os.makedirs(self.save_foler)
        self.save_dict = {}
        self.plot_data_dict = {}
        for ip in ip_list:
            self.plot_data_dict[ip] = []
            self.save_dict[ip] = os.path.join(self.save_foler,f"{ip}.csv")
            if not os.path.exists(self.save_dict[ip]):
                csv_write(self.save_dict[ip],["time","current(mA)"])
                
    @handle_exceptions
    def change_record_status(self, status = "start", sleep_time = 1):
        for _ in range(2):
            if status == "start":
                send_tcp(self.command_start,"192.168.1.2",8802,wait=True,wait_time=1)
            else:
                send_tcp(self.command_stop,"192.168.1.2",8802,wait=True,wait_time=1)
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    
    @handle_exceptions
    def change_relay_range(self,resistor,resistor_threshold=10): 
        self.change_record_status("stop")
        voltage_range = "20.0E-03" if resistor < resistor_threshold else "20.0E+00"
        print(f"start set voltage range to {voltage_range}V")
        for ch in self.relay_channels:
            if self.isInterruptionRequested():
                return
            command = f":UNIT:RANGe CH{self.relay_unit}_{ch},{voltage_range}"
            send_tcp(command,"192.168.1.2",8802,wait=True,wait_time=0.3)
        self.change_record_status("start")
        for ch in self.relay_channels:
            query_command = f":UNIT:RANGe? CH{self.relay_unit}_{ch}"
            query_res = send_tcp(query_command,"192.168.1.2",8802,wait=True,wait_time=0.3)
            if voltage_range not in query_res:
                print(f"set CH{self.relay_unit}_{ch} voltage range to {voltage_range}V failed, res: {query_res}")
            else:
                print(f"set CH{self.relay_unit}_{ch} voltage range to {voltage_range}V success")
    
    
    @handle_exceptions
    def run(self): #using tcp command
        last_resistor = 0
        resistor_threshold = 10 #distinct voltage unit(V/mV)
        self.change_record_status("start")
        voltage_command = f":MEMory:TAREAL? UNIT{self.relay_unit}"
        if len(self.ip_list) != len(self.relay_channels):
            print("ip_list and relay_channels length not match,please check the config file")
            return
        print("set relay status to display")
        for ch in range(1,16):
            if ch in self.relay_channels:
                disp_status = "ON"
            else:
                disp_status = "OFF"
            command = f":UNIT:STORe CH{self.relay_unit}_{ch},{disp_status}"
            send_tcp(command,"192.168.1.2",8802,wait=True,wait_time=0.3)
        while True:
            t = time.time()
            if os.getenv("resistor"):
                resistor = float(os.getenv("resistor"))
            else:
                resistor = 0.1
            if last_resistor != resistor:
                self.change_relay_range(resistor,resistor_threshold)
            last_resistor = resistor
            if self.isInterruptionRequested():
                return
            vol_str = send_tcp(voltage_command,"192.168.1.2",8802,wait=True,wait_time=0.3)
            res = re.findall("(-?\d+\.?\d*)",vol_str)
            date_time = f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}"
            if len(res) >= len(self.ip_list):
                for idx,ip in enumerate(self.ip_list):
                    voltage = float(res[idx])
                    voltage /= 1000
                    if resistor >= resistor_threshold:
                        voltage *= 1000
                    current = voltage/resistor
                    self.plot_data_dict[ip].append(current)
                    csv_write(self.save_dict[ip],[date_time,current])
                    if len(self.plot_data_dict[ip]) > self.plot_length:
                        self.plot_data_dict[ip] = self.plot_data_dict[ip][-self.plot_length:]
                    self.sigout_plot_data.emit(self.plot_data_dict[ip],ip)
            else:
                print(f"current monitor data error: return length {len(res)}")
            sleep_time = self.sleep_time - (time.time() - t)
            if sleep_time > 0:
                time.sleep(sleep_time)          
                

    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"try finish monitor current")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        self.change_record_status("stop",0)
        print(f"current thread finish success")



class Plot_Widget(QWidget):
    @handle_exceptions
    def __init__(self, parent=None,name="PPS"):
        super().__init__(parent)
        self.data = []  # 存储待绘制的数据
        self.title=name
        self.resize(widget_width, widget_height)
        self.title_height = 12
        self.point_width = 10
        self.font_heigth = 10  #最大值和最小值高度
        self.space_heigth = 15 #绘图空白区域预留高度 
        self.label_width = 60  #label的文字宽度
        self.max_value_space = 4 #title高度补偿
        
    @handle_exceptions
    def paintEvent(self, event):
        super().paintEvent(event)
        
        
        painter = QPainter(self)
        font = QFont()
        font.setPointSize(self.title_height)
        font.setBold(True)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.width(self.title)
        text_height = font_metrics.height()
        text_x = math.floor((self.width() - text_width) / 2)
        text_y = math.floor((text_height))
        painter.drawText(text_x, text_y, self.title)
        pen = QPen(QColor(255, 0, 0))  # 设置画笔颜色为红色
        font = QFont()
        font.setPointSize(10)  # 设置字体大小
        self.data=np.array(self.data)
        max_data_shape=math.floor((self.width()-self.label_width)/self.point_width)
        if self.data.shape[0] > 1:
            if self.data.shape[0]>max_data_shape:
                self.data=self.data[-max_data_shape:]
            painter.setFont(font)
            painter.drawText(self.font_heigth, self.height() - self.space_heigth, str(round(self.data.min(),2)))
            painter.drawText(self.font_heigth, font.pointSize() + self.space_heigth, str(round(self.data.max(),2)))
            painter.setPen(pen)
            self.convert_data()
            for i in range(self.data.shape[0]-1):
                x1 = int(i * self.point_width + self.label_width)
                y1 = int(self.data[i])
                x2 = int((i + 1) * self.point_width + self.label_width)
                y2 = int(self.data[i + 1])
                painter.drawLine(x1, y1, x2, y2)  # 绘制连线
        painter.end()
                
    def updateData(self, new_data):
        self.data = new_data
        self.update()  # 触发paintEvent重新绘制
        
        
    def convert_data(self): 
        #将data数据转换到坐标轴位置,坐标轴最顶部为0,最底部为self.height()
        #顶部预留tiltle的高度,底部预留self.space_heigth
        #映射关系为线性 [1,1000]->[self.height()-self.space_heigth,self.title_height],并取整'''
        plot_height = (self.height() - self.space_heigth) - (self.title_height + self.max_value_space)
        ptp = np.ptp(self.data)
        if ptp == 0:
            self.data = np.zeros(self.data.shape[0]) + self.height()-self.space_heigth
        else:
            data_temp = np.floor((self.data-self.data.min())*plot_height/ptp)
            self.data = self.height() - self.space_heigth - data_temp
            
            
if __name__ == "__main__":
    qwidget=QtWidgets.QWidget(self.scrollAreaWidgetContents_2)
    qwidget.setGeometry(QtCore.QRect(10, widget_height*idx, widget_width-30, widget_height))
    a = Plot_Widget(qwidget,"")
    a.updateData(list1)