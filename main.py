# coding=gbk
"""
动态加载ui文件
"""

import copy
import sys
import threading
import time
import configparser
import ldControl
from shutil import copyfile
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget,  QTableWidgetItem, QFileDialog, \
    QAbstractItemView, QHeaderView
from PyQt5 import uic, QtCore


checkEmuList=[]#选中模拟器加入到已选中模拟器列表
bakList=[]#备份已选中模拟器列表


class refreshEmulatorThread(QThread):
    # 声明刷新模拟器的自定义信号，类型为list，内容即ld对象返回的模拟器列表
    refreshEmulator_signal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.ld = ldControl.LdConsole()

    def run(self):
            while True:
                ldlist = self.ld.refreshEmulator()
                self.refreshEmulator_signal.emit(ldlist)#发射模拟器列表信号
                time.sleep(5)
                # print("更新table中")

class emuConsole():
    def __init__(self):
        self.ld = ldControl.LdConsole()
        self.w=MyWindow()

    def copyVmdk(self):
        source_file = w.lineEdit_vmdkPath.text()
        destination_filepath = w.lineEdit_vmsPath.text()
        # D:\Program Files (x86)\ChangZhi\dnplayer2\vms
        for i in range(len(checkEmuList)):
            destination_file=destination_filepath+'\\leidian'+checkEmuList[i]+'\system.vmdk'
            # print(destination_file)
            try:
                copyfile(source_file, destination_file)
                w.textBrowser_log.append("雷电模拟器%s VMDK覆盖完毕"%(checkEmuList[i]))
            except:
                print("VMDK覆盖出错，雷电%s无法读写，请关闭模拟器后再试"%(checkEmuList[i]))
                w.textBrowser_log.append("VMDK覆盖出错，雷电模拟器%s无法读写，请关闭模拟器后再试"%(checkEmuList[i]))

    def startEmulator(self):
        for i in range(len(checkEmuList)):
            if w.checkBox_powerBootApp.isChecked():
                # print(w.lineEdit_powerBootAppName.text())
                self.ld.powerBootApp(checkEmuList[i],w.lineEdit_powerBootAppName.text())
            else:
                self.ld.startEmulator(checkEmuList[i])
            time.sleep(1)

    def sendShell(self):
        for i in range(len(checkEmuList)):
            if self.ld.emulatorIsRunning(i):
                self.ld.ldShell(checkEmuList[i],w.lineEdit_shellCommand.text())
                w.textBrowser_log.append("模拟器%s执行shell命令成功" %(checkEmuList[i]))
            else:
                w.textBrowser_log.append("模拟器%s未启动，执行shell命令失败"%(checkEmuList[i]))

    def executeGlobalSet(self):
        CPU=w.lineEdit_CPU.text()
        memory=w.lineEdit_memory.text()
        FPS=w.lineEdit_FPS.text()
        downCPU=w.lineEdit_DownCPU.text()
        resolution=w.lineEdit_resolution.text()
        if w.checkBox_fastPlay.isChecked()==True:
            fastPlay=1
        else:
            fastPlay=0
        if w.checkBox_audio.isChecked()==True:
            audio=1
        else:
            audio=0
        if w.checkBox_cleanMode.isChecked()==True:
            cleanMode=1
        else:
            cleanMode=0

        for i in range(len(self.ld.getLdDevicesList())):
            self.ld.emulatorGlobalSet(i, FPS, audio, fastPlay, cleanMode, resolution, CPU, memory, downCPU)
            if self.ld.emulatorIsRunning(i)==True:
                w.textBrowser_log.append(f"模拟器{i}正在运行中,全局配置重启后生效")
            else:
                w.textBrowser_log.append(f"模拟器{i}全局配置成功")

