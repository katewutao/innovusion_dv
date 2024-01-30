# /**
#  * @author katewutao
#  * @email [kate.wu@cn.innovuison.com]
#  * @create date 2023-05-05 10:12:54
#  * @modify date 2023-10-20 13:30:48
#  * @desc [description]
#  */
import os
import sys
import time
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QObject
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import userpage
import subprocess
import re,threading
import platform
import datetime
import traceback
import inspect
import pandas as pd
import requests
import shutil,json,importlib
import math
from threading import Thread
import sys
import builtins
from utils import *

 
builtins.print_origin=print
def rewrite_print(log_path):
    if not os.path.exists(os.path.dirname(log_path)):
        os.makedirs(os.path.dirname(log_path))
    def print_res(*args, **kwargs):
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        msg = ' '.join(map(str, args))  # Convert all arguments to strings and join them with spaces
        builtins.print_origin(f"[{current_date}] {msg}", **kwargs)
        builtins.print_origin(f"[{current_date}] {msg}", **kwargs, file=open(log_path, "a"))
    return print_res
 
 

def time_limited(timeout):
    def decorator(function):
        def decorator2(*args, **kwargs):
            class TimeLimited(Thread):
                def __init__(self, _error=None, ):
                    Thread.__init__(self)
                    self.error = _error
                    self.result = None

                def run(self):
                    try:
                        self.result = function(*args, **kwargs)
                    except Exception as e:
                        self.error = e
            t = TimeLimited()
            t.setDaemon(True)
            t.start()
            t.join(timeout)
            if t.error:
                raise t.error
            if t.is_alive():
                # print(f"{function.__name__} time out")
                pass
            return t.result
        return decorator2
    return decorator

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
    

def get_circle_time(dict_config):
    times=[]
    if isinstance(dict_config,dict):
        for key in dict_config.keys():
            temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*):?(\d+\.?\d*)?",key)
            for i in range(len(temp_times)):
                temp_times[i]=list(temp_times[i])
                for j in range(len(temp_times[i])):
                    if j!=2:
                        temp_times[i][j]=float(temp_times[i][j])*60
                    else:
                        if temp_times[i][j]!="":
                            temp_times[i][j]=float(temp_times[i][j])
                        else:
                            temp_times[i][j]=14
            times+=temp_times*dict_config[key]
    elif isinstance(dict_config,str):
        dict_config=dict_config.split("\n")
        for one_line in dict_config:
            temp_times=re.findall("(\d+\.?\d*):(\d+\.?\d*):?(\d+\.?\d*)?",one_line)
            temp_circle=re.search('''(".+"|'.+').*?(\d+)''',one_line)
            if len(temp_times)>0 and temp_circle:
                circle = int(temp_circle.group(2))
                for i in range(len(temp_times)):
                    temp_times[i]=list(temp_times[i])
                    for j in range(len(temp_times[i])):
                        if j!=2:
                            temp_times[i][j]=float(temp_times[i][j])*60
                        else:
                            if temp_times[i][j]!="":
                                temp_times[i][j]=float(temp_times[i][j])
                            else:
                                temp_times[i][j]=14
                times+=temp_times*circle        
    return times
            
