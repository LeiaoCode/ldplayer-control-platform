# coding=gbk
"""
��̬����ui�ļ�
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


checkEmuList=[]#ѡ��ģ�������뵽��ѡ��ģ�����б�
bakList=[]#������ѡ��ģ�����б�


class refreshEmulatorThread(QThread):
    # ����ˢ��ģ�������Զ����źţ�����Ϊlist�����ݼ�ld���󷵻ص�ģ�����б�
    refreshEmulator_signal = pyqtSignal(list)
    def __init__(self):
        super().__init__()
        self.ld = ldControl.LdConsole()

    def run(self):
            while True:
                ldlist = self.ld.refreshEmulator()
                self.refreshEmulator_signal.emit(ldlist)#����ģ�����б��ź�
                time.sleep(5)
                # print("����table��")

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
                w.textBrowser_log.append("�׵�ģ����%s VMDK�������"%(checkEmuList[i]))
            except:
                print("VMDK���ǳ����׵�%s�޷���д����ر�ģ����������"%(checkEmuList[i]))
                w.textBrowser_log.append("VMDK���ǳ����׵�ģ����%s�޷���д����ر�ģ����������"%(checkEmuList[i]))

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
                w.textBrowser_log.append("ģ����%sִ��shell����ɹ�" %(checkEmuList[i]))
            else:
                w.textBrowser_log.append("ģ����%sδ������ִ��shell����ʧ��"%(checkEmuList[i]))

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
                w.textBrowser_log.append(f"ģ����{i}����������,ȫ��������������Ч")
            else:
                w.textBrowser_log.append(f"ģ����{i}ȫ�����óɹ�")

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
                w.textBrowser_log.append("ģ����%sӦ�ø������" %(i))
            else:
                w.textBrowser_log.append("ģ����%sδ���У���װʧ��"%(i))

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
        # print(self.ui.__dict__)  # �鿴ui�ļ�������Щ�ؼ�

        # ��ȡ�ؼ�
        self.tableWidget=self.ui.tableWidget
        self.listWidget_candidate=self.ui.listWidget_candidate
        self.listWidget_selected = self.ui.listWidget_selected
        self.textBrowser_log= self.ui.textBrowser_log

        #ģ���������ؼ�
        self.pushButton_startEmulator=self.ui.pushButton_startEmulator#����ģ������ť
        self.pushButton_stopEmulator = self.ui.pushButton_stopEmulator#�ر�ģ������ť
        self.pushButton_rebootEmulator = self.ui.pushButton_rebootEmulator # ����ģ������ť
        self.pushButton_refreshEmulator = self.ui.pushButton_refreshEmulator  # ˢ��ģ������ť
        self.pushButton_seleteAll = self.ui.pushButton_seleteAll # ȫѡģ������ť
        self.pushButton_deselectAll = self.ui.pushButton_deselectAll  # ȡ��ȫѡģ������ť
        self.pushButton_sortWnd = self.ui.pushButton_sortWnd # ���д��ڰ�ť
        self.pushButton_updateApp = self.ui.pushButton_updateApp  # ����Ӧ�ð�ť
        self.pushButton_reSetVmdk=self.ui.pushButton_reSetVmdk #����vmdk��ť
        self.pushButton_saveDefaultCfg=self.ui.pushButton_saveDefaultCfg#����������ð�ť
        self.pushButton_sendShell=self.ui.pushButton_sendShell #����shell
        self.pushButton_executeGlobalSet=self.ui.pushButton_executeGlobalSet

        # ·�����ÿؼ�
        self.pushButton_loadAppPath = self.ui.pushButton_loadAppPath  # ����app·����ť
        self.lineEdit_appPath = self.ui.lineEdit_appPath  # ģ����·��
        self.pushButton_loadVmdkPath = self.ui.pushButton_loadVmdkPath  # ����vmdk·����ť
        self.lineEdit_vmdkPath = self.ui.lineEdit_vmdkPath  # vmdk·��
        self.pushButton_loadVmsPath = self.ui.pushButton_loadVmsPath  # ����vms·����ť
        self.lineEdit_vmsPath = self.ui.lineEdit_vmsPath  # vms·��

        # �������ÿؼ�
        self.pushButton_addAllTask=self.ui.pushButton_addAllTask #ȫѡ����ť
        self.pushButton_removeAllTask = self.ui.pushButton_removeAllTask  # ȫѡ����ť

        # ģ�����������ÿؼ�
        self.pushButton_randomCfg = self.ui.pushButton_randomCfg  # ������ð�ť
        self.pushButton_saveCfg = self.ui.pushButton_saveCfg  # ��ȡ���ð�ť
        self.lineEdit_IMEI = self.ui.lineEdit_IMEI  # ģ����IMEI
        self.lineEdit_IMSI = self.ui.lineEdit_IMSI  # ģ����IMSI
        self.lineEdit_SIM = self.ui.lineEdit_SIM  # ģ����SIM
        self.lineEdit_androidID = self.ui.lineEdit_androidID  # ģ������׿ID

        # �ű������ؼ�
        self.pushButton_startApp=self.ui.pushButton_startApp #����APP��ť
        self.pushButton_stopApp = self.ui.pushButton_stopApp  # ��ֹAPP��ť
        self.pushButton_startScript=self.ui.pushButton_startScript #�����ű���ť
        self.pushButton_stopScript = self.ui.pushButton_stopScript  # �����ű���ť
        self.pushButton_suspendScript=self.ui.pushButton_suspendScript #���нű���ť
        self.pushButton_recoveryScript=self.ui.pushButton_recoveryScript#��ͣ�ű���ť


        # �����ؼ�
        self.checkBox_powerBootApp=self.ui.checkBox_powerBootApp#��������APP
        self.lineEdit_powerBootAppName=self.ui.lineEdit_powerBootAppName#��������APP����
        self.lineEdit_scriptPackageName=self.ui.lineEdit_scriptPackageName#�ű�����
        self.lineEdit_appPackageName=self.ui.lineEdit_appPackageName#app����
        self.lineEdit_shellCommand=self.ui.lineEdit_shellCommand#shell����

        #ȫ�����ÿؼ�
        self.lineEdit_CPU=self.ui.lineEdit_CPU
        self.lineEdit_memory=self.ui.lineEdit_memory
        self.lineEdit_FPS=self.ui.lineEdit_FPS
        self.lineEdit_DownCPU=self.ui.lineEdit_DownCPU
        self.lineEdit_resolution=self.ui.lineEdit_resolution
        self.checkBox_fastPlay=self.ui.checkBox_fastPlay
        self.checkBox_audio=self.ui.checkBox_audio
        self.checkBox_cleanMode=self.ui.checkBox_cleanMode

        #����tableWigdit��ʽ
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)#��ֹ�༭
        self.tableWidget.setShowGrid(True)#��ʾ����
        self.tableWidget.verticalHeader().setVisible(False)  # False���ر�ͷ
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)#ѡ������
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)#��ͷ����Ӧ�п�


        #д��tableWigdit����
        ldlist=self.ld.getLdDevicesList()
        data = ['ѡ��',"����", "����", "���㴰�ھ��", "�󶨴��ھ��", "�Ƿ���밲׿", '����PID', "VBOXPID"]
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

        # д��listWigdit����
        taskList=["����0","����1","����2","����3","����4"]
        for i in taskList:
            self.listWidget_candidate.addItem(i)

        #д����ʾ
        # self.textBrowser_log.append("ʹ��ǰ���뽫�׵�ģ����·���µ�ldconsole.exe����ϵͳ��������")

        # ���ź���ۺ���
        # self.tableWidget.cellPressed.connect(self.readCfg)#��ȡ������
        self.tableWidget.cellPressed.connect(self.readCfgThread)  # ��ȡ������
        self.tableWidget.cellChanged.connect(self.checkEmulator)#table��ѡ��仯�¼�
        self.listWidget_candidate.itemDoubleClicked.connect(self.addTask)#list����¼�
        self.listWidget_selected.itemDoubleClicked.connect(self.removeTask)  # list����¼�

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
        # self.login_status_signal.connect(self.login_status)#���Զ���ۺ���

    def readDefaultCfg(self):
        #  ʵ����configParser����
        config = configparser.ConfigParser()
        # -read��ȡini�ļ�
        config.read('conf.ini', encoding='GB18030')
        # -sections�õ����е�section�������б����ʽ����
        # print('sections:', ' ', config.sections())
        # -options(section)�õ���section������option
        # print('options:', ' ', config.options('appName'))
        # print('options:', ' ', config.options('filePath'))
        # -items��section���õ���section�����м�ֵ��
        # print('items:', ' ', config.items('filePath'))

        # # -get(section,option)�õ�section��option��ֵ������Ϊstring����
        # print('get:', ' ', config.get('appName', 'powerBootApp'))
        # # -getint(section,option)�õ�section�е�option��ֵ������Ϊint����
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
        io.close()  # ��Ҫ���ǹر�

    def checkEmulator(self,row,column):
        item = self.tableWidget.item(row, column)
        # print(row, column)
        lastState = item.data(QtCore.Qt.UserRole)
        # print("check����",item)
        currentState = item.checkState()
        # print(lastState,currentState)
        if currentState != lastState:
            # print("changed: ")
            if currentState == QtCore.Qt.Checked:
                # print("checked")
                checkEmuList.append(str(row))
                # print(checkEmuList)
            else:
                # print("uncheck��")
                if str(row) in checkEmuList :
                    # print("���Ƴ�ѡ�", str(row))
                    checkEmuList.remove(str(row))
                # print("�Ƴ�ѡ���ģ�",checkEmuList)
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
            self.pushButton_refreshEmulator.setText("�ָ�ˢ��")
            self.refreshEmulator.terminate()
        else:
            self.refreshEmulator.refreshEmulator_signal.connect(self.refreshEmulator_slot)#�󶨲۷���
            self.pushButton_refreshEmulator.setText("��ͣˢ��")
            self.refreshEmulator.start()

    def refreshEmulator_slot(self, ldlist):#���շ����źţ�ld���󷵻ص�ģ�����б�list
        # ���±������
        global checkEmuList
        bakList = copy.deepcopy(checkEmuList)
        # print("bakǰbaklist��",bakList)
        for i in range(len(ldlist)):
            for j in range(len(ldlist[i])):
                self.tableWidget.setItem(i, j + 3, QTableWidgetItem(str(ldlist[i][j])))
        # print("bak��baklist", bakList)
        checkEmuList=bakList
        # print("fresh��",checkEmuList)
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
        index = int(self.listWidget_candidate.currentIndex().row())#��ȡѡ��������
        self.listWidget_selected.addItem(self.listWidget_candidate.item(index).text())#��ѡ����������ӵ���ѡ�����б�
        self.listWidget_candidate.takeItem(self.listWidget_candidate.currentIndex().row())#�ڴ�ѡ�����б���ɾ��ѡ����

    def removeTask(self,Index):
        index = int(self.listWidget_selected.currentIndex().row())#��ȡѡ��������
        self.listWidget_candidate.addItem(self.listWidget_selected.item(index).text())#��ѡ����������ӵ���ѡ�����б�
        self.listWidget_selected.takeItem(self.listWidget_selected.currentIndex().row())#����ѡ�����б���ɾ��ѡ����

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
        path,filter = QFileDialog.getOpenFileName(filter="APK (*.apk)")#�������ļ�·����ɸѡ����
        # print(path,filter)
        self.lineEdit_appPath.setText(path)

    def loadVmdkPath(self):
        path,filter = QFileDialog.getOpenFileName(filter="APK (*.vmdk)")#�������ļ�·����ɸѡ����
        # print(path,filter)
        self.lineEdit_vmdkPath.setText(path)

    def loadVmsPath(self):
        path=QFileDialog.getExistingDirectory(self, "ѡ��ģ����VMSĿ¼")
        self.lineEdit_vmsPath.setText(path)

    def readCfgThread(self,row,col):
        global checkRow
        checkRow = row
        newThread=threading.Thread(target=self.readCfg,args=(row,))
        newThread.start()

    def readCfg(self,row):
        # content = self.tableWidget.item(row, col).text()#ѡ������
        # print("ѡ���У�" + str(row))
        # print("ѡ���У�" + str(col))
        # print('ѡ������:' + content)
        # global checkRow
        # checkRow = row
        # self.ld = ldControl.LdConsole()
        if self.ld.emulatorIsRunning(row):
            para=self.ld.getEmulatorParameter(row)
            # print(para)
            if para!=[]:
                self.lineEdit_IMEI.setText(para[0])   # ģ����IMEI
                self.lineEdit_IMSI.setText(para[1])  # ģ����IMSI
                self.lineEdit_SIM.setText(para[2])  # ģ����SIM
                self.lineEdit_androidID.setText(para[3])   # ģ������׿ID
            else:
                self.textBrowser_log.append('adb�쳣���޷���ȡģ����������Ϣ,����netstat -ano | finder ��5037����ѯռ����Ϣ��ʹ��taskkill /pid pid��������')
                print('adb�쳣���޷���ȡģ����������Ϣ,����netstat -ano | finder ��5037����ѯռ����Ϣ��ʹ��taskkill /pid pid��������')
        else:
            self.textBrowser_log.append('ģ����δ����,�޷���ȡģ��������')
            print('ģ����δ����,�޷���ȡģ��������')

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
            # QMessageBox.information(self, "��ʾ", "ģ����δ���У���������ʱ���Ĳ���")
            self.textBrowser_log.append("ģ����δ���У���������ʱ���Ĳ���")

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
    # չʾ����
    w=MyWindow()
    w.ui.show()
    app.exec()