class appConsole():
    def __init__(self):
        # super().__init__()
        self.ld = ldControl.LdConsole()
        self.w=MyWindow()

    def startApp(self):
        for i in range(len(checkEmuList)):
            self.ld.runApp(checkEmuList[i], w.lineEdit_appPackageName.text())

    def stopApp(self):
        for i in range(len(checkEmuList)):
            self.ld.killApp(checkEmuList[i], w.lineEdit_appPackageName.text())

    def startScript(self):
        for i in range(len(checkEmuList)):
            self.ld.runApp(checkEmuList[i],w.lineEdit_scriptPackageName.text())

    def stopScript(self):
        for i in range(len(checkEmuList)):
            self.ld.killApp(checkEmuList[i], w.lineEdit_scriptPackageName.text())

    def suspendScript(self):
        for i in range(len(checkEmuList)):
            self.ld.startAnJianScript(checkEmuList[i])

    def recoveryScript(self):
        for i in range(len(checkEmuList)):
            self.ld.startAnJianScript(checkEmuList[i])

    def updateApp(self):
        for i in range(len(self.ld.getLdDevicesList())):
            # print(i,self.ld.emulatorIsRunning(i))
            if self.ld.emulatorIsRunning(i):
                self.ld.installAPP(i,w.lineEdit_appPath.text())
                time.sleep(5)
                w.textBrowser_log.append("模拟器%s应用更新完成" %(i))
            else:
                w.textBrowser_log.append("模拟器%s未运行，安装失败"%(i))