def get_tags():
    cmd = subprocess.Popen("git describe --tags", shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    time.sleep(0.8)
    if not cmd.poll():
        res = cmd.stdout.read()
        if "fatal" not in res:
            return res.strip("\n")
    tags_folder = "./.git/refs/tags"
    if not os.path.exists(tags_folder):
        return ""
    tags = os.listdir(tags_folder)
    if len(tags) == 0:
        return ""
    modify_time = [[tag, os.path.getmtime(
        os.path.join(tags_folder, tag))] for tag in tags]
    modify_time = sorted(modify_time, key=lambda x: x[1], reverse=True)
    tag = modify_time[0][0]
    if not os.path.exists(os.path.join(tags_folder, tag)):
        return ""
    with open(os.path.join(tags_folder, tag), "r") as f:
        tag_content = f.read()
    head_folder = "./.git/HEAD"
    if not os.path.exists(head_folder):
        return ""
    with open(head_folder, "r") as f:
        head_content = f.read()
    ret = re.search("ref:\s?(.+)$", head_content)
    if not ret:
        return tag
    else:
        with open(os.path.join("./.git", ret.group(1)), "r") as f:
            branch_content = f.read()
        if branch_content == tag_content:
            return tag
    return f"{tag}-g{branch_content[:7]}"
            

def get_time():
    times_now=time.strftime('%Y.%m.%d %H:%M:%S ',time.localtime(time.time()))
    res=times_now.strip().replace(':', '_').replace('.', '_').replace(' ', '_')
    return res




class TestMain(QThread):
    sigout_test_finish = pyqtSignal(str)
    sigout_lidar_info=pyqtSignal(list,int)
    sigout_schedule=pyqtSignal(int,int)
    sigout_set_fault=pyqtSignal(str,int)
    sigout_heal_fault=pyqtSignal(str,int)
    sigout_power=pyqtSignal(bool)
    
    
    def __init__(self,can_mode,ip_list,record_folder,record_header,times,csv_write_func,record_func,txt_record_interval,txt_off_counter,txt_timeout,cb_lidar_mode):
        super(TestMain,self).__init__()
        self.csv_write_func=csv_write_func
        self.txt_record_interval=txt_record_interval
        self.cb_lidar_mode=cb_lidar_mode
        self.save_folder=record_folder
        self.ip_list=ip_list
        self.txt_timeout=txt_timeout
        self.record_header=record_header
        self.txt_off_counter=txt_off_counter
        self.times=times
        self.record_func=record_func
        self.can_mode=can_mode
    
    def send_lidar_info(self,list1,row_idx):
        self.sigout_lidar_info.emit(list1,row_idx)
    
    def set_fault(self,fault,row_idx):
        self.sigout_set_fault.emit(fault,row_idx)
    
    def heal_fault(self,fault,row_idx):
        self.sigout_heal_fault.emit(fault,row_idx)
    
    @handle_exceptions
    def one_cycle(self,power_one_time,ip_list,i,data_num_power_off,log_path):
        self.sigout_power.emit(True)
        import power
        print(f"current circle {i}")
        t=time.time()
        last_timestamp=time.time()
        while True:
            try:
                print(f"start set voltage")
                pow=power.Power()
                print(f"init power")
                pow.power_on()
                print(f"power on")
                pow.set_voltage(power_one_time[2])
                print(f"set {power_one_time[2]}V")
                voltage=pow.PowerStatus()[0]
                print(f"voltage is {voltage}")
                if abs(voltage-power_one_time[2])<0.3:
                    break
            except:
                current_timestamp=time.time()
                if current_timestamp-last_timestamp>3:
                    last_timestamp=current_timestamp
                    print(f"set power voltage failed, {power_one_time[2]}V")
                time.sleep(2)
        sleep_time = int(power_one_time[0]-time.time()+t)
        print(f"start monitor {sleep_time}s")
        self.records=[]
        self.monitors=[]
        self.dsps=[]
        if sleep_time>2:
            sleep_time = power_one_time[0]-time.time()+t
            if sleep_time > 0:
                time.sleep(sleep_time)
        self.sigout_power.emit(False)
        while True:
            try:
                pow=power.Power()
                pow.power_off()
                break
            except:
                print(f"power off failed")
                time.sleep(2)
        print(f"start sleep {int(power_one_time[0]+power_one_time[1]-(time.time()-t))}s")
        t0=(power_one_time[0]+power_one_time[1]-(time.time()-t))
        if t0>0:
            time.sleep(t0)

    @handle_exceptions
    def run(self):
        i=1
        for time_one in self.times:
            self.sigout_schedule.emit(i,len(self.times))
            self.one_cycle(time_one,self.ip_list,i,int(self.txt_off_counter.text()),self.save_folder)
            i+=1 
        self.sigout_test_finish.emit(None)
        
    
    @handle_exceptions
    def stop(self):
        t=time.time()
        while self.isRunning():
            print(f"try finish test")
            self.requestInterruption()
            self.wait(1000)
            if time.time()-t>3:
                self.terminate()
                break
        self.sigout_test_finish.emit(None)
        print(f"Test has been stop")

class EmittingStream(QtCore.QObject):
    textWritten = QtCore.pyqtSignal(str)
    def write(self, text):
        self.textWritten.emit(str(text))

        
class MainCode(QMainWindow,userpage.Ui_MainWindow):
    
    def __init__(self):
        QMainWindow.__init__(self)
        userpage.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.log_rows = 0
        self.lb_version.setText(f"Version:  {get_tags()}")
        
        self.project_folder="./project"
        self.test_folder="./test_config"
        self.power_folder="./power"
        self.logo_path = "config/Seyond Black Horizontal RGB.jpg"
        
        self.timer = QTimer()
        
        self.cb_project.currentIndexChanged.connect(self.project_changed)
        self.cb_test_name.currentIndexChanged.connect(self.test_name_changed)
        self.cb_power_type.currentIndexChanged.connect(self.power_changed)
        self.cb_lidar_mode.currentIndexChanged.connect(self.lidar_mode_changed)
        self.btn_start.clicked.connect(self.test_main)
        self.btn_stop.clicked.connect(self.test_stop)
        self.init_select_item()
        
        self.cb_lidar_mode.setEnabled(False)
        self.cb_can_mode.setEnabled(False)
        self.lb_logo.setPixmap(QPixmap(self.logo_path))
        
        IntValidator = QIntValidator(0,100000)
        DoubleValidator = QDoubleValidator(0,100000,3,notation=QtGui.QDoubleValidator.StandardNotation)
        self.txt_timeout.setValidator(DoubleValidator)
        self.txt_record_interval.setValidator(DoubleValidator)
        self.txt_off_counter.setValidator(IntValidator)
        
        self.scrollArea_list=[]      
    
        sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
        sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)

    def write(self, info):
        self.txt_log.insertPlainText(info)
        if len(info):
            self.txt_log.setText(info)
            QtWidgets.qApp.processEvents(
                QtCore.QEventLoop.ExcludeUserInputEvents | QtCore.QEventLoop.ExcludeSocketNotifiers)
            self.stdoutbak.write(info)

    def normalOutputWritten(self, text):
        if self.log_rows>50000:
            self.txt_log.clear()
            self.log_rows=0
        self.txt_log.append(text.strip('\n'))
        self.cursor=self.txt_log.textCursor()
        self.txt_log.moveCursor(self.cursor.End) 
        QtWidgets.QApplication.processEvents()
        self.log_rows+=1
    
    
    @handle_exceptions
    def update_test_time(self):
        time_s=TimeConvert.hms2time(self.lb_test_time.text())
        time_s+=1
        hms=TimeConvert.time2hms(time_s)
        self.lb_test_time.setText(hms)
    
    
    @handle_exceptions
    def init_table(self,row_counter,columns):
        columns=["Lidar_IP"]+list(columns)
        for row_num in range(self.tbw_data.rowCount(),-1,-1):
            self.tbw_data.removeRow(row_num)
        for row_num in range(self.tbw_fault.rowCount(),-1,-1):
            self.tbw_fault.removeRow(row_num)
        self.tbw_data.setColumnCount(len(columns))
        self.tbw_fault.setColumnCount(1)
        for j in range(len(columns)):
            self.tbw_data.setHorizontalHeaderItem(j, QtWidgets.QTableWidgetItem())
            self.tbw_data.horizontalHeader().setSectionResizeMode(j, QHeaderView.ResizeToContents)
            item = self.tbw_data.horizontalHeaderItem(j)
            item.setText(f"{columns[j]}")
        
        self.tbw_fault.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem())
        self.tbw_fault.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        item = self.tbw_fault.horizontalHeaderItem(0)
        item.setText("Lidar_IP")
        
        
        for i in range(row_counter):
            self.tbw_data.insertRow(i)
            self.tbw_fault.insertRow(i)
            self.tbw_data.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_fault.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.tbw_fault.setItem(i,0,QtWidgets.QTableWidgetItem(self.ip_list[i]))
            for j in range(len(columns)):
                if j==0:
                    cell_value=self.ip_list[i]
                else:
                    cell_value=""
                self.tbw_data.setItem(i,j,QtWidgets.QTableWidgetItem(cell_value))
        
    
    @handle_exceptions
    def report_fault(self,fault,row_idx):
        self.set_fault(fault,row_idx)
        for col_idx in range(self.tbw_fault.columnCount()):
            if  self.tbw_fault.horizontalHeaderItem(col_idx).text()==fault:
                if self.tbw_fault.item(row_idx,col_idx)!=None:
                    last_fault_count=self.tbw_fault.item(row_idx,col_idx).text()
                    if re.search("\d+",last_fault_count):
                        self.tbw_fault.setItem(row_idx,col_idx,QtWidgets.QTableWidgetItem(f"{int(last_fault_count)+1}"))
                        
                        return
                self.tbw_fault.setItem(row_idx,col_idx,QtWidgets.QTableWidgetItem(f"{1}"))
                return
        last_max_col=self.tbw_fault.columnCount()
        self.tbw_fault.setColumnCount(last_max_col+1)
        self.tbw_fault.setHorizontalHeaderItem(last_max_col, QtWidgets.QTableWidgetItem())
        self.tbw_fault.horizontalHeader().setSectionResizeMode(last_max_col, QHeaderView.ResizeToContents)
        item = self.tbw_fault.horizontalHeaderItem(last_max_col)
        item.setText(f"{fault}")
        self.tbw_fault.setItem(row_idx,last_max_col,QtWidgets.QTableWidgetItem(f"{1}"))
        
    @handle_exceptions
    def set_fault(self,fault,row_idx):
        fault_name_width=185
        if fault not in self.scrollArea_list:
            self.scrollArea_list.append(fault)
            self.scrollArea.takeWidget()
            self.scrollAreaWidgetContents.setMinimumSize(fault_name_width+19+40*len(self.ip_list),20+30*len(self.scrollArea_list))
            label=QtWidgets.QLabel(self.scrollAreaWidgetContents)
            label.setGeometry(QtCore.QRect(10,30*len(self.scrollArea_list)-10,fault_name_width,21))
            label.setText(fault)
            setattr(self,f"lb_{fault}",label)            
            for idx,ip in enumerate(self.ip_list):
                label=QtWidgets.QLabel(self.scrollAreaWidgetContents)
                label.setGeometry(QtCore.QRect(fault_name_width+19+40*idx, 30*len(self.scrollArea_list)-10, 21, 21))
                label.setText("")
                label.setStyleSheet("border-radius:10px;background-color:rgb(0, 0, 0)")
                setattr(self,f"lb_{fault}_{idx}",label)
            self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        getattr(self,f"lb_{fault}_{row_idx}").setStyleSheet("border-radius:10px;background-color:rgb(255, 0, 0)")

    @handle_exceptions
    def heal_fault(self,fault,row_idx):
        if fault in self.scrollArea_list:
            getattr(self,f"lb_{fault}_{row_idx}").setStyleSheet("border-radius:10px;background-color:rgb(115, 210, 22)")
    
    def init_select_item(self):
        self.cb_project.clear()
        self.cb_test_name.clear()
        for project in sorted(os.listdir(self.project_folder)):
            ret=re.search("^(.+)\.py",project)
            if ret:
                self.cb_project.addItem(ret.group(1))
        for test_name in sorted(os.listdir(self.test_folder)):  # may can be json file, but no explain
            ret=re.search("^(.+)\.py",test_name)
            if ret:
                self.cb_test_name.addItem(ret.group(1))
        for power_type in sorted(os.listdir(self.power_folder)):
            ret=re.search("^power_(.+)\.py$",power_type)
            if ret:
                self.cb_power_type.addItem(ret.group(1))
    
    @handle_exceptions
    def power_changed(self):
        print(f"current power is {self.cb_power_type.currentText()},please ensure has connect!")
        os.environ["power_type"]=self.cb_power_type.currentText()
        if os.path.exists("power.py"):
            os.remove("power.py")
        shutil.copyfile(os.path.join(self.power_folder,f"power_{self.cb_power_type.currentText()}.py"),os.path.join(os.getcwd(),"power.py"))
    
    def lidar_mode_changed(self):
        if self.cb_lidar_mode.currentText()=="No Power":
            self.cb_power_type.setEnabled(False)
        else:
            self.cb_power_type.setEnabled(True)
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cb_can_mode.setEnabled(True)
        else:
            self.cb_can_mode.setEnabled(False)
        os.environ["lidar_mode"]=self.cb_lidar_mode.currentText()
            
    
    def power_status(self,mode):
        if mode:
            self.lb_power_status.setStyleSheet("border-radius:10px;background-color:rgb(115, 210, 22)")
        else:
            self.lb_power_status.setStyleSheet("border-radius:10px;background-color:rgb(255, 0, 0)")
    
    @handle_exceptions
    def test_name_changed(self):
        if self.cb_test_name.currentText().strip()!="":
            os.environ["test_name"]=self.cb_test_name.currentText()
            mata_class=importlib.import_module(f"{self.test_folder.strip('.').strip('/')}.{self.cb_test_name.currentText()}")
            self.test_config=mata_class.config
            self.save_folder=self.cb_test_name.currentText()
            self.read_config()
    
    def project_changed(self):
        if self.cb_project.currentText().strip()!="":
            os.environ["project"]=self.cb_project.currentText()
            mata_class=importlib.import_module(f"{self.project_folder.strip('.').strip('/')}.{self.cb_project.currentText()}")
            self.record_header=mata_class.record_header
            self.csv_write_func=mata_class.csv_write
            self.record_func=mata_class.one_record
            self.read_config()

    def read_config(self):
        if hasattr(self,"test_config"):
            self.ip_list=self.test_config["lidar_ip"]
            self.times=get_circle_time(self.test_config["time_dict"])
            self.init_table(len(self.ip_list),self.record_header.split(","))
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 485, 795))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea_list=[]
    
    @handle_exceptions
    def test_main(self):
        if self.txt_off_counter.text().strip()=="":  #setReadOnly(True)
            print(f"please input power off empty data number")
            return        
        if self.txt_record_interval.text().strip()=="":  #setReadOnly(True)
            print(f"please input record interval time")
            return
        if self.txt_timeout.text().strip()=="":  #setReadOnly(True)
            print(f"please input timeout")
            return
        self.btn_start.setEnabled(False)
        self.pgb_test.setValue(0)
        self.lb_test_time.setText("00:00:00")
        self.timer.start(1000)
        self.timer.timeout.connect(self.update_test_time)
        print(f"{self.lb_version.text()},Laser test,Lidar mode:{self.cb_lidar_mode.currentText()}, Powers:{self.cb_power_type.currentText()}, Project:{self.cb_project.currentText()},Test name:{self.cb_test_name.currentText()},CAN mode:{self.cb_can_mode.currentText()},Off counter:{self.txt_off_counter.text()},Interval:{self.txt_record_interval.text()}s,Relay:{self.relay.isChecked()},DSP:{self.dsp.isChecked()},Timeout:{self.txt_timeout.text()}s")
        os.environ["relay"]=str(self.relay.isChecked())
        os.environ["dsp"]=str(self.dsp.isChecked())
        self.test=TestMain(self.cb_can_mode.currentText(),self.ip_list,self.save_folder,self.record_header,self.times,self.csv_write_func,self.record_func,self.txt_record_interval,self.txt_off_counter,self.txt_timeout,self.cb_lidar_mode)
        self.test.sigout_test_finish.connect(self.test_finish)
        self.test.sigout_schedule.connect(self.set_schedule)
        self.test.sigout_power.connect(self.power_status)
        self.test.start()
        self.test_set_off()
    
    @handle_exceptions
    def test_finish(self,util_path):
        if hasattr(self,"timer"):
            self.timer.stop()
            try:
                self.timer.timeout.disconnect(self.update_test_time)
            except:
                pass
        self.test_set_on()
        print(f"Test finished")
    
    def test_set_off(self):
        self.cb_lidar_mode.setEnabled(False)
        self.cb_project.setEnabled(False)
        self.cb_test_name.setEnabled(False)
        self.cb_power_type.setEnabled(False)
        self.cb_can_mode.setEnabled(False)
        self.txt_off_counter.setEnabled(False)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(False)
        self.txt_timeout.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_cancle_can.setEnabled(False)
        self.relay.setEnabled(False)
        self.dsp.setEnabled(False)
        self.btn_stop.setEnabled(True)
    
    def test_set_on(self):
        self.cb_lidar_mode.setEnabled(False)
        self.cb_project.setEnabled(True)
        self.cb_test_name.setEnabled(True)
        if self.cb_lidar_mode.currentText()!="No Power":
            self.cb_power_type.setEnabled(True)
        if self.cb_lidar_mode.currentText()=="CAN":
            self.cb_can_mode.setEnabled(True)
        self.txt_off_counter.setEnabled(True)  #setReadOnly(True)
        self.txt_record_interval.setEnabled(True)
        self.txt_timeout.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_cancle_can.setEnabled(True)
        self.relay.setEnabled(True)
        self.dsp.setEnabled(True)
        self.btn_stop.setEnabled(False)
    
    @handle_exceptions
    def set_schedule(self,current_counter,sum_counter):
        str1=f"{round(current_counter*100/sum_counter,1)}%"
        # self.lb_schedule.setText(f"Test Schedule: {str1}")
        self.pgb_test.setValue(math.floor(current_counter*10000/sum_counter))
        self.pgb_test.setFormat(str1)
    
    @handle_exceptions
    def test_stop(self):
        self.btn_stop.setEnabled(False)
        if hasattr(self,"test"):
            self.test.stop()
        if hasattr(self,"timer"):
            self.timer.stop()
            try:
                self.timer.timeout.disconnect(self.update_test_time)
            except:
                pass
        self.test_set_on()
    
        
    
        
if __name__ == '__main__':
    log_folder="./python_log"
    log_file=os.path.join(log_folder,get_current_date()+".log")
    builtins.print=rewrite_print(log_file)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QGuiApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    window = MainCode()
    window.show()
    sys.exit(app.exec_())
