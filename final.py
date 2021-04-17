from GUI_interface import *
from ok_dialog import Ui_Dialog as Form
# from ok_dialog import warning_Dialog_ch1 as warn_ch1
# from ok_dialog import warning_Dialog_ch2 as warn_ch2

import sys
import subprocess
import threading
from PyQt5 import QtCore, QtWidgets
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import pyqtgraph.graphicsItems.PlotItem
from pyqtgraph import PlotData
import RPi.GPIO as GPIO

try:
    from StringIO import StringIO  ## for Python 2
except ImportError:
    from io import StringIO  ## for Python 3
import time
import csv
from datetime import datetime

GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

sample_count = 5000
channels = '0'
batch_size = '50'

stylesheet = """
    QMainWindow {
        background-image: url("rasp1.jpg") stretch  stretch; 
        background-repeat: no-repeat; 
        background-position: center;
    }
"""


class WorkerTread(QtCore.QThread):
    update_output = QtCore.pyqtSignal(list)

    def run(self):
        global sample_count, channels, batch_size

        while (True):
            self.p = QtCore.QProcess()
            self.p.start("mcp3008hwspi -c {} -f 0 -n {}  -b {}".format(channels, str(sample_count), batch_size))
            self.p.waitForFinished()
            out = bytes(self.p.readAllStandardOutput())
            out = out.decode('utf-8')
            out_final = []
            out_final.append(float(out.split()[9]))  # sample rate
            data = np.genfromtxt(StringIO(out), skip_header=1, delimiter=',', names=True)
            try:
                if channels == '01':
                    out_final.append((1 / 1024) * data['value_ch0'])  # ych1
                    out_final.append(((1 / 1024) * data['value_ch1']))  # ych2
                    out_final.append((1 / out_final[0]) * np.arange(int(sample_count)))  # xdata
                    self.update_output.emit(out_final)
                elif channels == '0':
                    out_final.append((1 / 1024) * data['value_ch0'])  # ych1
                    out_final.append((1 / out_final[0]) * np.arange(int(sample_count)))  # xdata
                    self.update_output.emit(out_final)
                elif channels == '1':
                    out_final.append(((1 / 1024) * data['value_ch1']))  # ych2
                    out_final.append((1 / out_final[0]) * np.arange(int(sample_count)))  # xdata
                    self.update_output.emit(out_final)
            except:
                pass


