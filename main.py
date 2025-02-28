# coding=gbk
import configparser
import copy
import os
import subprocess
import sys
import threading
import time
from shutil import copyfile

from PyQt5 import uic, QtCore
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QFileDialog, \
    QAbstractItemView, QHeaderView
from pywinauto import Application

# ѡ��ģ�������뵽��ѡ��ģ�����б�
checkEmuList = []
# ������ѡ��ģ�����б�
bakList = []
# ����̨·��
ldconsole_path = ""


# ����
class LdConsole():

    def run_command(self, command):
        """ͨ�ú���������ִ������������"""
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()  # �Ƴ�����Ļ��з�
        except subprocess.CalledProcessError as e:
            print(f"����ִ��ʧ��: {command}")
            print(f"������Ϣ: {e}")
            return None

    def getLdDevicesList(self):
        """��ȡģ�����б�"""
        command = f'{ldconsole_path} list2'
        cmd_output = self.run_command(command)
        if cmd_output:
            devices = cmd_output.split('\n')
            # ����ÿ�е�ǰ6���ֶ�
            devices = [device.split(",")[:7] for device in devices if device]
            return devices
        return []

    def startEmulator(self, index):
        """����ָ��������ģ����"""
        command = f'{ldconsole_path} launch --index {index}'
        self.run_command(command)

    def powerBootApp(self, index, packageName):
        """Ϊָ��ģ�������ÿ�������Ӧ��"""
        command = f'{ldconsole_path} launchex --index {index} --packagename {packageName}'
        self.run_command(command)

    def stopEmulator(self, index):
        """ָֹͣ��������ģ����"""
        command = f'{ldconsole_path} quit --index {index}'
        self.run_command(command)

    def rebootEmulator(self, index):
        """����ָ��������ģ����"""
        command = f'{ldconsole_path} reboot --index {index}'
        self.run_command(command)

    def refreshEmulator(self):
        """ˢ��ģ�����б�"""
        command = f'{ldconsole_path} list2'
        cmd_output = self.run_command(command)
        if cmd_output:
            devices = cmd_output.split('\n')
            devices = [device.split(",")[2:] for device in devices if device]
            return devices
        return []

    def getEmulatorParameter(self, index):
        """��ȡָ��ģ�����Ĳ���"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        emulator_params = []
        for param in params:
            command = f'{ldconsole_path} getprop --index {index} --key {param}'
            result = self.run_command(command)
            if result:
                emulator_params.append(result)
            else:
                break  # ����κ�һ�������޷���ȡ������ֹ
            time.sleep(0.1)
        return emulator_params

    def setEmulatorParameter(self, index, newParaList):
        """����ָ��ģ�����Ĳ���"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        for param, value in zip(params, newParaList):
            command = f'{ldconsole_path} setprop --index {index} --key {param} --value "{value}"'
            self.run_command(command)

    def randomSetEmulatorParameter(self, index):
        """Ϊָ��ģ���������������"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        for param in params:
            command = f'{ldconsole_path} setprop --index {index} --key {param} --value "auto"'
            self.run_command(command)

    def emulatorIsRunning(self, index):
        """���ָ��ģ�����Ƿ���������"""
        command = f'{ldconsole_path} isrunning --index {index}'
        cmd_output = self.run_command(command)
        return cmd_output == 'running'

    def runApp(self, index, packageName):
        """����ָ��������Ӧ��"""
        command = f'{ldconsole_path} runapp --index {index} --packagename {packageName}'
        print(command)
        self.run_command(command)

    def killApp(self, index, packageName):
        """ָֹͣ��������Ӧ��"""
        command = f'{ldconsole_path} killapp --index {index} --packagename {packageName}'
        self.run_command(command)

    def installAPP(self, index, filePath):
        """��ָ��ģ�����а�װӦ��"""
        command = f'{ldconsole_path} installapp --index {index} --filename {filePath}'
        self.run_command(command)

    def appIsRunning(self, index, packageName):
        """���ָ��������Ӧ���Ƿ���������"""
        command = f'{ldconsole_path} adb --index {index} --command "shell pidof {packageName}"'
        cmd_output = self.run_command(command)
        return bool(cmd_output)

    def showappList(self, index):
        """�г�ָ��ģ�����е�����Ӧ�ð���"""
        command = f'{ldconsole_path} adb --index {index} --command "shell pm list packages"'
        cmd_output = self.run_command(command)

    def inputText(self, index, text):
        """��ģ�����������ı�"""
        command = f'{ldconsole_path} action --index {index} --key call.input --value {text}'
        self.run_command(command)

    def sortWnd(self, checkEmuList):
        """���д���"""
        command = f'{ldconsole_path} sortWnd'
        self.run_command(command)

    def adjustWindowPosition(self, checkEmuList):
        """����ģ��������λ�úʹ�С"""
        try:
            app = Application().connect(path=ldconsole_path)  # �������������׵�ģ����
            for emulator in checkEmuList:
                hwnd = app.window(title=emulator)
                hwnd.move_window(x=100, y=100, width=800, height=600)
                print(f"ģ���� {int(emulator) + 1} �����ѵ���λ�úʹ�С��")
        except Exception as e:
            print(f"��������λ�úʹ�Сʱ����: {e}")

    def startAnJianScript(self, index):
        """���������ű�"""
        command = f'{ldconsole_path} action --index {index} --key call.keyboard --value volumedown'
        self.run_command(command)

    def ldShell(self, index, command):
        """��ģ������ִ��Shell����"""
        str_command = f'ld -s {index} {command}'
        self.run_command(str_command)

    def emulatorGlobalSet(self, index, fps, audio, fastplay, cleanmode, resolution, cpu, memory, downcpu):
        """����ģ������ȫ������"""
        command1 = f'{ldconsole_path} globalsetting --fps {fps} --audio {audio} --fastplay {fastplay} --cleanmode {cleanmode}'
        command2 = f'{ldconsole_path} modify --index {index} --resolution {resolution} --cpu {cpu} --memory {memory}'
        command3 = f'{ldconsole_path} downcpu --index {index} --rate {downcpu}'
        self.run_command(command1)
        self.run_command(command2)
        self.run_command(command3)


# ͨ�����߳�
class WorkerThread(QThread):
    result_signal = pyqtSignal(str)  # ���ڷ���������

    def __init__(self, task_type, power_boot_app, app_name):
        super().__init__()
        self.task_type = task_type
        self.power_boot_app = power_boot_app
        self.app_name = app_name
        self.ld = LdConsole()

    def run(self):
        try:
            # ����checkEmuList�������е�Ԫ�ض���1
            # ������������ִ����Ӧ�Ĳ���
            if self.task_type == 'start_emulator':
                self.start_emulator()
            elif self.task_type == 'stop_emulator':
                self.stopEmulator()
            elif self.task_type == 'reboot_emulator':
                self.rebootEmulator()
            else:
                raise ValueError("Unknown task type")
        except Exception as e:
            self.result_signal.emit(f"����ʧ��: {str(e)}")

    def start_emulator(self):
        for emulator in checkEmuList:
            try:
                if self.power_boot_app:
                    self.ld.powerBootApp(emulator, self.app_name)
                    self.result_signal.emit(f"ģ���� {int(emulator) + 1} �������������ÿ�������Ӧ�á�")
                else:
                    self.ld.startEmulator(emulator)
                    self.result_signal.emit(f"ģ���� {int(emulator) + 1} ��������δ���ÿ�������Ӧ�á�")
                time.sleep(1)
            except Exception as e:
                self.result_signal.emit(f"����ģ���� {int(emulator) + 1} ʱ����: {str(e)}")

    def stopEmulator(self):
        for emulator in checkEmuList:
            self.ld.stopEmulator(emulator)
            self.result_signal.emit(f"ģ���� {int(emulator) + 1} ��ֹͣ")

    def rebootEmulator(self):
        for emulator in checkEmuList:
            self.ld.rebootEmulator(emulator)
            self.result_signal.emit(f"ģ���� {int(emulator) + 1} ������")

    def refreshEmulator_slot(self, ldlist):  # ���շ����źţ�ld���󷵻ص�ģ�����б�list
        # ���±������
        global checkEmuList
        bakList = copy.deepcopy(checkEmuList)
        # print("bakǰbaklist��",bakList)
        for i in range(len(ldlist)):
            for j in range(len(ldlist[i])):
                self.tableWidget.setItem(i, j + 3, QTableWidgetItem(str(ldlist[i][j])))
        # print("bak��baklist", bakList)
        checkEmuList = bakList
        # print("fresh��",checkEmuList)
        self.tableWidget.update()


# 1. ����һ�����߳��࣬��������ģ�����Ĳ���
class StartEmulatorThread(QThread):
    # ����һ���ź���֪ͨUI�߳�
    startEmulator_signal = pyqtSignal(str)

    def __init__(self, emulator_list, power_boot_app, app_name):
        super().__init__()
        self.emulator_list = emulator_list
        self.power_boot_app = power_boot_app
        self.app_name = app_name
        self.ld = LdConsole()  # ��ʼ��ģ��������

    def run(self):
        for emulator in self.emulator_list:
            try:
                if self.power_boot_app:
                    self.ld.powerBootApp(emulator, self.app_name)
                    self.startEmulator_signal.emit(f"ģ���� {int(emulator) + 1} �������������ÿ�������Ӧ�á�")
                else:
                    self.ld.startEmulator(emulator)
                    self.startEmulator_signal.emit(f"ģ���� {int(emulator) + 1} ��������")
                time.sleep(1)
            except Exception as e:
                self.startEmulator_signal.emit(f"����ģ���� {int(emulator) + 1} ʱ����: {str(e)}")


class refreshEmulatorThread(QThread):
    # ����ˢ��ģ�������Զ����źţ�����Ϊlist�����ݼ�ld���󷵻ص�ģ�����б�
    refreshEmulator_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.ld = LdConsole()
        self._is_running = False  # �����߳��Ƿ����еı�־

    def run(self):
        self.refreshEmulator_signal.emit()  # ����ģ�����б��ź�


# ˢ��ģ�������±��
class updateTableThread(QThread):
    # �������±�����ݵ��źţ�����ģ�����б�����
    updateTable_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.ld = LdConsole()

    def run(self):
        ldlist = self.ld.getLdDevicesList()
        self.updateTable_signal.emit(ldlist)  # ������º������


class emuConsole():
    def __init__(self):
        self.ld = LdConsole()
        self.w = MyWindow()

    def copyVmdk(self):
        source_file = w.lineEdit_vmdkPath.text()
        destination_filepath = w.lineEdit_vmsPath.text()
        for i in range(len(checkEmuList)):
            destination_file = destination_filepath + '\\leidian' + checkEmuList[i] + '\system.vmdk'
            # print(destination_file)
            try:
                copyfile(source_file, destination_file)
                w.textBrowser_log.append("�׵�ģ����%s VMDK�������" % (checkEmuList[i]))
            except:
                print("VMDK���ǳ����׵�%s�޷���д����ر�ģ����������" % (checkEmuList[i]))
                w.textBrowser_log.append("VMDK���ǳ����׵�ģ����%s�޷���д����ر�ģ����������" % (checkEmuList[i]))

    def startEmulator(self):
        for i in range(len(checkEmuList)):
            if w.checkBox_powerBootApp.isChecked():
                self.ld.powerBootApp(checkEmuList[i], w.lineEdit_powerBootAppName.text())
            else:
                self.ld.startEmulator(checkEmuList[i])
            time.sleep(1)

    def sendShell(self):
        for i in range(len(checkEmuList)):
            if self.ld.emulatorIsRunning(i):
                self.ld.ldShell(checkEmuList[i], w.lineEdit_shellCommand.text())
                w.textBrowser_log.append("ģ����%sִ��shell����ɹ�" % (checkEmuList[i]))
            else:
                w.textBrowser_log.append("ģ����%sδ������ִ��shell����ʧ��" % (checkEmuList[i]))

    def executeGlobalSet(self):
        CPU = w.lineEdit_CPU.text()
        memory = w.lineEdit_memory.text()
        FPS = w.lineEdit_FPS.text()
        downCPU = w.lineEdit_DownCPU.text()
        resolution = w.lineEdit_resolution.text()
        if w.checkBox_fastPlay.isChecked() == True:
            fastPlay = 1
        else:
            fastPlay = 0
        if w.checkBox_audio.isChecked() == True:
            audio = 1
        else:
            audio = 0
        if w.checkBox_cleanMode.isChecked() == True:
            cleanMode = 1
        else:
            cleanMode = 0

        for i in range(len(self.ld.getLdDevicesList())):
            self.ld.emulatorGlobalSet(i, FPS, audio, fastPlay, cleanMode, resolution, CPU, memory, downCPU)
            if self.ld.emulatorIsRunning(i) == True:
                w.textBrowser_log.append(f"ģ����{i}����������,ȫ��������������Ч")
            else:
                w.textBrowser_log.append(f"ģ����{i}ȫ�����óɹ�")


class appConsole():
    def __init__(self):
        super().__init__()
        self.ld = LdConsole()
        self.w = MyWindow()

    def startApp(self):
        for i in range(len(checkEmuList)):
            self.ld.runApp(checkEmuList[i], w.lineEdit_appPackageName.text())
        self.w.textBrowser_log.append("APP�����ɹ�")

    def stopApp(self):
        for i in range(len(checkEmuList)):
            self.ld.killApp(checkEmuList[i], w.lineEdit_appPackageName.text())
        self.w.textBrowser_log.append("APP��ֹ�ɹ�")

    def startScript(self):
        for i in range(len(checkEmuList)):
            self.ld.runApp(checkEmuList[i], w.lineEdit_scriptPackageName.text())

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
                self.ld.installAPP(i, w.lineEdit_appPath.text())
                time.sleep(5)
                w.textBrowser_log.append("ģ����%sӦ�ø������" % (i))
            else:
                w.textBrowser_log.append("ģ����%sδ���У���װʧ��" % (i))


class FileApkDialogThread(QThread):
    # ����һ���źţ����ļ�·�����ݸ����߳�
    fileSelected = pyqtSignal(str)

    def run(self):
        # �����߳��д��ļ��Ի���
        path, _ = QFileDialog.getOpenFileName(None, "ѡ��APK�ļ�", "", "APK Files (*.apk)")

        # ͨ���źŴ����ļ�·�������߳�
        if path:
            self.fileSelected.emit(path)
        else:
            self.fileSelected.emit("")


class FileExeDialogThread(QThread):
    # ����һ���źţ����ļ�·�����ݸ����߳�
    fileSelected = pyqtSignal(str)

    def run(self):
        # �����߳��д��ļ��Ի���
        path, _ = QFileDialog.getOpenFileName(None, "ѡ��EXE�ļ�", "", "APK Files (*.exe)")

        # ͨ���źŴ����ļ�·�������߳�
        if path:
            self.fileSelected.emit(path)
        else:
            self.fileSelected.emit("")


class DirectoryDialogThread(QThread):
    # ����һ���źţ�����ѡ���Ŀ¼·��
    directorySelected = pyqtSignal(str)

    def run(self):
        # �����߳��д��ļ���ѡ��Ի���
        path = QFileDialog.getExistingDirectory(None, "ѡ��ģ����VMSĿ¼")

        # ��ѡ���·�����ݸ����߳�
        if path:
            self.directorySelected.emit(path)
        else:
            self.directorySelected.emit("")


class FileVmdkDialogThread(QThread):
    # ����һ���źţ����ļ�·�����ݸ����߳�
    fileSelected = pyqtSignal(str)

    def run(self):
        # �����߳��д��ļ��Ի���
        path, _ = QFileDialog.getOpenFileName(None, "ѡ��VMDK�ļ�", "", "VMDK Files (*.vmdk)")

        # ͨ���źŴ����ļ�·�������߳�
        if path:
            self.fileSelected.emit(path)
        else:
            self.fileSelected.emit("")


class LoadDataThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, window):
        super().__init__()
        self.window = window

    def run(self):
        try:
            global ldconsole_path
            config = configparser.ConfigParser()
            config.read(self.window.resource_path('conf.ini'))
            ldconsole_path = config.get('filePath', 'ldconsolePath')
            if ldconsole_path.lower().endswith("ldconsole.exe"):
                self.window.updateTableData()  # ���±������
                self.window.populateTaskList()  # ��������б�
                self.finished_signal.emit()  # ��������ź�
            else:
                self.finished_signal.emit()  # ��������ź�
                self.window.textBrowser_log.append("�������ȷ��ldconsole.exe·����")
        except Exception as e:
            print(f"��������ʱ�����쳣: {e}")
            self.window.textBrowser_log.append(f"��������ʱ�����쳣: {e}")
            self.finished_signal.emit()  # �����źţ�ȷ��UI���ᱻ��ס

class ReadCfgThread(QThread):
    # �����źţ����������߳����ʱ�����̷߳�������
    finished_signal = pyqtSignal(list)  # ���ݲ���Ϊlist��ģ����������

    def __init__(self, ld, checkRow):
        super().__init__()
        self.ld = ld
        self.checkRow = checkRow

    def run(self):
        try:
            if not self.ld.emulatorIsRunning(self.checkRow):
                # ģ����δ���еĴ�����Ϣ
                error_message = 'ģ����δ���У��޷���ȡģ��������'
                print(error_message)
                self.finished_signal.emit([])  # ������б��ʾ��ȡʧ��
                return

            para = self.ld.getEmulatorParameter(self.checkRow)
            if para:
                # �����ȡ���������򷵻���Щ����
                self.finished_signal.emit(para)  # ��������б�
            else:
                # ��ȡ����ʧ�ܵĴ�����Ϣ
                error_message = ('adb�쳣���޷���ȡģ����������Ϣ, '
                                 '���� netstat -ano | find "5037" ��ѯռ����Ϣ�� '
                                 'ʹ�� taskkill /pid pid ��������')
                print(error_message)
                self.finished_signal.emit([])  # ������б��ʾ��ȡʧ��
        except Exception as e:
            # ���񲢼�¼�κο��ܵ��쳣
            error_message = f'��ȡ����ʱ�����쳣: {str(e)}'
            print(error_message)
            self.finished_signal.emit([])  # ������б��ʾ��ȡʧ��


# �̳�QThread����������������õ����߳�
class RandomCfgThread(QThread):
    finished_signal = pyqtSignal(list)  # ���ڽ�ģ�����������ݸ����߳�

    def __init__(self, ld, checkRow):
        super().__init__()
        self.ld = ld
        self.checkRow = checkRow

    def run(self):
        try:
            # �����������
            self.ld.randomSetEmulatorParameter(self.checkRow)

            # ��ȡģ��������
            para = self.ld.getEmulatorParameter(self.checkRow)
            self.finished_signal.emit(para)  # �����ȡ���Ĳ���

        except Exception as e:
            # ���񲢼�¼�κο��ܵ��쳣
            self.finished_signal.emit([])  # ������б��ʾ��ȡʧ��
            print(f"�����������ʱ�����쳣: {str(e)}")

class MyWindow(QWidget):
    checkRow = 0

    def __init__(self):
        # ���ư�ť��״̬�л�
        self.sum = 0
        super().__init__()
        self.ld = LdConsole()
        self.ini_ui()
        # �������������̼߳�������
        self.load_data_thread = LoadDataThread(self)
        self.load_data_thread.finished_signal.connect(self.on_load_data_finished)
        self.load_data_thread.start()

    def ini_ui(self):
        ui_file = self.resource_path("UI.ui")
        self.ui = uic.loadUi(ui_file)

        # ��ȡ�ؼ�
        self.tableWidget = self.ui.tableWidget
        self.listWidget_candidate = self.ui.listWidget_candidate
        self.listWidget_selected = self.ui.listWidget_selected
        self.textBrowser_log = self.ui.textBrowser_log

        # ����ģ������ť
        self.pushButton_startEmulator = self.ui.pushButton_startEmulator
        # �ر�ģ������ť
        self.pushButton_stopEmulator = self.ui.pushButton_stopEmulator
        # ����ģ������ť
        self.pushButton_rebootEmulator = self.ui.pushButton_rebootEmulator
        # ˢ��ģ������ť
        self.pushButton_refreshEmulator = self.ui.pushButton_refreshEmulator
        # ȫѡģ������ť
        self.pushButton_seleteAll = self.ui.pushButton_seleteAll
        # ȡ��ȫѡģ������ť
        self.pushButton_deselectAll = self.ui.pushButton_deselectAll
        # ���д��ڰ�ť
        self.pushButton_sortWnd = self.ui.pushButton_sortWnd
        # ����Ӧ�ð�ť
        self.pushButton_updateApp = self.ui.pushButton_updateApp
        # ����vmdk��ť
        self.pushButton_reSetVmdk = self.ui.pushButton_reSetVmdk
        # ����������ð�ť
        self.pushButton_saveDefaultCfg = self.ui.pushButton_saveDefaultCfg
        # ����shell
        self.pushButton_sendShell = self.ui.pushButton_sendShell
        self.pushButton_executeGlobalSet = self.ui.pushButton_executeGlobalSet

        # ����ldconsole.exe·��
        self.pushButton_loadLdconsolePath = self.ui.pushButton_loadLdconsolePath
        # ldconsole.exe·��
        self.ldconsole_appPath = self.ui.ldconsole_appPath
        # ����app·����ť
        self.pushButton_loadAppPath = self.ui.pushButton_loadAppPath
        # ģ����·��
        self.lineEdit_appPath = self.ui.lineEdit_appPath
        # ����vmdk·����ť
        self.pushButton_loadVmdkPath = self.ui.pushButton_loadVmdkPath
        # vmdk·��
        self.lineEdit_vmdkPath = self.ui.lineEdit_vmdkPath
        # ����vms·����ť
        self.pushButton_loadVmsPath = self.ui.pushButton_loadVmsPath
        # vms·��
        self.lineEdit_vmsPath = self.ui.lineEdit_vmsPath

        # �������ÿؼ�
        self.pushButton_addAllTask = self.ui.pushButton_addAllTask  # ȫѡ����ť
        self.pushButton_removeAllTask = self.ui.pushButton_removeAllTask  # ȫѡ����ť

        # ������ð�ť
        self.pushButton_randomCfg = self.ui.pushButton_randomCfg
        # ��ȡ���ð�ť
        self.pushButton_saveCfg = self.ui.pushButton_saveCfg
        # ģ����IMEI
        self.lineEdit_IMEI = self.ui.lineEdit_IMEI
        # ģ����IMSI
        self.lineEdit_IMSI = self.ui.lineEdit_IMSI
        # ģ����SIM
        self.lineEdit_SIM = self.ui.lineEdit_SIM
        # ģ������׿ID
        self.lineEdit_androidID = self.ui.lineEdit_androidID

        # ����APP��ť
        self.pushButton_startApp = self.ui.pushButton_startApp
        # ��ֹAPP��ť
        self.pushButton_stopApp = self.ui.pushButton_stopApp
        # �����ű���ť
        self.pushButton_startScript = self.ui.pushButton_startScript
        # �����ű���ť
        self.pushButton_stopScript = self.ui.pushButton_stopScript
        # ���нű���ť
        self.pushButton_suspendScript = self.ui.pushButton_suspendScript
        # ��ͣ�ű���ť
        self.pushButton_recoveryScript = self.ui.pushButton_recoveryScript

        # ��������APP
        self.checkBox_powerBootApp = self.ui.checkBox_powerBootApp
        # ��������APP����
        self.lineEdit_powerBootAppName = self.ui.lineEdit_powerBootAppName
        # �ű�����
        self.lineEdit_scriptPackageName = self.ui.lineEdit_scriptPackageName
        # app����
        self.lineEdit_appPackageName = self.ui.lineEdit_appPackageName
        # shell����
        self.lineEdit_shellCommand = self.ui.lineEdit_shellCommand

        # ȫ�����ÿؼ�
        self.lineEdit_CPU = self.ui.lineEdit_CPU
        self.lineEdit_memory = self.ui.lineEdit_memory
        self.lineEdit_FPS = self.ui.lineEdit_FPS
        self.lineEdit_DownCPU = self.ui.lineEdit_DownCPU
        self.lineEdit_resolution = self.ui.lineEdit_resolution
        self.checkBox_fastPlay = self.ui.checkBox_fastPlay
        self.checkBox_audio = self.ui.checkBox_audio
        self.checkBox_cleanMode = self.ui.checkBox_cleanMode

        # ����tableWigdit��ʽ
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # ��ֹ�༭
        self.tableWidget.setShowGrid(True)  # ��ʾ����
        self.tableWidget.verticalHeader().setVisible(False)  # False���ر�ͷ
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # ѡ������
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # ��ͷ����Ӧ�п�

        # ���ź���ۺ���
        # ��ȡ������
        self.tableWidget.cellPressed.connect(self.readCfgThread)
        # table��ѡ��仯�¼�
        self.tableWidget.cellChanged.connect(self.checkEmulator)
        # list����¼�
        self.listWidget_candidate.itemDoubleClicked.connect(self.addTask)
        # list����¼�
        self.listWidget_selected.itemDoubleClicked.connect(self.removeTask)
        self.pushButton_loadLdconsolePath.clicked.connect(self.loadLdconsolePath)
        self.pushButton_loadAppPath.clicked.connect(self.loadAppPath)
        self.pushButton_loadVmdkPath.clicked.connect(self.loadVmdkPath)
        self.pushButton_loadVmsPath.clicked.connect(self.loadVmsPath)

        self.pushButton_startEmulator.clicked.connect(self.handle_button_click)
        self.pushButton_stopEmulator.clicked.connect(self.handle_button_click)
        self.pushButton_rebootEmulator.clicked.connect(self.handle_button_click)
        # ˢ��ģ����
        self.pushButton_refreshEmulator.clicked.connect(self.refreshEmulator_slot)
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

    def on_load_data_finished(self):
        self.textBrowser_log.append("���ݼ������")
        # ������������
        self.readDefaultCfg()

    def populateTaskList(self):
        """�������б���ӵ���ѡ�����б���"""
        taskList = ["����0", "����1", "����2", "����3", "����4"]
        for task in taskList:
            self.listWidget_candidate.addItem(task)

    def updateTableData(self):
        # ��ȡģ�����豸�б�
        ldlist = self.ld.getLdDevicesList()
        # �����ͷ����
        headers = ['ѡ��', "����", "����", "���㴰�ھ��", "�󶨴��ھ��", "�Ƿ���밲׿", '����PID', "VBOXPID"]
        # ���ñ�������������
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setRowCount(len(ldlist))

        # ���ñ�ͷ
        self.tableWidget.setHorizontalHeaderLabels(headers)

        # ׼��Ҫ��ʾ�ı������
        table_data = []
        for i in range(len(ldlist)):
            row_data = []

            # ������ѡ�С���
            item = QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setData(QtCore.Qt.UserRole, item.checkState())
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # ˮƽ�ʹ�ֱ����
            row_data.append(item)

            # ��ӡ��������У������� 1 ��ʼ
            ldlist[i][0] = int(ldlist[i][0]) + 1
            # �������������
            for j in range(len(ldlist[i])):
                value = str(ldlist[i][j])

                # 2 �� 3 ������� 0 ����ʾ "��"
                if j == 2 or j == 3:
                    value = "��" if ldlist[i][j] == "0" else value

                # 5 �� 6 ������� -1 ����ʾ "��"
                if j == 5 or j == 6:
                    value = "��" if ldlist[i][j] == "-1" else value
                if j == 4:
                    print(ldlist[i][j])
                    value = "��" if ldlist[i][j] == "1" else "��"
                # ��ת�����ֵ���뵽������
                row_data.append(QTableWidgetItem(value))

            # ����������ӵ����
            table_data.append(row_data)
        # �������±��
        for row_idx, row_data in enumerate(table_data):
            for col_idx, item in enumerate(row_data):
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # ˮƽ�ʹ�ֱ����
                self.tableWidget.setItem(row_idx, col_idx, item)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def handle_button_click(self):
        # ��ȡ������İ�ť
        button = self.sender()
        # ����APP
        power_boot_app = self.checkBox_powerBootApp.isChecked()
        # �����İ���
        app_name = self.lineEdit_powerBootAppName.text()
        if button == self.pushButton_startEmulator:
            task_type = 'start_emulator'
        elif button == self.pushButton_stopEmulator:
            task_type = 'stop_emulator'
        elif button == self.pushButton_rebootEmulator:
            task_type = 'reboot_emulator'
        elif button == self.pushButton_refreshEmulator:
            task_type = 'refresh_emulator'
        else:
            return

        # �������������߳������������
        self.worker_thread = WorkerThread(task_type, power_boot_app, app_name)
        # �������̵߳��ź��Ը�����־
        self.worker_thread.result_signal.connect(self.updateLog)
        # �������߳�
        self.worker_thread.start()

    def readDefaultCfg(self):
        global ldconsole_path
        config = configparser.ConfigParser()
        config.read(self.resource_path('conf.ini'))
        self.lineEdit_powerBootAppName.setText(config.get('appName', 'powerBootApp'))
        self.lineEdit_scriptPackageName.setText(config.get('appName', 'scriptPackageName'))
        self.lineEdit_appPackageName.setText(config.get('appName', 'APPPackageName'))
        self.lineEdit_appPath.setText(config.get('filePath', 'updateAppPath'))
        self.ldconsole_appPath.setText(config.get('filePath', 'ldconsolePath'))
        ldconsole_path = config.get('filePath', 'ldconsolePath')
        self.lineEdit_vmdkPath.setText(config.get('filePath', 'VMDKPath'))
        self.lineEdit_vmsPath.setText(config.get('filePath', 'VMSPath'))
        self.lineEdit_shellCommand.setText(config.get('shell', 'command'))
        self.lineEdit_CPU.setText(config.get('globalSetting', 'CPU'))
        self.lineEdit_memory.setText(config.get('globalSetting', 'memory'))
        self.lineEdit_FPS.setText(config.get('globalSetting', 'FPS'))
        self.lineEdit_DownCPU.setText(config.get('globalSetting', 'downCPU'))
        self.lineEdit_resolution.setText(config.get('globalSetting', 'resolution'))
        if config.getboolean('checkbox', 'ispowerBootApp') == True:
            self.checkBox_powerBootApp.setChecked(True)
        else:
            self.checkBox_powerBootApp.setChecked(False)

        if config.getboolean('globalSetting', 'fastPlay') == True:
            self.checkBox_fastPlay.setChecked(True)
        else:
            self.checkBox_fastPlay.setChecked(False)

        if config.getboolean('globalSetting', 'audio') == True:
            self.checkBox_audio.setChecked(True)
        else:
            self.checkBox_audio.setChecked(False)

        if config.getboolean('globalSetting', 'cleanMode') == True:
            self.checkBox_cleanMode.setChecked(True)
        else:
            self.checkBox_cleanMode.setChecked(False)

    def saveDefaultCfg(self):
        config = configparser.ConfigParser()
        config.read('conf.ini', encoding='GB18030')
        config.set('appName', 'powerBootApp', self.lineEdit_powerBootAppName.text())
        config.set('appName', 'scriptPackageName', self.lineEdit_scriptPackageName.text())
        config.set('appName', 'APPPackageName', self.lineEdit_appPackageName.text())
        config.set('filePath', 'ldconsolePath', self.ldconsole_appPath.text())
        config.set('filePath', 'updateAppPath', self.lineEdit_appPath.text())
        config.set('filePath', 'VMDKPath', self.lineEdit_vmdkPath.text())
        config.set('filePath', 'VMSPath', self.lineEdit_vmsPath.text())
        config.set('globalSetting', 'CPU', self.lineEdit_CPU.text())
        config.set('globalSetting', 'memory', self.lineEdit_memory.text())
        config.set('globalSetting', 'FPS', self.lineEdit_FPS.text())
        config.set('globalSetting', 'downCPU', self.lineEdit_DownCPU.text())
        config.set('globalSetting', 'resolution', self.lineEdit_resolution.text())

        if self.checkBox_powerBootApp.isChecked() == True:
            config.set('checkbox', 'ispowerBootApp', 'True')
        else:
            config.set('checkbox', 'ispowerBootApp', 'False')

        if self.checkBox_fastPlay.isChecked() == True:
            config.set('globalSetting', 'fastPlay', 'True')
        else:
            config.set('globalSetting', 'fastPlay', 'False')

        if self.checkBox_audio.isChecked() == True:
            config.set('globalSetting', 'audio', 'True')
        else:
            config.set('globalSetting', 'audio', 'False')

        if self.checkBox_cleanMode.isChecked() == True:
            config.set('globalSetting', 'cleanMode', 'True')
        else:
            config.set('globalSetting', 'cleanMode', 'False')

        io = open('conf.ini', 'w')
        config.write(io)
        io.close()  # ��Ҫ���ǹر�
        self.textBrowser_log.append("����ȫ��Ĭ�����óɹ�")

    def checkEmulator(self, row, column):
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
                if str(row) in checkEmuList:
                    # print("���Ƴ�ѡ�", str(row))
                    checkEmuList.remove(str(row))
                # print("�Ƴ�ѡ���ģ�",checkEmuList)
            item.setData(QtCore.Qt.UserRole, currentState)

    def startEmulator(self):
        # self.emuCon=emuConsole()
        # newThread=threading.Thread(target=self.emuCon.startEmulator)
        # newThread.start()
        # ��ȡѡ�е�ģ����
        emulator_list = checkEmuList
        # ����APP
        power_boot_app = self.checkBox_powerBootApp.isChecked()
        # �����İ���
        app_name = self.lineEdit_powerBootAppName.text()

        # �������������߳�
        self.startEmulator_thread = StartEmulatorThread(emulator_list, power_boot_app, app_name)

        # �����ź����
        self.startEmulator_thread.startEmulator_signal.connect(self.updateLog)  # ������־
        self.startEmulator_thread.start()

    def updateLog(self, message):
        # ��UI�߳��и�����־
        self.textBrowser_log.append(message)

    def refreshEmulator_slot(self):
        self.updateTableThread = updateTableThread()
        self.updateTableThread.updateTable_signal.connect(self.updateTable_slot)
        self.updateTableThread.start()

    def updateTable_slot(self, table_data):
        global checkEmuList
        # ��� table_data �Ƿ�Ϊ��
        if not table_data:
            self.textBrowser_log.append("�������Ϊ�գ�")
            return

        self.tableWidget.blockSignals(True)
        try:
            # ���ñ�������������
            num_rows = len(table_data)
            num_cols = len(table_data[0]) + 1  # ����һ������"ѡ��"��
            # �����������������仯�ˣ�����������
            if self.tableWidget.rowCount() != num_rows or self.tableWidget.columnCount() != num_cols:
                self.tableWidget.setRowCount(num_rows)
                self.tableWidget.setColumnCount(num_cols)

            # ���±������
            print(table_data)
            for i in range(num_rows):
                for j in range(len(table_data[i])):
                    try:
                        if j == 0:  # �����У�+1
                            value = str(int(table_data[i][j]) + 1)
                        elif j == 4:  # ��4 (�Ƿ���밲׿)���滻Ϊ"��"��"��"
                            value = "��" if table_data[i][j] == "1" else "��"
                        elif j == 2 or j == 3:  # ��2����3 (�󶨴��ھ�������㴰�ھ��)��0��ʾ���ޡ�
                            value = "��" if table_data[i][j] == "0" else str(table_data[i][j])
                        elif j == 5 or j == 6:  # ��5����6 (����PID��VBOXPID)��-1��ʾ���ޡ�
                            value = "��" if table_data[i][j] == "-1" else str(table_data[i][j])
                        else:
                            value = str(table_data[i][j])
                        # ���������
                        table_item = QTableWidgetItem(value)
                        self.tableWidget.setItem(i, j + 1, table_item)  # ��������1����Ϊ��0����"ѡ��"�У�

                    except Exception as e:
                        print(f"�����ñ����ʱ�����쳣: {e}")

            # ����ģ����ѡ���б�
            checkEmuList = []
        except Exception as e:
            print(f"���±������ʱ�����쳣: {e}")

        finally:
            # �����źŴ�������������´���
            self.tableWidget.blockSignals(False)
            self.removeSelectionColumn()
        # ǿ�Ƹ��±��
        self.tableWidget.update()

        self.textBrowser_log.append("����ģ�������ݳɹ�")

    def removeSelectionColumn(self):
        # ��ȡ��������
        num_rows = self.tableWidget.rowCount()
        num_cols = self.tableWidget.columnCount()

        # ����ÿһ�У��Ƴ���һ�е�ѡ���
        for i in range(num_rows):
            item = self.tableWidget.item(i, 0)

            if item:
                # ���øõ�Ԫ��Ϊ����ѡ��״̬
                item.setCheckState(QtCore.Qt.Unchecked)  # ȡ��ѡ��״̬
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # ˮƽ�ʹ�ֱ����
                self.tableWidget.setItem(i, 0, item)

        # ����ÿһ�У����������о�����ʾ
        for i in range(num_rows):
            for j in range(1, num_cols):  # �ӵ�һ�У�����0����ʼ�������һ��
                item = self.tableWidget.item(i, j)
                if item:
                    item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # ˮƽ�ʹ�ֱ����
                    self.tableWidget.setItem(i, j, item)

    def seleteAll(self):
        global checkEmuList
        # self.ld = LdConsole()
        ldlist = self.ld.getLdDevicesList()
        self.tableWidget.setRowCount(len(ldlist))
        for i in range(len(ldlist)):
            self.item = QTableWidgetItem()
            self.item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.item.setCheckState(QtCore.Qt.Checked)  # Unchecked
            self.item.setData(QtCore.Qt.UserRole, self.item.checkState())
            self.tableWidget.setItem(i, 0, self.item)
            checkEmuList.append(str(i))
        checkEmuList = list(set(checkEmuList))
        # print(checkEmuList)

    def deselectAll(self):
        global checkEmuList
        # self.ld = LdConsole()
        list = self.ld.getLdDevicesList()
        self.tableWidget.setRowCount(len(list))
        for i in range(len(list)):
            self.item = QTableWidgetItem()
            self.item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.item.setCheckState(QtCore.Qt.Unchecked)
            self.item.setData(QtCore.Qt.UserRole, self.item.checkState())
            self.tableWidget.setItem(i, 0, self.item)
        checkEmuList = []

    def addTask(self, Index):
        index = int(self.listWidget_candidate.currentIndex().row())  # ��ȡѡ��������
        self.listWidget_selected.addItem(self.listWidget_candidate.item(index).text())  # ��ѡ����������ӵ���ѡ�����б�
        self.listWidget_candidate.takeItem(self.listWidget_candidate.currentIndex().row())  # �ڴ�ѡ�����б���ɾ��ѡ����

    def removeTask(self, Index):
        index = int(self.listWidget_selected.currentIndex().row())  # ��ȡѡ��������
        self.listWidget_candidate.addItem(self.listWidget_selected.item(index).text())  # ��ѡ����������ӵ���ѡ�����б�
        self.listWidget_selected.takeItem(self.listWidget_selected.currentIndex().row())  # ����ѡ�����б���ɾ��ѡ����

    def addAllTask(self, Index):
        for i in range(self.listWidget_candidate.count()):
            print(self.listWidget_candidate.item(i).text())
            self.listWidget_selected.addItem(self.listWidget_candidate.item(i).text())
        self.listWidget_candidate.clear()

    def removeAllTask(self, Index):
        for i in range(self.listWidget_selected.count()):
            print(self.listWidget_selected.item(i).text())
            self.listWidget_candidate.addItem(self.listWidget_selected.item(i).text())
        self.listWidget_selected.clear()

    def loadLdconsolePath(self):
        # �������������߳������ļ�ѡ��Ի���
        self.dialogThread = FileExeDialogThread()

        # �������߳�����ļ�ѡ�����ź�
        self.dialogThread.fileSelected.connect(self.updateLdconsolePath)
        self.dialogThread.start()

    def updateLdconsolePath(self, path):
        global ldconsole_path
        # ����UI�������ļ�·����lineEdit�ؼ�
        if path:
            print(f"ѡ���EXE�ļ�·��: {path}")
            ldconsole_path = path
            print(ldconsole_path)
            self.ldconsole_appPath.setText(path)
        else:
            print("û��ѡ���ļ�")

    def loadAppPath(self):
        # �������������߳������ļ�ѡ��Ի���
        self.dialogThread = FileApkDialogThread()

        # �������߳�����ļ�ѡ�����ź�
        self.dialogThread.fileSelected.connect(self.updateAppPath)
        self.dialogThread.start()

    def updateAppPath(self, path):
        # ����UI�������ļ�·����lineEdit�ؼ�
        if path:
            print(f"ѡ���APK�ļ�·��: {path}")
            self.lineEdit_appPath.setText(path)
        else:
            print("û��ѡ���ļ�")

    def loadVmdkPath(self):
        # �������������߳������ļ�ѡ��Ի���
        self.dialogThread = FileVmdkDialogThread()

        # �������߳�����ļ�ѡ�����ź�
        self.dialogThread.fileSelected.connect(self.updateVmdkPath)
        self.dialogThread.start()

    def updateVmdkPath(self, path):
        # ����UI�������ļ�·����lineEdit�ؼ�
        if path:
            print(f"ѡ���VMDK�ļ�·��: {path}")
            self.lineEdit_vmdkPath.setText(path)
        else:
            print("û��ѡ���ļ�")

    def loadVmsPath(self):
        # �������������߳������ļ���ѡ��Ի���
        self.dialogThread = DirectoryDialogThread()

        # �������߳�����ļ���ѡ�����ź�
        self.dialogThread.directorySelected.connect(self.updateVmsPath)
        self.dialogThread.start()

    def updateVmsPath(self, path):
        # ����UI������ѡ���Ŀ¼·����lineEdit�ؼ�
        if path:
            print(f"ѡ���VMSĿ¼·��: {path}")
            self.lineEdit_vmsPath.setText(path)
        else:
            print("û��ѡ���ļ���")

    def readCfgThread(self, row, col):
        global  checkRow
        checkRow=row
        # �������������߳�����ȡģ��������
        self.read_cfg_thread = ReadCfgThread(self.ld, checkRow)
        self.read_cfg_thread.finished_signal.connect(self.updateCfg)  # �ź����ӵ��ۺ���
        self.read_cfg_thread.start()

    def updateCfg(self, para):
        if para:
            # �����ȡ������������½���
            self.textBrowser_log.append(f'���{self.checkRow + 1}�гɹ����ɹ���ȡģ����������������鿴�������ý���')
            # ���û�ȡ����ģ��������
            self.lineEdit_IMEI.setText(para[0])  # ģ����IMEI
            self.lineEdit_IMSI.setText(para[1])  # ģ����IMSI
            self.lineEdit_SIM.setText(para[2])  # ģ����SIM
            self.lineEdit_androidID.setText(para[3])  # ģ������׿ID
        else:
            # ��ȡ����ʧ�ܵĴ�����Ϣ
            error_message = ('adb�쳣���޷���ȡģ����������Ϣ, '
                             '���� netstat -ano | find "5037" ��ѯռ����Ϣ�� '
                             'ʹ�� taskkill /pid pid ��������')
            self.textBrowser_log.append(error_message)

    def readCfg(self):
        global checkRow
        try:
            if not self.ld.emulatorIsRunning(checkRow):
                # ģ����δ���еĴ�����Ϣ
                self.textBrowser_log.append('ģ����δ���У��޷���ȡģ��������')
                print('ģ����δ���У��޷���ȡģ��������')
                return

            para = self.ld.getEmulatorParameter(checkRow)
            print(para)
            if para:
                # �����ȡ������������½���
                self.textBrowser_log.append(f'���{checkRow + 1}�гɹ����ɹ���ȡģ����������������鿴�������ý���')

                # ���û�ȡ����ģ��������
                self.lineEdit_IMEI.setText(para[0])  # ģ����IMEI
                self.lineEdit_IMSI.setText(para[1])  # ģ����IMSI
                self.lineEdit_SIM.setText(para[2])  # ģ����SIM
                self.lineEdit_androidID.setText(para[3])  # ģ������׿ID
            else:
                # ��ȡ����ʧ�ܵĴ�����Ϣ
                error_message = ('adb�쳣���޷���ȡģ����������Ϣ, '
                                 '���� netstat -ano | find "5037" ��ѯռ����Ϣ�� '
                                 'ʹ�� taskkill /pid pid ��������')
                self.textBrowser_log.append(error_message)
                print(error_message)
        except Exception as e:
            # ���񲢼�¼�κο��ܵ��쳣
            self.textBrowser_log.append(f'��ȡ����ʱ�����쳣: {str(e)}')
            print(f'��ȡ����ʱ�����쳣: {str(e)}')

    # �������
    def randomCfg(self):
        global checkRow
        # �������������߳��������������
        self.random_cfg_thread = RandomCfgThread(self.ld, checkRow)
        self.random_cfg_thread.finished_signal.connect(self.updateCfg)  # �����źŵ��������ú���
        self.random_cfg_thread.start()
        self.textBrowser_log.append('������������ɹ�')

    def saveCfg(self):
        global checkRow
        paraList = []
        if self.ld.emulatorIsRunning(checkRow):
            paraList.append(self.lineEdit_IMEI.text())
            paraList.append(self.lineEdit_IMSI.text())
            paraList.append(self.lineEdit_SIM.text())
            paraList.append(self.lineEdit_androidID.text())
            self.ld.setEmulatorParameter(checkRow, paraList)
            self.textBrowser_log.append("ģ���������޸���ɣ���������ʱ���Ĳ���")
        else:
            self.textBrowser_log.append("ģ����δ���У���������ʱ���Ĳ���")

    def sortWnd(self):
        self.textBrowser_log.append("ģ�������д��ڳɹ�")
        self.ld.sortWnd(checkEmuList)

    def updateApp(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.updateApp)
        newThread.start()

    def startAJScript(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.startScript)
        newThread.start()

    def stopAJScript(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.stopScript)
        newThread.start()

    def startApp(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.startApp)
        newThread.start()

    def stopApp(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.stopApp)
        newThread.start()

    def suspendAJScript(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.suspendScript)
        newThread.start()

    def recoveryAJScript(self):
        self.appCon = appConsole()
        newThread = threading.Thread(target=self.appCon.recoveryScript)
        newThread.start()

    def reSetVmdk(self):
        self.emuCon = emuConsole()
        newThread = threading.Thread(target=self.emuCon.copyVmdk)
        newThread.start()

    def sendShell(self):
        self.emuCon = emuConsole()
        newThread = threading.Thread(target=self.emuCon.sendShell)
        newThread.start()

    def executeGlobalSet(self):
        self.emuCon = emuConsole()
        newThread = threading.Thread(target=self.emuCon.executeGlobalSet)
        newThread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # չʾ����
    w = MyWindow()
    w.ui.show()
    app.exec()