class MyWindow(QWidget):
    sum = 0
    checkRow = 0
    def __init__(self):
        super().__init__()
        self.ld = ldControl.LdConsole()
        self.ini_ui()
        self.refreshEmulator = refreshEmulatorThread()
        self.readDefaultCfg()

    def ini_ui(self):
        self.ui = uic.loadUi("UI.ui")
        # print(self.ui.__dict__)  # 查看ui文件中有哪些控件

        # 提取控件
        self.tableWidget=self.ui.tableWidget
        self.listWidget_candidate=self.ui.listWidget_candidate
        self.listWidget_selected = self.ui.listWidget_selected
        self.textBrowser_log= self.ui.textBrowser_log

        #模拟器操作控件
        self.pushButton_startEmulator=self.ui.pushButton_startEmulator#启动模拟器按钮
        self.pushButton_stopEmulator = self.ui.pushButton_stopEmulator#关闭模拟器按钮
        self.pushButton_rebootEmulator = self.ui.pushButton_rebootEmulator # 重启模拟器按钮
        self.pushButton_refreshEmulator = self.ui.pushButton_refreshEmulator  # 刷新模拟器按钮
        self.pushButton_seleteAll = self.ui.pushButton_seleteAll # 全选模拟器按钮
        self.pushButton_deselectAll = self.ui.pushButton_deselectAll  # 取消全选模拟器按钮
        self.pushButton_sortWnd = self.ui.pushButton_sortWnd # 排列窗口按钮
        self.pushButton_updateApp = self.ui.pushButton_updateApp  # 更新应用按钮
        self.pushButton_reSetVmdk=self.ui.pushButton_reSetVmdk #重置vmdk按钮
        self.pushButton_saveDefaultCfg=self.ui.pushButton_saveDefaultCfg#保存界面配置按钮
        self.pushButton_sendShell=self.ui.pushButton_sendShell #发送shell
        self.pushButton_executeGlobalSet=self.ui.pushButton_executeGlobalSet

        # 路径配置控件
        self.pushButton_loadAppPath = self.ui.pushButton_loadAppPath  # 加载app路径按钮
        self.lineEdit_appPath = self.ui.lineEdit_appPath  # 模拟器路径
        self.pushButton_loadVmdkPath = self.ui.pushButton_loadVmdkPath  # 加载vmdk路径按钮
        self.lineEdit_vmdkPath = self.ui.lineEdit_vmdkPath  # vmdk路径
        self.pushButton_loadVmsPath = self.ui.pushButton_loadVmsPath  # 加载vms路径按钮
        self.lineEdit_vmsPath = self.ui.lineEdit_vmsPath  # vms路径

        # 任务设置控件
        self.pushButton_addAllTask=self.ui.pushButton_addAllTask #全选任务按钮
        self.pushButton_removeAllTask = self.ui.pushButton_removeAllTask  # 全选任务按钮

        # 模拟器参数配置控件
        self.pushButton_randomCfg = self.ui.pushButton_randomCfg  # 随机配置按钮
        self.pushButton_saveCfg = self.ui.pushButton_saveCfg  # 读取配置按钮
        self.lineEdit_IMEI = self.ui.lineEdit_IMEI  # 模拟器IMEI
        self.lineEdit_IMSI = self.ui.lineEdit_IMSI  # 模拟器IMSI
        self.lineEdit_SIM = self.ui.lineEdit_SIM  # 模拟器SIM
        self.lineEdit_androidID = self.ui.lineEdit_androidID  # 模拟器安卓ID

        # 脚本操作控件
        self.pushButton_startApp=self.ui.pushButton_startApp #启动APP按钮
        self.pushButton_stopApp = self.ui.pushButton_stopApp  # 终止APP按钮
        self.pushButton_startScript=self.ui.pushButton_startScript #启动脚本按钮
        self.pushButton_stopScript = self.ui.pushButton_stopScript  # 启动脚本按钮
        self.pushButton_suspendScript=self.ui.pushButton_suspendScript #运行脚本按钮
        self.pushButton_recoveryScript=self.ui.pushButton_recoveryScript#暂停脚本按钮


        # 其他控件
        self.checkBox_powerBootApp=self.ui.checkBox_powerBootApp#开机自启APP
        self.lineEdit_powerBootAppName=self.ui.lineEdit_powerBootAppName#开机自启APP包名
        self.lineEdit_scriptPackageName=self.ui.lineEdit_scriptPackageName#脚本包名
        self.lineEdit_appPackageName=self.ui.lineEdit_appPackageName#app包名
        self.lineEdit_shellCommand=self.ui.lineEdit_shellCommand#shell命令

        #全局配置控件
        self.lineEdit_CPU=self.ui.lineEdit_CPU
        self.lineEdit_memory=self.ui.lineEdit_memory
        self.lineEdit_FPS=self.ui.lineEdit_FPS
        self.lineEdit_DownCPU=self.ui.lineEdit_DownCPU
        self.lineEdit_resolution=self.ui.lineEdit_resolution
        self.checkBox_fastPlay=self.ui.checkBox_fastPlay
        self.checkBox_audio=self.ui.checkBox_audio
        self.checkBox_cleanMode=self.ui.checkBox_cleanMode

        #设置tableWigdit格式
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)#禁止编辑
        self.tableWidget.setShowGrid(True)#显示网格
        self.tableWidget.verticalHeader().setVisible(False)  # False隐藏表头
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)#选择整行
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)#表头自适应列宽


        #写入tableWigdit数据
        ldlist=self.ld.getLdDevicesList()
        data = ['选中',"索引", "标题", "顶层窗口句柄", "绑定窗口句柄", "是否进入安卓", '进程PID', "VBOXPID"]
        self.tableWidget.setColumnCount(len(data))
        self.tableWidget.setRowCount(len(ldlist))
        for i in range(len(data)):
            self.tableWidget.setHorizontalHeaderItem(i, QTableWidgetItem(str(data[i])))
        for i in range(len(ldlist)):
            self.item=QTableWidgetItem()
            self.item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.item.setCheckState(QtCore.Qt.Unchecked)
            self.item.setData(QtCore.Qt.UserRole, self.item.checkState())
            self.tableWidget.setItem(i, 0, self.item)
            for j in range(len(ldlist[i])):
                self.tableWidget.setItem(i, j + 1, QTableWidgetItem(str(ldlist[i][j])))

        # 写入listWigdit数据
        taskList=["任务0","任务1","任务2","任务3","任务4"]
        for i in taskList:
            self.listWidget_candidate.addItem(i)

        #写入提示
        # self.textBrowser_log.append("使用前必须将雷电模拟器路径下的ldconsole.exe加入系统环境变量")

        # 绑定信号与槽函数
        # self.tableWidget.cellPressed.connect(self.readCfg)#读取表格参数
        self.tableWidget.cellPressed.connect(self.readCfgThread)  # 读取表格参数
        self.tableWidget.cellChanged.connect(self.checkEmulator)#table复选框变化事件
        self.listWidget_candidate.itemDoubleClicked.connect(self.addTask)#list点击事件
        self.listWidget_selected.itemDoubleClicked.connect(self.removeTask)  # list点击事件

        self.pushButton_loadAppPath.clicked.connect(self.loadAppPath)
        self.pushButton_loadVmdkPath.clicked.connect(self.loadVmdkPath)
        self.pushButton_loadVmsPath.clicked.connect(self.loadVmsPath)

        self.pushButton_startEmulator.clicked.connect(self.startEmulator)
        self.pushButton_stopEmulator.clicked.connect(self.stopEmulator)
        self.pushButton_rebootEmulator.clicked.connect(self.rebootEmulator)
        self.pushButton_refreshEmulator.clicked.connect(self.refreshEmulator_click)
        self.pushButton_seleteAll.clicked.connect(self.seleteAll)
        self.pushButton_deselectAll.clicked.connect(self.deselectAll)
        self.pushButton_sortWnd.clicked.connect(self.sortWnd)
        self.pushButton_updateApp.clicked.connect(self.updateApp)


        self.pushButton_startApp.clicked.connect(self.startApp)
        self.pushButton_stopApp.clicked.connect(self.stopApp)
        self.pushButton_startScript.clicked.connect(self.startAJScript)
        self.pushButton_stopScript.clicked.connect(self.stopAJScript)
        self.pushButton_suspendScript.clicked.connect(self.suspendAJScript)
        self.pushButton_recoveryScript.clicked.connect(self.recoveryAJScript)
        self.pushButton_saveDefaultCfg.clicked.connect(self.saveDefaultCfg)
        self.pushButton_randomCfg.clicked.connect(self.randomCfg)
        self.pushButton_saveCfg.clicked.connect(self.saveCfg)
        self.pushButton_reSetVmdk.clicked.connect(self.reSetVmdk)
        self.pushButton_removeAllTask.clicked.connect(self.removeAllTask)
        self.pushButton_addAllTask.clicked.connect(self.addAllTask)
        self.pushButton_sendShell.clicked.connect(self.sendShell)
        self.pushButton_executeGlobalSet.clicked.connect(self.executeGlobalSet)
        # self.login_status_signal.connect(self.login_status)#绑定自定义槽函数

    def readDefaultCfg(self):
        #  实例化configParser对象
        config = configparser.ConfigParser()
        # -read读取ini文件
        config.read('conf.ini', encoding='GB18030')
        # -sections得到所有的section，并以列表的形式返回
        # print('sections:', ' ', config.sections())
        # -options(section)得到该section的所有option
        # print('options:', ' ', config.options('appName'))
        # print('options:', ' ', config.options('filePath'))
        # -items（section）得到该section的所有键值对
        # print('items:', ' ', config.items('filePath'))

        # # -get(section,option)得到section中option的值，返回为string类型
        # print('get:', ' ', config.get('appName', 'powerBootApp'))
        # # -getint(section,option)得到section中的option的值，返回为int类型
        # print('getint:', ' ', config.getint('cmd', 'id'))
        # print('getfloat:', ' ', config.getfloat('cmd', 'weight'))
        # print('getboolean:', '  ', config.getboolean('cmd', 'isChoice'))
        self.lineEdit_powerBootAppName.setText(config.get('appName', 'powerBootApp'))
        self.lineEdit_scriptPackageName.setText(config.get('appName', 'scriptPackageName'))
        self.lineEdit_appPackageName.setText(config.get('appName', 'APPPackageName'))
        self.lineEdit_appPath.setText(config.get('filePath', 'updateAppPath'))
        self.lineEdit_vmdkPath.setText(config.get('filePath', 'VMDKPath'))
        self.lineEdit_vmsPath.setText(config.get('filePath', 'VMSPath'))
        self.lineEdit_shellCommand.setText(config.get('shell', 'command'))
        self.lineEdit_CPU.setText(config.get('globalSetting','CPU'))
        self.lineEdit_memory.setText(config.get('globalSetting','memory'))
        self.lineEdit_FPS.setText(config.get('globalSetting','FPS'))
        self.lineEdit_DownCPU.setText(config.get('globalSetting','downCPU'))
        self.lineEdit_resolution.setText(config.get('globalSetting','resolution'))
        if config.getboolean('checkbox', 'ispowerBootApp')==True:
            self.checkBox_powerBootApp.setChecked(True)
        else:
            self.checkBox_powerBootApp.setChecked(False)

        if config.getboolean('globalSetting', 'fastPlay')==True:
            self.checkBox_fastPlay.setChecked(True)
        else:
            self.checkBox_fastPlay.setChecked(False)

        if config.getboolean('globalSetting', 'audio')==True:
            self.checkBox_audio.setChecked(True)
        else:
            self.checkBox_audio.setChecked(False)

        if config.getboolean('globalSetting', 'cleanMode')==True:
            self.checkBox_cleanMode.setChecked(True)
        else:
            self.checkBox_cleanMode.setChecked(False)

    def saveDefaultCfg(self):
        config = configparser.ConfigParser()
        config.read('conf.ini', encoding='GB18030')
        config.set('appName','powerBootApp',self.lineEdit_powerBootAppName.text())
        config.set('appName', 'scriptPackageName', self.lineEdit_scriptPackageName.text())
        config.set('appName', 'APPPackageName', self.lineEdit_appPackageName.text())
        config.set('filePath', 'updateAppPath', self.lineEdit_appPath.text())
        config.set('filePath', 'VMDKPath', self.lineEdit_vmdkPath.text())
        config.set('filePath', 'VMSPath', self.lineEdit_vmsPath.text())
        config.set('globalSetting', 'CPU', self.lineEdit_CPU.text())
        config.set('globalSetting', 'memory', self.lineEdit_memory.text())
        config.set('globalSetting', 'FPS', self.lineEdit_FPS.text())
        config.set('globalSetting', 'downCPU', self.lineEdit_DownCPU.text())
        config.set('globalSetting', 'resolution', self.lineEdit_resolution.text())

        if self.checkBox_powerBootApp.isChecked()==True:
            config.set('checkbox', 'ispowerBootApp', 'True')
        else:
            config.set('checkbox', 'ispowerBootApp', 'False')

        if self.checkBox_fastPlay.isChecked()==True:
            config.set('globalSetting', 'fastPlay', 'True')
        else:
            config.set('globalSetting', 'fastPlay', 'False')

        if self.checkBox_audio.isChecked()==True:
            config.set('globalSetting', 'audio', 'True')
        else:
            config.set('globalSetting', 'audio', 'False')

        if self.checkBox_cleanMode.isChecked()==True:
            config.set('globalSetting', 'cleanMode', 'True')
        else:
            config.set('globalSetting', 'cleanMode', 'False')


        io = open('conf.ini', 'w')
        config.write(io)
        io.close()  # 不要忘记关闭

    def checkEmulator(self,row,column):
        item = self.tableWidget.item(row, column)
        # print(row, column)
        lastState = item.data(QtCore.Qt.UserRole)
        # print("check函数",item)
        currentState = item.checkState()
        # print(lastState,currentState)
        if currentState != lastState:
            # print("changed: ")
            if currentState == QtCore.Qt.Checked:
                # print("checked")
                checkEmuList.append(str(row))
                # print(checkEmuList)
            else:
                # print("uncheck：")
                if str(row) in checkEmuList :
                    # print("待移除选项：", str(row))
                    checkEmuList.remove(str(row))
                # print("移除选项后的：",checkEmuList)
            item.setData(QtCore.Qt.UserRole, currentState)

    def startEmulator(self):
        self.emuCon=emuConsole()
        newThread=threading.Thread(target=self.emuCon.startEmulator)
        newThread.start()

    def stopEmulator(self):
        for i in range(len(checkEmuList)):
            self.ld.stopEmulator(checkEmuList[i])

    def rebootEmulator(self):
        for i in range(len(checkEmuList)):
            self.ld.rebootEmulator(checkEmuList[i])
            time.sleep(1)

    def refreshEmulator_click(self):
        self.sum += 1
        if self.sum % 2 == 0:
            self.refreshEmulator.refreshEmulator_signal.disconnect(self.refreshEmulator_slot)
            self.pushButton_refreshEmulator.setText("恢复刷新")
            self.refreshEmulator.terminate()
        else:
            self.refreshEmulator.refreshEmulator_signal.connect(self.refreshEmulator_slot)#绑定槽方法
            self.pushButton_refreshEmulator.setText("暂停刷新")
            self.refreshEmulator.start()

    def refreshEmulator_slot(self, ldlist):#接收发射信号，ld对象返回的模拟器列表list
        # 更新表格内容
        global checkEmuList
        bakList = copy.deepcopy(checkEmuList)
        # print("bak前baklist：",bakList)
        for i in range(len(ldlist)):
            for j in range(len(ldlist[i])):
                self.tableWidget.setItem(i, j + 3, QTableWidgetItem(str(ldlist[i][j])))
        # print("bak后：baklist", bakList)
        checkEmuList=bakList
        # print("fresh后：",checkEmuList)
        self.tableWidget.update()

    def seleteAll(self):
        global checkEmuList
        # self.ld = ldControl.LdConsole()
        ldlist = self.ld.getLdDevicesList()
        self.tableWidget.setRowCount(len(ldlist))
        for i in range(len(ldlist)):
            self.item = QTableWidgetItem()
            self.item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.item.setCheckState(QtCore.Qt.Checked)#Unchecked
            self.item.setData(QtCore.Qt.UserRole, self.item.checkState())
            self.tableWidget.setItem(i, 0, self.item)
            checkEmuList.append(str(i))
        checkEmuList=list(set(checkEmuList))
        # print(checkEmuList)

    def deselectAll(self):
        global checkEmuList
        # self.ld = ldControl.LdConsole()
        list = self.ld.getLdDevicesList()
        self.tableWidget.setRowCount(len(list))
        for i in range(len(list)):
            self.item = QTableWidgetItem()
            self.item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.item.setCheckState(QtCore.Qt.Unchecked)  # Unchecked
            self.item.setData(QtCore.Qt.UserRole, self.item.checkState())
            self.tableWidget.setItem(i, 0, self.item)
        checkEmuList=[]
        # print(checkEmuList)

    def addTask(self,Index):
        index = int(self.listWidget_candidate.currentIndex().row())#获取选中行索引
        self.listWidget_selected.addItem(self.listWidget_candidate.item(index).text())#将选中行内容添加到已选任务列表
        self.listWidget_candidate.takeItem(self.listWidget_candidate.currentIndex().row())#在待选任务列表中删除选中行

    def removeTask(self,Index):
        index = int(self.listWidget_selected.currentIndex().row())#获取选中行索引
        self.listWidget_candidate.addItem(self.listWidget_selected.item(index).text())#将选中行内容添加到待选任务列表
        self.listWidget_selected.takeItem(self.listWidget_selected.currentIndex().row())#在已选任务列表中删除选中行

    def addAllTask(self,Index):
        for i in range(self.listWidget_candidate.count()):
            print(self.listWidget_candidate.item(i).text())
            self.listWidget_selected.addItem(self.listWidget_candidate.item(i).text())
        self.listWidget_candidate.clear()

    def removeAllTask(self,Index):
        for i in range(self.listWidget_selected.count()):
            print(self.listWidget_selected.item(i).text())
            self.listWidget_candidate.addItem(self.listWidget_selected.item(i).text())
        self.listWidget_selected.clear()

    def loadAppPath(self):
        path,filter = QFileDialog.getOpenFileName(filter="APK (*.apk)")#返回了文件路径和筛选类型
        # print(path,filter)
        self.lineEdit_appPath.setText(path)

    def loadVmdkPath(self):
        path,filter = QFileDialog.getOpenFileName(filter="APK (*.vmdk)")#返回了文件路径和筛选类型
        # print(path,filter)
        self.lineEdit_vmdkPath.setText(path)

    def loadVmsPath(self):
        path=QFileDialog.getExistingDirectory(self, "选择模拟器VMS目录")
        self.lineEdit_vmsPath.setText(path)

    def readCfgThread(self,row,col):
        global checkRow
        checkRow = row
        newThread=threading.Thread(target=self.readCfg,args=(row,))
        newThread.start()

    def readCfg(self,row):
        # content = self.tableWidget.item(row, col).text()#选中内容
        # print("选中行：" + str(row))
        # print("选中列：" + str(col))
        # print('选中内容:' + content)
        # global checkRow
        # checkRow = row
        # self.ld = ldControl.LdConsole()
        if self.ld.emulatorIsRunning(row):
            para=self.ld.getEmulatorParameter(row)
            # print(para)
            if para!=[]:
                self.lineEdit_IMEI.setText(para[0])   # 模拟器IMEI
                self.lineEdit_IMSI.setText(para[1])  # 模拟器IMSI
                self.lineEdit_SIM.setText(para[2])  # 模拟器SIM
                self.lineEdit_androidID.setText(para[3])   # 模拟器安卓ID
            else:
                self.textBrowser_log.append('adb异常，无法获取模拟器参数信息,输入netstat -ano | finder ”5037“查询占用信息，使用taskkill /pid pid结束进程')
                print('adb异常，无法获取模拟器参数信息,输入netstat -ano | finder ”5037“查询占用信息，使用taskkill /pid pid结束进程')
        else:
            self.textBrowser_log.append('模拟器未运行,无法获取模拟器参数')
            print('模拟器未运行,无法获取模拟器参数')

    def randomCfg(self):
        global checkRow
        self.ld.randomSetEmulatorParameter(checkRow)
        newThread=threading.Thread(target=self.readCfg,args=(checkRow,))
        newThread.start()

    def saveCfg(self):
        global checkRow
        paraList = []
        # self.ld = ldControl.LdConsole()
        if self.ld.emulatorIsRunning(checkRow):
            # paraList.append(self.lineEdit_phoneNum.text())
            paraList.append(self.lineEdit_IMEI.text())
            paraList.append(self.lineEdit_IMSI.text())
            paraList.append(self.lineEdit_SIM.text())
            paraList.append(self.lineEdit_androidID.text())
            # paraList.append(self.lineEdit_MAC.text())
        # print(paraList)
            self.ld.setEmulatorParameter(checkRow,paraList)
        else:
            # QMessageBox.information(self, "提示", "模拟器未运行，请在运行时更改参数")
            self.textBrowser_log.append("模拟器未运行，请在运行时更改参数")

    def sortWnd(self):
        self.ld.sortWnd()

    def updateApp(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.updateApp)
        newThread.start()

    def startAJScript(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.startScript)
        newThread.start()

    def stopAJScript(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.stopScript)
        newThread.start()

    def startApp(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.startApp)
        newThread.start()

    def stopApp(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.stopApp)
        newThread.start()

    def suspendAJScript(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.suspendScript)
        newThread.start()

    def recoveryAJScript(self):
        self.appCon=appConsole()
        newThread=threading.Thread(target=self.appCon.recoveryScript)
        newThread.start()

    def reSetVmdk(self):
        self.emuCon=emuConsole()
        newThread=threading.Thread(target=self.emuCon.copyVmdk)
        newThread.start()

    def sendShell(self):
        self.emuCon=emuConsole()
        newThread=threading.Thread(target=self.emuCon.sendShell)
        newThread.start()

    def executeGlobalSet(self):
        self.emuCon = emuConsole()
        newThread = threading.Thread(target=self.emuCon.executeGlobalSet)
        newThread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 展示窗口
    w=MyWindow()
    w.ui.show()
    app.exec()