class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    global channels, channels, batch_size, sample_count

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.init_qt()
        self.init_variables()
        self.init_button_actions()
        self.offset_func()
        self.volt_div_func()
        self.time_div_func()
        self.bias = 2.425
        self.graphicsView.setYRange(self.min_voltage, self.max_voltage)
        self.graphicsView.setXRange(self.ax_min, self.ax_max)
        self.worker = WorkerTread()
        self.worker.start()
        self.worker.update_output.connect(self.update_data1)

    def gain_func(self, channel):
        channelA = [GPIO.input(x) for x in self.channel_A_list]
        channelB = [GPIO.input(x) for x in self.channel_B_list]
        suma = np.sum(channelA)
        sumb = np.sum(channelB)

        while suma > 1:
            channelA = [GPIO.input(x) for x in self.channel_A_list]
            suma = np.sum(channelA)
            self.gain_message1.setText("multiple gain button pressed in CH1")
        self.gain_message1.setText("")
        if suma == 0:
            self.gain_message1.setText("None gain button pressed in CH1")
        else:
            self.gain_message1.setText("")
        if channelA[0] == 1:
            self.gain_ch1 = 2.2 / 10
        elif channelA[1] == 1:
            self.gain_ch1 = 4.7 / 10
        elif channelA[2] == 1:
            self.gain_ch1 = 10 / 10
        elif channelA[3] == 1:
            self.gain_ch1 = 47 / 10
        elif channelA[4] == 1:
            self.gain_ch1 = 100 / 10
        while sumb > 1:
            channelB = [GPIO.input(x) for x in self.channel_B_list]
            sumb = np.sum(channelB)
            self.gain_message2.setText("multiple gain button pressed in CH2")
        self.gain_message2.setText("")
        if sumb == 0:
            self.gain_message2.setText("None gain button pressed in CH2")
        else:
            self.gain_message2.setText("")
        if channelB[0] == 1:
            self.gain_ch2 = 2.2 / 10
        elif channelB[1] == 1:
            self.gain_ch2 = 4.7 / 10
        elif channelB[2] == 1:
            self.gain_ch2 = 10 / 10
        elif channelB[3] == 1:
            self.gain_ch2 = 47 / 10
        elif channelB[4] == 1:
            self.gain_ch2 = 100 / 10

    def update_data1(self, val):
        global sample_count, channels, batch_size
        if self.keep_runnig == True:
            try:
                if channels == '012':
                    self.sample_rate = val[0]
                    self.ych1.append(val[1] * self.vref)
                    self.ych2.append(val[2] * self.vref)
                    self.ych3.append(val[3] * self.vref)
                    self.xdata.append(val[4])
                elif channels == '01':
                    self.sample_rate = val[0]
                    self.ych1.append(val[1] * self.vref)
                    self.ych2.append(val[2] * self.vref)
                    self.xdata.append(val[3])
                elif channels == '0':
                    self.sample_rate = val[0]
                    self.ych1.append(val[1] * self.vref)
                    self.xdata.append(val[2])
                elif channels == '1':
                    self.sample_rate = val[0]
                    self.ych2.append(val[1] * self.vref)
                    self.xdata.append(val[2])
                self.update_plot()
            except:
                pass

    def datalogging(self):
        if self.datalog == False:

            text, ok = QtWidgets.QInputDialog.getText(self, 'File name', 'Type file name?')
            file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
            if ok and text != '':
                self.file_location = file + "/" + str(text)
                self.datalog = True
                self.recording_message.setText("\nRecording")

            else:
                self.recording_message.setText("\nFile name or location Error\nReady to record")

        else:
            self.datalog = False
            self.recording_message.setText("\nSaving to file")

            time.sleep(0.5)
            if len(self.ych1_log) > 0:
                with open(self.file_location + '_ych1' + '.csv', mode='w') as ych1:
                    wr = csv.writer(ych1)
                    for i in self.ych1_log:
                        wr.writerow(i)
                with open(self.file_location + '_xch1' + '.csv', mode='w') as xch1:
                    wr = csv.writer(xch1)
                    for i in self.xdata1_log:
                        wr.writerow(i)

            if len(self.ych2_log) > 0:
                with open(self.file_location + '_ych2' + '.csv', mode='w') as ych2:
                    wr = csv.writer(ych2)
                    for i in self.ych2_log:
                        wr.writerow(i)
                with open(self.file_location + '_xch2' + '.csv', mode='w') as xch2:
                    wr = csv.writer(xch2)
                    for i in self.xdata2_log:
                        wr.writerow(i)
            self.recording_message.setText("\nReady to record")

    def init_qt(self):
        self.color_white = 'color: white;'
        self.background_red = 'background-color: red;'
        self.background_black = 'background-color: black;'
        self.checked_color_box = "QCheckBox::indicator""{""}""QCheckBox::indicator:checked""{""background-color:green;""}"
        self.checked_color_radio = "QCheckBox::indicator""{""}""QRadioButton::indicator:checked""{""background-color:green;""}"
        self.qss = """
            QMenuBar {
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 lightgray, stop:1 darkgray);
            }
            QMenuBar::item {
                spacing: 3px;           
                padding: 2px 10px;
                background-color: rgb(210,105,30);
                color: rgb(255,255,255);  
                border-radius: 5px;
            }
            QMenuBar::item:selected {    
                background-color: rgb(244,164,96);
            }
            QMenuBar::item:pressed {
                background: rgb(128,0,0);
            }

            /* +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ */  

            QMenu {
                background-color: #ABABAB;   
                border: 1px solid black;
                margin: 2px;
            }
            QMenu::item {
                background-color: transparent;
            }
            QMenu::item:selected { 
                background-color: #654321;
                color: rgb(255,255,255);
            }
            """
        self.show_ch1.setStyleSheet(self.color_white)
        self.show_ch2.setStyleSheet(self.color_white)
        self.centralwidget.setStyleSheet(self.color_white)
        self.show_ch1.setStyleSheet(self.checked_color_box)
        self.show_ch2.setStyleSheet(self.checked_color_box)
        self.menubar.setStyleSheet(self.qss)
        self.Prev_frame.setStyleSheet(self.background_red)
        self.offset_corection = 1000
        self.Live_plot.setStyleSheet(self.background_red)
        self.FFT_Time.setStyleSheet(self.background_red)
        self.save_to_file_pb.setStyleSheet(self.background_red)
        self.Load_from_file_pb.setStyleSheet(self.background_red)
        self.Screen_shot.setStyleSheet(self.background_red)
        self.Next_frame.setStyleSheet(self.background_red)

    def offset_func(self):
        self.yOffset1 = (self.ch1_y_offset.value() - self.offset_corection) / 200
        self.xOffset1 = (self.ch1_x_offset.value() - self.offset_corection) / 20000
        self.yOffset2 = (self.ch2_y_offset.value() - self.offset_corection) / 200
        self.xOffset2 = (self.ch2_x_offset.value() - self.offset_corection) / 20000
        if self.flag_csv_read == True:
            self.plot_from_csv()

    def init_variables(self):
        self.channel_A_list = [22, 23, 24, 25, 18]
        self.channel_B_list = [27, 16, 17, 21, 26]
        self.minimum_len_csv1 = 0
        self.frame_num = 0
        self.x_array1 = list()
        self.y_array1 = list()
        self.file_loc = None
        self.flag_csv_read = False
        self.lines_cvs = None
        self.ych1_log = list()
        self.ych2_log = list()
        self.xdata1_log = list()
        self.xdata2_log = list()
        self.keep_runnig = True
        self.datalog = False
        self.freeze_screen = False
        self.output = list()
        self.show_ch1.setChecked(True)
        self.data = None
        self.channel_num = '01'
        self.freq_samp = '0'
        self.vref = 4.85
        self.gain_ch1 = 1
        self.gain_ch2 = 1
        self.gain_ch3 = 1
        self.volt_div_val_ch1 = 1
        self.volt_div_val_ch2 = 1
        self.volt_div_val_ch3 = 1
        self.time_div_val_ch1 = 1
        self.time_div_val_ch2 = 1
        self.time_div_val_ch3 = 1

        self.xdata = list()
        self.ydata = list()
        self.sample_rate = 0
        self.ax_min = 1
        self.ax_max = 8
        self.ax_step = 0.0001
        self.min_voltage = -5
        self.max_voltage = 5
        self.ych1 = list()
        self.ych2 = list()
        self.ych3 = list()

    def init_button_actions(self):
        self.Screen_shot.clicked.connect(self.screen_shot_func)
        self.actionExit.triggered.connect(self.exit_func)
        self.actionInfo.triggered.connect(self.info_func)
        self.Live_plot.clicked.connect(self.live_plot_func)
        self.FFT_Time.clicked.connect(self.FFT_func)

        self.save_to_file_pb.clicked.connect(self.datalogging)
        self.Load_from_file_pb.clicked.connect(self.load_csv)
        self.Prev_frame.clicked.connect(self.prev_frame_func)
        self.Next_frame.clicked.connect(self.next_frame_func)
        self.Volt_div.valueChanged.connect(self.volt_div_func)
        self.Time_div.valueChanged.connect(self.time_div_func)
        self.Volt_div_2.valueChanged.connect(self.volt_div_func)
        self.Time_div_2.valueChanged.connect(self.time_div_func)
        self.lcd_volt.setSmallDecimalPoint(True)
        self.lcd_volt_2.setSmallDecimalPoint(True)
        self.lcd_time.setSmallDecimalPoint(True)
        self.lcd_time_2.setSmallDecimalPoint(True)
        self.lcd_volt.setDigitCount(6)
        self.lcd_volt_2.setDigitCount(6)
        self.lcd_time.setDigitCount(6)
        self.lcd_time_2.setDigitCount(6)
        self.lcd_volt.display(self.Volt_div.value())
        self.lcd_volt_2.display(self.Volt_div_2.value())
        self.lcd_time.display(self.Time_div.value())
        self.lcd_time_2.display(self.Time_div_2.value())
        self.ch1_y_offset.valueChanged.connect(self.offset_func)
        self.ch1_x_offset.valueChanged.connect(self.offset_func)
        self.ch2_y_offset.valueChanged.connect(self.offset_func)
        self.ch2_x_offset.valueChanged.connect(self.offset_func)
        self.show_ch1.clicked.connect(self.set_channels)
        self.show_ch2.clicked.connect(self.set_channels)
        GPIO.add_event_detect(22, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(23, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(24, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(25, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(18, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(27, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(16, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(17, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(21, GPIO.BOTH, callback=self.gain_func, bouncetime=200)
        GPIO.add_event_detect(26, GPIO.BOTH, callback=self.gain_func, bouncetime=200)

        self.graphicsView.showGrid(x=True, y=True, alpha=1)
        self.graphicsView.plotItem.setLabel('bottom', text='(Time  ', units='*(Time/div))[sec]', color='red')
        self.graphicsView.plotItem.setLabel('left', text='(Amplitude  ', units='*(V/div))[V]', color='red')
        self.graphicsView.plotItem.setClipToView(True)

    def info_func(self):
        dialog = QtWidgets.QDialog()
        dialog.ui = Form()
        dialog.ui.setupUi(dialog)
        dialog.exec_()
        dialog.show()
    def screen_shot_func(self):
        exporter = pg.exporters.ImageExporter(self.graphicsView.scene())
        now = datetime.now()
        text, ok = QtWidgets.QInputDialog.getText(self, 'File name', 'Type file name?')
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if ok and text != '':
            self.file_location = file + "/" + str(text)
            self.datalog = True
            self.recording_message.setText("\nRecording")

        else:
            self.recording_message.setText("\nFile name or location Error\nReady to record")
        exporter.export("{}".format(self.file_location) + ".jpg")
    def FFT_func(self):
        if self.graphicsView.centralWidget.ctrl.fftCheck.isChecked()==False:
            self.graphicsView.centralWidget.ctrl.fftCheck.toggle()
            self.graphicsView.setYRange(self.min_voltage, self.max_voltage)
            self.graphicsView.setXRange(0, 10000)
            self.time_div_val_ch1=1
            self.time_div_val_ch2=1
            self.graphicsView.plotItem.setLabel('bottom', text='(Frequency', units='[Hz]', color='red')

        else:
            self.graphicsView.centralWidget.ctrl.fftCheck.toggle()
            self.graphicsView.plotItem.setLabel('bottom', text='(Time  ', units='*(Time/div))[sec]', color='red')
            self.graphicsView.setYRange(self.min_voltage, self.max_voltage)
            self.graphicsView.setXRange(self.ax_min, self.ax_max)
            self.time_div_func()


    def live_plot_func(self):
        if self.flag_csv_read != True:
            if self.freeze_screen == False:
                self.freeze_screen = True
            else:
                self.freeze_screen = False
        elif self.flag_csv_read == True:
            self.keep_runnig = True
            self.flag_csv_read = False

    def exit_func(self):
        self.keep_runnig = False
        time.sleep(2)
        if self.datalog == True:
            if len(self.ych1_log) > 0:
                with open(self.file_location + '_ych1' + '.csv', mode='w') as ych1:
                    wr = csv.writer(ych1)
                    for i in self.ych1_log:
                        wr.writerow(i)
                with open(self.file_location + '_xch1' + '.csv', mode='w') as xch1:
                    wr = csv.writer(xch1)
                    for i in self.xdata1_log:
                        wr.writerow(i)

            if len(self.ych2_log) > 0:
                with open(self.file_location + '_ych2' + '.csv', mode='w') as ych2:
                    wr = csv.writer(ych2)
                    for i in self.ych2_log:
                        wr.writerow(i)
                with open(self.file_location + '_xch2' + '.csv', mode='w') as xch2:
                    wr = csv.writer(xch2)
                    for i in self.xdata2_log:
                        wr.writerow(i)
        app.quit()

    def set_channels(self):
        global sample_count, channels, batch_size
        if self.show_ch1.isChecked() and self.show_ch2.isChecked():
            channels = '01'
            batch_size = '20'
        elif self.show_ch1.isChecked():
            channels = '0'
            batch_size = '50'
        elif self.show_ch2.isChecked():
            channels = '1'
            batch_size = '50'

    def time_div_func(self):
        global sample_count
        if self.graphicsView.centralWidget.ctrl.fftCheck.isChecked()==True:
            self.time_div_val_ch1 = 1
            self.time_div_val_ch2 = 1
        else:
            if self.Time_div.value() == 0:
                self.time_div_val_ch1 = 0.00005
            elif self.Time_div.value() == 1:
                self.time_div_val_ch1 = 0.0001
            elif self.Time_div.value() == 2:
                self.time_div_val_ch1 = 0.001
            elif self.Time_div.value() == 3:
                self.time_div_val_ch1 = 0.01
            elif self.Time_div.value() == 4:
                self.time_div_val_ch1 = 0.05
            self.lcd_time.display(self.time_div_val_ch1)

            if self.Time_div_2.value() == 0:
                self.time_div_val_ch2 = 0.00005
            elif self.Time_div_2.value() == 1:
                self.time_div_val_ch2 = 0.0001
            elif self.Time_div_2.value() == 2:
                self.time_div_val_ch2 = 0.001
            elif self.Time_div_2.value() == 3:
                self.time_div_val_ch2 = 0.01
            elif self.Time_div_2.value() == 4:
                self.time_div_val_ch2 = 0.05
            self.lcd_time_2.display(self.time_div_val_ch2)
            if self.flag_csv_read == True:
                self.plot_from_csv()

    def volt_div_func(self):

        if self.Volt_div.value() == 0:
            self.volt_div_val_ch1 = 0.01
        elif self.Volt_div.value() == 1:
            self.volt_div_val_ch1 = 0.1
        elif self.Volt_div.value() == 2:
            self.volt_div_val_ch1 = 0.5
        elif self.Volt_div.value() == 3:
            self.volt_div_val_ch1 = 1.0
        elif self.Volt_div.value() == 4:
            self.volt_div_val_ch1 = 5.0
        self.lcd_volt.display(self.volt_div_val_ch1)

        if self.Volt_div_2.value() == 0:
            self.volt_div_val_ch2 = 0.01
        elif self.Volt_div_2.value() == 1:
            self.volt_div_val_ch2 = 0.1
        elif self.Volt_div_2.value() == 2:
            self.volt_div_val_ch2 = 0.5
        elif self.Volt_div_2.value() == 3:
            self.volt_div_val_ch2 = 1.0
        elif self.Volt_div_2.value() == 4:
            self.volt_div_val_ch2 = 5.0
        self.lcd_volt_2.display(self.volt_div_val_ch2)
        if self.flag_csv_read == True:
            self.plot_from_csv()

    def next_frame_func(self):
        if self.frame_num + 1 <= self.minimum_len_csv1:
            self.frame_num = self.frame_num + 1
            self.plot_from_csv()
        else:
            self.csv_message.setText(
                "Ploting from:\n{}\nFrame num:\n{}\nYou reached end of file".format(self.file_loc.split('/')[-1],
                                                                                    self.frame_num))

    def prev_frame_func(self):
        if self.frame_num >= 1:
            self.frame_num = self.frame_num - 1
            self.plot_from_csv()
        else:
            self.csv_message.setText(
                "Ploting from:\n{}\nFrame num:\n{}\nYou reached start of file".format(self.file_loc.split('/')[-1],
                                                                                      self.frame_num))

    def load_csv(self):
        file = QtWidgets.QFileDialog.getOpenFileNames(self, "Select file")
        self.file_loc = ''.join(str(x) for x in file[0])
        self.directory_loc = ''.join(
            self.file_loc.split('/')[x] + '/' for x in range(len(self.file_loc.split('/')[:]) - 1))
        self.filex = self.file_loc.split('/')[-1].split('.')[0][:-4] + 'xch' + self.file_loc.split('/')[-1][-5:]
        self.filey = self.file_loc.split('/')[-1].split('.')[0][:-4] + 'ych' + self.file_loc.split('/')[-1][-5:]
        if self.file_loc.split('/')[-1][-4:] == '.csv':
            try:
                fx = open(self.directory_loc + self.filex, 'r')
                fy = open(self.directory_loc + self.filey, 'r')
                self.lines_csvx = fx.readlines()
                self.lines_csvy = fy.readlines()
                self.csv_message.setText("Ploting from:\n{}".format(self.file_loc.split('/')[-1]))
                for line in self.lines_csvx:
                    self.x_array1.append(np.fromstring(line, dtype=float, sep=','))
                for line in self.lines_csvy:
                    self.y_array1.append(np.fromstring(line, dtype=float, sep=','))
                self.keep_runnig = False
                self.flag_csv_read = True
                self.minimum_len_csv1 = min(len(self.x_array1), len(self.y_array1))
                fx.close()
                fy.close()
                self.csv_message.setText("Ploting from:\n{}".format(self.file_loc.split('/')[-1]))
            except:
                self.csv_message.setText("error loading\n x or y csv file")
                try:
                    fx.close()
                    fy.close()
                except:
                    pass
        elif len(self.file_loc) == 0:
            self.csv_message.setText("No file chosen")
        else:
            self.csv_message.setText("The file:\n{} isn't csv file".format(self.file_loc.split('/')[-1]))
            self.load_csv()
        if self.flag_csv_read == True:
            self.plot_from_csv()

    def plot_from_csv(self):
        if self.flag_csv_read == True:
            if self.frame_num < self.minimum_len_csv1:
                self.graphicsView.plotItem.clear()
                try:
                    y = (self.y_array1[self.frame_num] + self.yOffset1) / self.volt_div_val_ch1
                    x = (self.x_array1[self.frame_num] + self.xOffset1) / self.time_div_val_ch1
                    self.graphicsView.plot(x, y, pen='g')
                    self.csv_message.setText(
                        "Ploting from:\n{}\nFrame num:\n{}".format(self.file_loc.split('/')[-1], self.frame_num))
                except:
                    self.frame_num = self.frame_num - 1
                    self.csv_message.setText("You reached end of file")
            else:
                self.csv_message.setText("You reached end of file")


    def update_plot(self):
        global sample_count, channels, batch_size
        if self.keep_runnig == True:
            if self.freeze_screen == False:
                self.graphicsView.plotItem.clear()
                try:
                    if (self.show_ch1.isChecked() == True and self.show_ch2.isChecked() == True):
                        if self.datalog == True:
                            self.ych1_log.append(self.gain_ch1 * (self.ych1[0] - self.bias))
                            self.ych2_log.append(self.gain_ch2 * (self.ych2[0] - self.bias))
                            self.xdata1_log.append(self.xdata[0][:])
                            self.xdata2_log.append(self.xdata[0] + (
                                    self.xdata[0][1] - self.xdata[0][0]))
                        self.ych1[0] = ((self.ych1[
                                             0] - self.bias + self.yOffset1) / self.gain_ch1) / self.volt_div_val_ch1
                        self.ych2[0] = ((self.ych2[
                                             0] - self.bias + self.yOffset2) / self.gain_ch2) / self.volt_div_val_ch2
                        self.xdata1 = (self.xOffset1 + self.xdata[0][:]) / self.time_div_val_ch1
                        self.xdata2 = ((self.xOffset2 + self.xdata[0] + (
                                self.xdata[0][1] - self.xdata[0][0]))) / self.time_div_val_ch2
                        self.graphicsView.plot(self.xdata1, self.ych1[0], pen='g')
                        self.graphicsView.plot(self.xdata2, self.ych2[0], pen='r')
                        self.ych1.pop(0)
                        self.ych2.pop(0)
                        self.xdata.pop(0)
                    elif (self.show_ch1.isChecked() == True):
                        if self.datalog == True:
                            self.ych1_log.append(self.gain_ch1 * (self.ych1[0] - self.bias))
                            self.xdata1_log.append(self.xdata[0][:])

                        self.ych1[0] = (self.gain_ch1 * (
                                self.ych1[0] + self.yOffset1) - self.bias) / self.volt_div_val_ch1
                        self.xdata1 = (self.xOffset1 + self.xdata[0][:]) / self.time_div_val_ch1
                        self.graphicsView.plot(self.xdata1, self.ych1[0], pen='g')
                        self.ych1.pop(0)
                        self.xdata.pop(0)
                    elif (self.show_ch2.isChecked() == True):
                        if self.datalog == True:
                            self.ych2_log.append(self.gain_ch2 * (self.ych2[0] - self.bias))
                            self.xdata2_log.append(self.xdata[0] + (
                                    self.xdata[0][1] - self.xdata[0][0]))
                        self.ych2[0] = (self.gain_ch2 * (
                                self.ych2[0] + self.yOffset2) - self.bias) / self.volt_div_val_ch2
                        self.xdata2 = ((self.xOffset2 + self.xdata[0] + (
                                self.xdata[0][1] - self.xdata[0][0]))) / self.time_div_val_ch2
                        self.graphicsView.plot(self.xdata2, self.ych2[0], pen='r')

                        self.ych2.pop(0)
                        self.xdata.pop(0)
                    self.sample_rate_label.setText("Sample rate\nper channel:\n{}".format(self.sample_rate))
                except:
                    pass

    def get_data(self, arg):
        popen = subprocess.Popen("mcp3008hwspi -c 2 -f 0 -n 500  -b 10", shell=True, stdout=subprocess.PIPE)
        output = popen.communicate()[0]
        data = np.genfromtxt(StringIO(self.output.decode('utf-8')), skip_header=1, delimiter=',', names=True)
        return data['value_ch2']

    def change_args(self):
        global sample_count
        self.args = (
            "mcp3008hwspi -c {0} -f {1} -n {2}  -b 10".format(self.channel_num, self.freq_samp, sample_count))



if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    try:
        app.setStyleSheet(stylesheet)
    except:
        print("Backround Picture File Not Found")
    w = MyWindow()
    w.show()
    sys.exit(app.exec_())
