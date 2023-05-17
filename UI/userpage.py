# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/demo/code/linux/UI/dv_ui/userpage.ui'
#
# Created by: PyQt5 UI code generator 5.15.8
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(917, 916)
        MainWindow.setMinimumSize(QtCore.QSize(873, 916))
        MainWindow.setMaximumSize(QtCore.QSize(99999, 916))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.txt_log = QtWidgets.QTextBrowser(self.centralwidget)
        self.txt_log.setGeometry(QtCore.QRect(10, 630, 901, 261))
        self.txt_log.setObjectName("txt_log")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(20, 60, 80, 31))
        self.label_4.setObjectName("label_4")
        self.btn_start = QtWidgets.QPushButton(self.centralwidget)
        self.btn_start.setGeometry(QtCore.QRect(20, 140, 261, 50))
        self.btn_start.setObjectName("btn_start")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(10, 600, 60, 20))
        self.label_3.setObjectName("label_3")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(30, 0, 881, 51))
        font = QtGui.QFont()
        font.setPointSize(28)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.tbw_data = QtWidgets.QTableWidget(self.centralwidget)
        self.tbw_data.setEnabled(True)
        self.tbw_data.setGeometry(QtCore.QRect(10, 230, 901, 161))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tbw_data.sizePolicy().hasHeightForWidth())
        self.tbw_data.setSizePolicy(sizePolicy)
        self.tbw_data.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbw_data.setObjectName("tbw_data")
        self.tbw_data.setColumnCount(0)
        self.tbw_data.setRowCount(0)
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(10, 200, 80, 20))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(640, 60, 80, 31))
        self.label_6.setObjectName("label_6")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(10, 51, 901, 80))
        self.frame.setFrameShape(QtWidgets.QFrame.WinPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.cb_test_name = QtWidgets.QComboBox(self.frame)
        self.cb_test_name.setGeometry(QtCore.QRect(730, 10, 161, 31))
        self.cb_test_name.setObjectName("cb_test_name")
        self.label_7 = QtWidgets.QLabel(self.frame)
        self.label_7.setGeometry(QtCore.QRect(10, 50, 171, 21))
        self.label_7.setObjectName("label_7")
        self.cb_lidar_mode = QtWidgets.QComboBox(self.frame)
        self.cb_lidar_mode.setGeometry(QtCore.QRect(190, 10, 71, 31))
        self.cb_lidar_mode.setObjectName("cb_lidar_mode")
        self.cb_lidar_mode.addItem("")
        self.cb_lidar_mode.addItem("")
        self.txt_off_counter = QtWidgets.QLineEdit(self.frame)
        self.txt_off_counter.setGeometry(QtCore.QRect(190, 50, 71, 25))
        self.txt_off_counter.setObjectName("txt_off_counter")
        self.label_8 = QtWidgets.QLabel(self.frame)
        self.label_8.setGeometry(QtCore.QRect(310, 50, 121, 21))
        self.label_8.setObjectName("label_8")
        self.txt_record_interval = QtWidgets.QLineEdit(self.frame)
        self.txt_record_interval.setGeometry(QtCore.QRect(440, 50, 71, 25))
        self.txt_record_interval.setObjectName("txt_record_interval")
        self.label_9 = QtWidgets.QLabel(self.frame)
        self.label_9.setGeometry(QtCore.QRect(630, 50, 121, 21))
        self.label_9.setObjectName("label_9")
        self.txt_timeout = QtWidgets.QLineEdit(self.frame)
        self.txt_timeout.setGeometry(QtCore.QRect(730, 50, 71, 25))
        self.txt_timeout.setObjectName("txt_timeout")
        self.cb_project = QtWidgets.QComboBox(self.frame)
        self.cb_project.setGeometry(QtCore.QRect(440, 10, 161, 31))
        self.cb_project.setObjectName("cb_project")
        self.label_10 = QtWidgets.QLabel(self.frame)
        self.label_10.setGeometry(QtCore.QRect(310, 10, 80, 31))
        self.label_10.setObjectName("label_10")
        self.btn_cancle_can = QtWidgets.QPushButton(self.centralwidget)
        self.btn_cancle_can.setGeometry(QtCore.QRect(630, 140, 271, 50))
        self.btn_cancle_can.setObjectName("btn_cancle_can")
        self.btn_stop = QtWidgets.QPushButton(self.centralwidget)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setGeometry(QtCore.QRect(310, 140, 291, 50))
        self.btn_stop.setObjectName("btn_stop")
        self.tbw_fault = QtWidgets.QTableWidget(self.centralwidget)
        self.tbw_fault.setEnabled(True)
        self.tbw_fault.setGeometry(QtCore.QRect(10, 430, 901, 161))
        self.tbw_fault.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbw_fault.setObjectName("tbw_fault")
        self.tbw_fault.setColumnCount(0)
        self.tbw_fault.setRowCount(0)
        self.label_11 = QtWidgets.QLabel(self.centralwidget)
        self.label_11.setGeometry(QtCore.QRect(10, 400, 80, 20))
        self.label_11.setObjectName("label_11")
        self.lb_schedule = QtWidgets.QLabel(self.centralwidget)
        self.lb_schedule.setGeometry(QtCore.QRect(520, 400, 101, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setItalic(False)
        font.setUnderline(False)
        font.setWeight(75)
        font.setKerning(True)
        self.lb_schedule.setFont(font)
        self.lb_schedule.setStyleSheet("color:rgb(239, 41, 41)")
        self.lb_schedule.setObjectName("lb_schedule")
        self.pgb_test = QtWidgets.QProgressBar(self.centralwidget)
        self.pgb_test.setGeometry(QtCore.QRect(630, 402, 281, 21))
        self.pgb_test.setMaximum(10000)
        self.pgb_test.setProperty("value", 0)
        self.pgb_test.setTextVisible(True)
        self.pgb_test.setInvertedAppearance(False)
        self.pgb_test.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.pgb_test.setObjectName("pgb_test")
        self.frame.raise_()
        self.txt_log.raise_()
        self.label_4.raise_()
        self.btn_start.raise_()
        self.label_3.raise_()
        self.label_2.raise_()
        self.tbw_data.raise_()
        self.label_5.raise_()
        self.label_6.raise_()
        self.btn_cancle_can.raise_()
        self.btn_stop.raise_()
        self.tbw_fault.raise_()
        self.label_11.raise_()
        self.lb_schedule.raise_()
        self.pgb_test.raise_()
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_record_start = QtWidgets.QAction(MainWindow)
        self.action_record_start.setObjectName("action_record_start")
        self.action_replay_start = QtWidgets.QAction(MainWindow)
        self.action_replay_start.setObjectName("action_replay_start")

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "DV Test"))
        self.label_4.setText(_translate("MainWindow", "Lidar mode"))
        self.btn_start.setText(_translate("MainWindow", "Test Start"))
        self.label_3.setText(_translate("MainWindow", "Log:"))
        self.label_2.setText(_translate("MainWindow", "Innovusion DV Test Tool"))
        self.label_5.setText(_translate("MainWindow", "Lidar status"))
        self.label_6.setText(_translate("MainWindow", "Test Name"))
        self.label_7.setText(_translate("MainWindow", "Power_off_data_number"))
        self.cb_lidar_mode.setItemText(0, _translate("MainWindow", "Power"))
        self.cb_lidar_mode.setItemText(1, _translate("MainWindow", "CAN"))
        self.txt_off_counter.setText(_translate("MainWindow", "10"))
        self.label_8.setText(_translate("MainWindow", "Record Interval(s)"))
        self.txt_record_interval.setText(_translate("MainWindow", "5"))
        self.label_9.setText(_translate("MainWindow", "Timeout(s)"))
        self.txt_timeout.setText(_translate("MainWindow", "5"))
        self.label_10.setText(_translate("MainWindow", "Project"))
        self.btn_cancle_can.setText(_translate("MainWindow", "Cancle CAN Mode"))
        self.btn_stop.setText(_translate("MainWindow", "Test Stop"))
        self.label_11.setText(_translate("MainWindow", "Lidar Fault"))
        self.lb_schedule.setText(_translate("MainWindow", "Test Schedule"))
        self.pgb_test.setFormat(_translate("MainWindow", "%p%"))
        self.action_record_start.setText(_translate("MainWindow", "start"))
        self.action_record_start.setIconText(_translate("MainWindow", "record"))
        self.action_replay_start.setText(_translate("MainWindow", "start"))
        self.action_replay_start.setIconText(_translate("MainWindow", "replay"))
