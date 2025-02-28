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

# 选中模拟器加入到已选中模拟器列表
checkEmuList = []
# 备份已选中模拟器列表
bakList = []
# 控制台路径
ldconsole_path = ""


# 命令
class LdConsole():

    def run_command(self, command):
        """通用函数，用于执行命令并返回输出"""
        try:
            result = subprocess.check_output(command, shell=True, text=True)
            return result.strip()  # 移除多余的换行符
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败: {command}")
            print(f"错误信息: {e}")
            return None

    def getLdDevicesList(self):
        """获取模拟器列表"""
        command = f'{ldconsole_path} list2'
        cmd_output = self.run_command(command)
        if cmd_output:
            devices = cmd_output.split('\n')
            # 保留每行的前6个字段
            devices = [device.split(",")[:7] for device in devices if device]
            return devices
        return []

    def startEmulator(self, index):
        """启动指定索引的模拟器"""
        command = f'{ldconsole_path} launch --index {index}'
        self.run_command(command)

    def powerBootApp(self, index, packageName):
        """为指定模拟器设置开机自启应用"""
        command = f'{ldconsole_path} launchex --index {index} --packagename {packageName}'
        self.run_command(command)

    def stopEmulator(self, index):
        """停止指定索引的模拟器"""
        command = f'{ldconsole_path} quit --index {index}'
        self.run_command(command)

    def rebootEmulator(self, index):
        """重启指定索引的模拟器"""
        command = f'{ldconsole_path} reboot --index {index}'
        self.run_command(command)

    def refreshEmulator(self):
        """刷新模拟器列表"""
        command = f'{ldconsole_path} list2'
        cmd_output = self.run_command(command)
        if cmd_output:
            devices = cmd_output.split('\n')
            devices = [device.split(",")[2:] for device in devices if device]
            return devices
        return []

    def getEmulatorParameter(self, index):
        """获取指定模拟器的参数"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        emulator_params = []
        for param in params:
            command = f'{ldconsole_path} getprop --index {index} --key {param}'
            result = self.run_command(command)
            if result:
                emulator_params.append(result)
            else:
                break  # 如果任何一个参数无法获取，就终止
            time.sleep(0.1)
        return emulator_params

    def setEmulatorParameter(self, index, newParaList):
        """设置指定模拟器的参数"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        for param, value in zip(params, newParaList):
            command = f'{ldconsole_path} setprop --index {index} --key {param} --value "{value}"'
            self.run_command(command)

    def randomSetEmulatorParameter(self, index):
        """为指定模拟器设置随机参数"""
        params = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        for param in params:
            command = f'{ldconsole_path} setprop --index {index} --key {param} --value "auto"'
            self.run_command(command)

    def emulatorIsRunning(self, index):
        """检查指定模拟器是否正在运行"""
        command = f'{ldconsole_path} isrunning --index {index}'
        cmd_output = self.run_command(command)
        return cmd_output == 'running'

    def runApp(self, index, packageName):
        """启动指定包名的应用"""
        command = f'{ldconsole_path} runapp --index {index} --packagename {packageName}'
        print(command)
        self.run_command(command)

    def killApp(self, index, packageName):
        """停止指定包名的应用"""
        command = f'{ldconsole_path} killapp --index {index} --packagename {packageName}'
        self.run_command(command)

    def installAPP(self, index, filePath):
        """在指定模拟器中安装应用"""
        command = f'{ldconsole_path} installapp --index {index} --filename {filePath}'
        self.run_command(command)

    def appIsRunning(self, index, packageName):
        """检查指定包名的应用是否正在运行"""
        command = f'{ldconsole_path} adb --index {index} --command "shell pidof {packageName}"'
        cmd_output = self.run_command(command)
        return bool(cmd_output)

    def showappList(self, index):
        """列出指定模拟器中的所有应用包名"""
        command = f'{ldconsole_path} adb --index {index} --command "shell pm list packages"'
        cmd_output = self.run_command(command)

    def inputText(self, index, text):
        """在模拟器中输入文本"""
        command = f'{ldconsole_path} action --index {index} --key call.input --value {text}'
        self.run_command(command)

    def sortWnd(self, checkEmuList):
        """排列窗口"""
        command = f'{ldconsole_path} sortWnd'
        self.run_command(command)

    def adjustWindowPosition(self, checkEmuList):
        """调整模拟器窗口位置和大小"""
        try:
            app = Application().connect(path=ldconsole_path)  # 连接已启动的雷电模拟器
            for emulator in checkEmuList:
                hwnd = app.window(title=emulator)
                hwnd.move_window(x=100, y=100, width=800, height=600)
                print(f"模拟器 {int(emulator) + 1} 窗口已调整位置和大小。")
        except Exception as e:
            print(f"调整窗口位置和大小时出错: {e}")

    def startAnJianScript(self, index):
        """启动按键脚本"""
        command = f'{ldconsole_path} action --index {index} --key call.keyboard --value volumedown'
        self.run_command(command)

    def ldShell(self, index, command):
        """在模拟器中执行Shell命令"""
        str_command = f'ld -s {index} {command}'
        self.run_command(str_command)

    def emulatorGlobalSet(self, index, fps, audio, fastplay, cleanmode, resolution, cpu, memory, downcpu):
        """设置模拟器的全局配置"""
        command1 = f'{ldconsole_path} globalsetting --fps {fps} --audio {audio} --fastplay {fastplay} --cleanmode {cleanmode}'
        command2 = f'{ldconsole_path} modify --index {index} --resolution {resolution} --cpu {cpu} --memory {memory}'
        command3 = f'{ldconsole_path} downcpu --index {index} --rate {downcpu}'
        self.run_command(command1)
        self.run_command(command2)
        self.run_command(command3)


# 通用子线程
class WorkerThread(QThread):
    result_signal = pyqtSignal(str)  # 用于发送任务结果

    def __init__(self, task_type, power_boot_app, app_name):
        super().__init__()
        self.task_type = task_type
        self.power_boot_app = power_boot_app
        self.app_name = app_name
        self.ld = LdConsole()

    def run(self):
        try:
            # 遍历checkEmuList，将其中的元素都减1
            # 根据任务类型执行相应的操作
            if self.task_type == 'start_emulator':
                self.start_emulator()
            elif self.task_type == 'stop_emulator':
                self.stopEmulator()
            elif self.task_type == 'reboot_emulator':
                self.rebootEmulator()
            else:
                raise ValueError("Unknown task type")
        except Exception as e:
            self.result_signal.emit(f"任务失败: {str(e)}")

    def start_emulator(self):
        for emulator in checkEmuList:
            try:
                if self.power_boot_app:
                    self.ld.powerBootApp(emulator, self.app_name)
                    self.result_signal.emit(f"模拟器 {int(emulator) + 1} 已启动，并设置开机自启应用。")
                else:
                    self.ld.startEmulator(emulator)
                    self.result_signal.emit(f"模拟器 {int(emulator) + 1} 已启动。未设置开机自启应用。")
                time.sleep(1)
            except Exception as e:
                self.result_signal.emit(f"启动模拟器 {int(emulator) + 1} 时出错: {str(e)}")

    def stopEmulator(self):
        for emulator in checkEmuList:
            self.ld.stopEmulator(emulator)
            self.result_signal.emit(f"模拟器 {int(emulator) + 1} 已停止")

    def rebootEmulator(self):
        for emulator in checkEmuList:
            self.ld.rebootEmulator(emulator)
            self.result_signal.emit(f"模拟器 {int(emulator) + 1} 已重启")

    def refreshEmulator_slot(self, ldlist):  # 接收发射信号，ld对象返回的模拟器列表list
        # 更新表格内容
        global checkEmuList
        bakList = copy.deepcopy(checkEmuList)
        # print("bak前baklist：",bakList)
        for i in range(len(ldlist)):
            for j in range(len(ldlist[i])):
                self.tableWidget.setItem(i, j + 3, QTableWidgetItem(str(ldlist[i][j])))
        # print("bak后：baklist", bakList)
        checkEmuList = bakList
        # print("fresh后：",checkEmuList)
        self.tableWidget.update()


# 1. 创建一个子线程类，处理启动模拟器的操作
class StartEmulatorThread(QThread):
    # 定义一个信号来通知UI线程
    startEmulator_signal = pyqtSignal(str)

    def __init__(self, emulator_list, power_boot_app, app_name):
        super().__init__()
        self.emulator_list = emulator_list
        self.power_boot_app = power_boot_app
        self.app_name = app_name
        self.ld = LdConsole()  # 初始化模拟器控制

    def run(self):
        for emulator in self.emulator_list:
            try:
                if self.power_boot_app:
                    self.ld.powerBootApp(emulator, self.app_name)
                    self.startEmulator_signal.emit(f"模拟器 {int(emulator) + 1} 已启动，并设置开机自启应用。")
                else:
                    self.ld.startEmulator(emulator)
                    self.startEmulator_signal.emit(f"模拟器 {int(emulator) + 1} 已启动。")
                time.sleep(1)
            except Exception as e:
                self.startEmulator_signal.emit(f"启动模拟器 {int(emulator) + 1} 时出错: {str(e)}")


class refreshEmulatorThread(QThread):
    # 声明刷新模拟器的自定义信号，类型为list，内容即ld对象返回的模拟器列表
    refreshEmulator_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.ld = LdConsole()
        self._is_running = False  # 控制线程是否运行的标志

    def run(self):
        self.refreshEmulator_signal.emit()  # 发射模拟器列表信号


# 刷新模拟器更新表格
class updateTableThread(QThread):
    # 声明更新表格内容的信号，传递模拟器列表数据
    updateTable_signal = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.ld = LdConsole()

    def run(self):
        ldlist = self.ld.getLdDevicesList()
        self.updateTable_signal.emit(ldlist)  # 发射更新后的数据


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
                w.textBrowser_log.append("雷电模拟器%s VMDK覆盖完毕" % (checkEmuList[i]))
            except:
                print("VMDK覆盖出错，雷电%s无法读写，请关闭模拟器后再试" % (checkEmuList[i]))
                w.textBrowser_log.append("VMDK覆盖出错，雷电模拟器%s无法读写，请关闭模拟器后再试" % (checkEmuList[i]))

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
                w.textBrowser_log.append("模拟器%s执行shell命令成功" % (checkEmuList[i]))
            else:
                w.textBrowser_log.append("模拟器%s未启动，执行shell命令失败" % (checkEmuList[i]))

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
                w.textBrowser_log.append(f"模拟器{i}正在运行中,全局配置重启后生效")
            else:
                w.textBrowser_log.append(f"模拟器{i}全局配置成功")


class appConsole():
    def __init__(self):
        super().__init__()
        self.ld = LdConsole()
        self.w = MyWindow()

    def startApp(self):
        for i in range(len(checkEmuList)):
            self.ld.runApp(checkEmuList[i], w.lineEdit_appPackageName.text())
        self.w.textBrowser_log.append("APP启动成功")

    def stopApp(self):
        for i in range(len(checkEmuList)):
            self.ld.killApp(checkEmuList[i], w.lineEdit_appPackageName.text())
        self.w.textBrowser_log.append("APP终止成功")

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
                w.textBrowser_log.append("模拟器%s应用更新完成" % (i))
            else:
                w.textBrowser_log.append("模拟器%s未运行，安装失败" % (i))


class FileApkDialogThread(QThread):
    # 定义一个信号，将文件路径传递给主线程
    fileSelected = pyqtSignal(str)

    def run(self):
        # 在子线程中打开文件对话框
        path, _ = QFileDialog.getOpenFileName(None, "选择APK文件", "", "APK Files (*.apk)")

        # 通过信号传递文件路径给主线程
        if path:
            self.fileSelected.emit(path)
        else:
            self.fileSelected.emit("")


class FileExeDialogThread(QThread):
    # 定义一个信号，将文件路径传递给主线程
    fileSelected = pyqtSignal(str)

    def run(self):
        # 在子线程中打开文件对话框
        path, _ = QFileDialog.getOpenFileName(None, "选择EXE文件", "", "APK Files (*.exe)")

        # 通过信号传递文件路径给主线程
        if path:
            self.fileSelected.emit(path)
        else:
            self.fileSelected.emit("")


class DirectoryDialogThread(QThread):
    # 定义一个信号，传递选择的目录路径
    directorySelected = pyqtSignal(str)

    def run(self):
        # 在子线程中打开文件夹选择对话框
        path = QFileDialog.getExistingDirectory(None, "选择模拟器VMS目录")

        # 将选择的路径传递给主线程
        if path:
            self.directorySelected.emit(path)
        else:
            self.directorySelected.emit("")


class FileVmdkDialogThread(QThread):
    # 定义一个信号，将文件路径传递给主线程
    fileSelected = pyqtSignal(str)

    def run(self):
        # 在子线程中打开文件对话框
        path, _ = QFileDialog.getOpenFileName(None, "选择VMDK文件", "", "VMDK Files (*.vmdk)")

        # 通过信号传递文件路径给主线程
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
                self.window.updateTableData()  # 更新表格数据
                self.window.populateTaskList()  # 填充任务列表
                self.finished_signal.emit()  # 任务完成信号
            else:
                self.finished_signal.emit()  # 任务完成信号
                self.window.textBrowser_log.append("请加载正确的ldconsole.exe路径！")
        except Exception as e:
            print(f"加载数据时发生异常: {e}")
            self.window.textBrowser_log.append(f"加载数据时发生异常: {e}")
            self.finished_signal.emit()  # 发射信号，确保UI不会被卡住

class ReadCfgThread(QThread):
    # 定义信号，用于在子线程完成时向主线程发送数据
    finished_signal = pyqtSignal(list)  # 传递参数为list（模拟器参数）

    def __init__(self, ld, checkRow):
        super().__init__()
        self.ld = ld
        self.checkRow = checkRow

    def run(self):
        try:
            if not self.ld.emulatorIsRunning(self.checkRow):
                # 模拟器未运行的错误信息
                error_message = '模拟器未运行，无法获取模拟器参数'
                print(error_message)
                self.finished_signal.emit([])  # 发射空列表表示获取失败
                return

            para = self.ld.getEmulatorParameter(self.checkRow)
            if para:
                # 如果获取到参数，则返回这些参数
                self.finished_signal.emit(para)  # 发射参数列表
            else:
                # 获取参数失败的错误信息
                error_message = ('adb异常，无法获取模拟器参数信息, '
                                 '输入 netstat -ano | find "5037" 查询占用信息， '
                                 '使用 taskkill /pid pid 结束进程')
                print(error_message)
                self.finished_signal.emit([])  # 发射空列表表示获取失败
        except Exception as e:
            # 捕获并记录任何可能的异常
            error_message = f'读取配置时发生异常: {str(e)}'
            print(error_message)
            self.finished_signal.emit([])  # 发射空列表表示获取失败


# 继承QThread来创建处理随机配置的子线程
class RandomCfgThread(QThread):
    finished_signal = pyqtSignal(list)  # 用于将模拟器参数传递给主线程

    def __init__(self, ld, checkRow):
        super().__init__()
        self.ld = ld
        self.checkRow = checkRow

    def run(self):
        try:
            # 设置随机参数
            self.ld.randomSetEmulatorParameter(self.checkRow)

            # 获取模拟器参数
            para = self.ld.getEmulatorParameter(self.checkRow)
            self.finished_signal.emit(para)  # 发射获取到的参数

        except Exception as e:
            # 捕获并记录任何可能的异常
            self.finished_signal.emit([])  # 发射空列表表示获取失败
            print(f"设置随机参数时发生异常: {str(e)}")

class MyWindow(QWidget):
    checkRow = 0

    def __init__(self):
        # 控制按钮的状态切换
        self.sum = 0
        super().__init__()
        self.ld = LdConsole()
        self.ini_ui()
        # 创建并启动子线程加载数据
        self.load_data_thread = LoadDataThread(self)
        self.load_data_thread.finished_signal.connect(self.on_load_data_finished)
        self.load_data_thread.start()

    def ini_ui(self):
        ui_file = self.resource_path("UI.ui")
        self.ui = uic.loadUi(ui_file)

        # 提取控件
        self.tableWidget = self.ui.tableWidget
        self.listWidget_candidate = self.ui.listWidget_candidate
        self.listWidget_selected = self.ui.listWidget_selected
        self.textBrowser_log = self.ui.textBrowser_log

        # 启动模拟器按钮
        self.pushButton_startEmulator = self.ui.pushButton_startEmulator
        # 关闭模拟器按钮
        self.pushButton_stopEmulator = self.ui.pushButton_stopEmulator
        # 重启模拟器按钮
        self.pushButton_rebootEmulator = self.ui.pushButton_rebootEmulator
        # 刷新模拟器按钮
        self.pushButton_refreshEmulator = self.ui.pushButton_refreshEmulator
        # 全选模拟器按钮
        self.pushButton_seleteAll = self.ui.pushButton_seleteAll
        # 取消全选模拟器按钮
        self.pushButton_deselectAll = self.ui.pushButton_deselectAll
        # 排列窗口按钮
        self.pushButton_sortWnd = self.ui.pushButton_sortWnd
        # 更新应用按钮
        self.pushButton_updateApp = self.ui.pushButton_updateApp
        # 重置vmdk按钮
        self.pushButton_reSetVmdk = self.ui.pushButton_reSetVmdk
        # 保存界面配置按钮
        self.pushButton_saveDefaultCfg = self.ui.pushButton_saveDefaultCfg
        # 发送shell
        self.pushButton_sendShell = self.ui.pushButton_sendShell
        self.pushButton_executeGlobalSet = self.ui.pushButton_executeGlobalSet

        # 加载ldconsole.exe路径
        self.pushButton_loadLdconsolePath = self.ui.pushButton_loadLdconsolePath
        # ldconsole.exe路径
        self.ldconsole_appPath = self.ui.ldconsole_appPath
        # 加载app路径按钮
        self.pushButton_loadAppPath = self.ui.pushButton_loadAppPath
        # 模拟器路径
        self.lineEdit_appPath = self.ui.lineEdit_appPath
        # 加载vmdk路径按钮
        self.pushButton_loadVmdkPath = self.ui.pushButton_loadVmdkPath
        # vmdk路径
        self.lineEdit_vmdkPath = self.ui.lineEdit_vmdkPath
        # 加载vms路径按钮
        self.pushButton_loadVmsPath = self.ui.pushButton_loadVmsPath
        # vms路径
        self.lineEdit_vmsPath = self.ui.lineEdit_vmsPath

        # 任务设置控件
        self.pushButton_addAllTask = self.ui.pushButton_addAllTask  # 全选任务按钮
        self.pushButton_removeAllTask = self.ui.pushButton_removeAllTask  # 全选任务按钮

        # 随机配置按钮
        self.pushButton_randomCfg = self.ui.pushButton_randomCfg
        # 读取配置按钮
        self.pushButton_saveCfg = self.ui.pushButton_saveCfg
        # 模拟器IMEI
        self.lineEdit_IMEI = self.ui.lineEdit_IMEI
        # 模拟器IMSI
        self.lineEdit_IMSI = self.ui.lineEdit_IMSI
        # 模拟器SIM
        self.lineEdit_SIM = self.ui.lineEdit_SIM
        # 模拟器安卓ID
        self.lineEdit_androidID = self.ui.lineEdit_androidID

        # 启动APP按钮
        self.pushButton_startApp = self.ui.pushButton_startApp
        # 终止APP按钮
        self.pushButton_stopApp = self.ui.pushButton_stopApp
        # 启动脚本按钮
        self.pushButton_startScript = self.ui.pushButton_startScript
        # 启动脚本按钮
        self.pushButton_stopScript = self.ui.pushButton_stopScript
        # 运行脚本按钮
        self.pushButton_suspendScript = self.ui.pushButton_suspendScript
        # 暂停脚本按钮
        self.pushButton_recoveryScript = self.ui.pushButton_recoveryScript

        # 开机自启APP
        self.checkBox_powerBootApp = self.ui.checkBox_powerBootApp
        # 开机自启APP包名
        self.lineEdit_powerBootAppName = self.ui.lineEdit_powerBootAppName
        # 脚本包名
        self.lineEdit_scriptPackageName = self.ui.lineEdit_scriptPackageName
        # app包名
        self.lineEdit_appPackageName = self.ui.lineEdit_appPackageName
        # shell命令
        self.lineEdit_shellCommand = self.ui.lineEdit_shellCommand

        # 全局配置控件
        self.lineEdit_CPU = self.ui.lineEdit_CPU
        self.lineEdit_memory = self.ui.lineEdit_memory
        self.lineEdit_FPS = self.ui.lineEdit_FPS
        self.lineEdit_DownCPU = self.ui.lineEdit_DownCPU
        self.lineEdit_resolution = self.ui.lineEdit_resolution
        self.checkBox_fastPlay = self.ui.checkBox_fastPlay
        self.checkBox_audio = self.ui.checkBox_audio
        self.checkBox_cleanMode = self.ui.checkBox_cleanMode

        # 设置tableWigdit格式
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑
        self.tableWidget.setShowGrid(True)  # 显示网格
        self.tableWidget.verticalHeader().setVisible(False)  # False隐藏表头
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)  # 选择整行
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # 表头自适应列宽

        # 绑定信号与槽函数
        # 读取表格参数
        self.tableWidget.cellPressed.connect(self.readCfgThread)
        # table复选框变化事件
        self.tableWidget.cellChanged.connect(self.checkEmulator)
        # list点击事件
        self.listWidget_candidate.itemDoubleClicked.connect(self.addTask)
        # list点击事件
        self.listWidget_selected.itemDoubleClicked.connect(self.removeTask)
        self.pushButton_loadLdconsolePath.clicked.connect(self.loadLdconsolePath)
        self.pushButton_loadAppPath.clicked.connect(self.loadAppPath)
        self.pushButton_loadVmdkPath.clicked.connect(self.loadVmdkPath)
        self.pushButton_loadVmsPath.clicked.connect(self.loadVmsPath)

        self.pushButton_startEmulator.clicked.connect(self.handle_button_click)
        self.pushButton_stopEmulator.clicked.connect(self.handle_button_click)
        self.pushButton_rebootEmulator.clicked.connect(self.handle_button_click)
        # 刷新模拟器
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
        # self.login_status_signal.connect(self.login_status)#绑定自定义槽函数

    def on_load_data_finished(self):
        self.textBrowser_log.append("数据加载完成")
        # 加载配置数据
        self.readDefaultCfg()

    def populateTaskList(self):
        """将任务列表添加到候选任务列表中"""
        taskList = ["任务0", "任务1", "任务2", "任务3", "任务4"]
        for task in taskList:
            self.listWidget_candidate.addItem(task)

    def updateTableData(self):
        # 获取模拟器设备列表
        ldlist = self.ld.getLdDevicesList()
        # 定义表头数据
        headers = ['选中', "索引", "标题", "顶层窗口句柄", "绑定窗口句柄", "是否进入安卓", '进程PID', "VBOXPID"]
        # 设置表格的列数和行数
        self.tableWidget.setColumnCount(len(headers))
        self.tableWidget.setRowCount(len(ldlist))

        # 设置表头
        self.tableWidget.setHorizontalHeaderLabels(headers)

        # 准备要显示的表格数据
        table_data = []
        for i in range(len(ldlist)):
            row_data = []

            # 创建“选中”列
            item = QTableWidgetItem()
            item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            item.setData(QtCore.Qt.UserRole, item.checkState())
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # 水平和垂直居中
            row_data.append(item)

            # 添加“索引”列，索引从 1 开始
            ldlist[i][0] = int(ldlist[i][0]) + 1
            # 填充其他列数据
            for j in range(len(ldlist[i])):
                value = str(ldlist[i][j])

                # 2 和 3 列如果是 0 则显示 "无"
                if j == 2 or j == 3:
                    value = "无" if ldlist[i][j] == "0" else value

                # 5 和 6 列如果是 -1 则显示 "无"
                if j == 5 or j == 6:
                    value = "无" if ldlist[i][j] == "-1" else value
                if j == 4:
                    print(ldlist[i][j])
                    value = "是" if ldlist[i][j] == "1" else "否"
                # 将转换后的值加入到行数据
                row_data.append(QTableWidgetItem(value))

            # 将行数据添加到表格
            table_data.append(row_data)
        # 批量更新表格
        for row_idx, row_data in enumerate(table_data):
            for col_idx, item in enumerate(row_data):
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # 水平和垂直居中
                self.tableWidget.setItem(row_idx, col_idx, item)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def handle_button_click(self):
        # 获取被点击的按钮
        button = self.sender()
        # 启动APP
        power_boot_app = self.checkBox_powerBootApp.isChecked()
        # 启动的包名
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

        # 创建并启动子线程来处理该任务
        self.worker_thread = WorkerThread(task_type, power_boot_app, app_name)
        # 连接子线程的信号以更新日志
        self.worker_thread.result_signal.connect(self.updateLog)
        # 启动子线程
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
        io.close()  # 不要忘记关闭
        self.textBrowser_log.append("保存全局默认配置成功")

    def checkEmulator(self, row, column):
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
                if str(row) in checkEmuList:
                    # print("待移除选项：", str(row))
                    checkEmuList.remove(str(row))
                # print("移除选项后的：",checkEmuList)
            item.setData(QtCore.Qt.UserRole, currentState)

    def startEmulator(self):
        # self.emuCon=emuConsole()
        # newThread=threading.Thread(target=self.emuCon.startEmulator)
        # newThread.start()
        # 获取选中的模拟器
        emulator_list = checkEmuList
        # 启动APP
        power_boot_app = self.checkBox_powerBootApp.isChecked()
        # 启动的包名
        app_name = self.lineEdit_powerBootAppName.text()

        # 创建并启动子线程
        self.startEmulator_thread = StartEmulatorThread(emulator_list, power_boot_app, app_name)

        # 连接信号与槽
        self.startEmulator_thread.startEmulator_signal.connect(self.updateLog)  # 更新日志
        self.startEmulator_thread.start()

    def updateLog(self, message):
        # 在UI线程中更新日志
        self.textBrowser_log.append(message)

    def refreshEmulator_slot(self):
        self.updateTableThread = updateTableThread()
        self.updateTableThread.updateTable_signal.connect(self.updateTable_slot)
        self.updateTableThread.start()

    def updateTable_slot(self, table_data):
        global checkEmuList
        # 检查 table_data 是否为空
        if not table_data:
            self.textBrowser_log.append("表格数据为空！")
            return

        self.tableWidget.blockSignals(True)
        try:
            # 设置表格的行数和列数
            num_rows = len(table_data)
            num_cols = len(table_data[0]) + 1  # 增加一列用于"选中"列
            # 如果表格行数或列数变化了，更新行列数
            if self.tableWidget.rowCount() != num_rows or self.tableWidget.columnCount() != num_cols:
                self.tableWidget.setRowCount(num_rows)
                self.tableWidget.setColumnCount(num_cols)

            # 更新表格内容
            print(table_data)
            for i in range(num_rows):
                for j in range(len(table_data[i])):
                    try:
                        if j == 0:  # 索引列，+1
                            value = str(int(table_data[i][j]) + 1)
                        elif j == 4:  # 列4 (是否进入安卓)，替换为"是"和"否"
                            value = "是" if table_data[i][j] == "1" else "否"
                        elif j == 2 or j == 3:  # 列2和列3 (绑定窗口句柄、顶层窗口句柄)，0显示“无”
                            value = "无" if table_data[i][j] == "0" else str(table_data[i][j])
                        elif j == 5 or j == 6:  # 列5和列6 (进程PID、VBOXPID)，-1显示“无”
                            value = "无" if table_data[i][j] == "-1" else str(table_data[i][j])
                        else:
                            value = str(table_data[i][j])
                        # 创建表格项
                        table_item = QTableWidgetItem(value)
                        self.tableWidget.setItem(i, j + 1, table_item)  # 填充表格项（加1是因为第0列是"选中"列）

                    except Exception as e:
                        print(f"在设置表格项时发生异常: {e}")

            # 更新模拟器选择列表
            checkEmuList = []
        except Exception as e:
            print(f"更新表格内容时发生异常: {e}")

        finally:
            # 启用信号处理，允许后续更新触发
            self.tableWidget.blockSignals(False)
            self.removeSelectionColumn()
        # 强制更新表格
        self.tableWidget.update()

        self.textBrowser_log.append("更新模拟器数据成功")

    def removeSelectionColumn(self):
        # 获取表格的行数
        num_rows = self.tableWidget.rowCount()
        num_cols = self.tableWidget.columnCount()

        # 遍历每一行，移除第一列的选择框
        for i in range(num_rows):
            item = self.tableWidget.item(i, 0)

            if item:
                # 设置该单元格为不可选的状态
                item.setCheckState(QtCore.Qt.Unchecked)  # 取消选择状态
                item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # 水平和垂直居中
                self.tableWidget.setItem(i, 0, item)

        # 遍历每一列，设置所有列居中显示
        for i in range(num_rows):
            for j in range(1, num_cols):  # 从第一列（索引0）开始，到最后一列
                item = self.tableWidget.item(i, j)
                if item:
                    item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)  # 水平和垂直居中
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
        index = int(self.listWidget_candidate.currentIndex().row())  # 获取选中行索引
        self.listWidget_selected.addItem(self.listWidget_candidate.item(index).text())  # 将选中行内容添加到已选任务列表
        self.listWidget_candidate.takeItem(self.listWidget_candidate.currentIndex().row())  # 在待选任务列表中删除选中行

    def removeTask(self, Index):
        index = int(self.listWidget_selected.currentIndex().row())  # 获取选中行索引
        self.listWidget_candidate.addItem(self.listWidget_selected.item(index).text())  # 将选中行内容添加到待选任务列表
        self.listWidget_selected.takeItem(self.listWidget_selected.currentIndex().row())  # 在已选任务列表中删除选中行

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
        # 创建并启动子线程来打开文件选择对话框
        self.dialogThread = FileExeDialogThread()

        # 连接子线程完成文件选择后的信号
        self.dialogThread.fileSelected.connect(self.updateLdconsolePath)
        self.dialogThread.start()

    def updateLdconsolePath(self, path):
        global ldconsole_path
        # 更新UI，设置文件路径到lineEdit控件
        if path:
            print(f"选择的EXE文件路径: {path}")
            ldconsole_path = path
            print(ldconsole_path)
            self.ldconsole_appPath.setText(path)
        else:
            print("没有选择文件")

    def loadAppPath(self):
        # 创建并启动子线程来打开文件选择对话框
        self.dialogThread = FileApkDialogThread()

        # 连接子线程完成文件选择后的信号
        self.dialogThread.fileSelected.connect(self.updateAppPath)
        self.dialogThread.start()

    def updateAppPath(self, path):
        # 更新UI，设置文件路径到lineEdit控件
        if path:
            print(f"选择的APK文件路径: {path}")
            self.lineEdit_appPath.setText(path)
        else:
            print("没有选择文件")

    def loadVmdkPath(self):
        # 创建并启动子线程来打开文件选择对话框
        self.dialogThread = FileVmdkDialogThread()

        # 连接子线程完成文件选择后的信号
        self.dialogThread.fileSelected.connect(self.updateVmdkPath)
        self.dialogThread.start()

    def updateVmdkPath(self, path):
        # 更新UI，设置文件路径到lineEdit控件
        if path:
            print(f"选择的VMDK文件路径: {path}")
            self.lineEdit_vmdkPath.setText(path)
        else:
            print("没有选择文件")

    def loadVmsPath(self):
        # 创建并启动子线程来打开文件夹选择对话框
        self.dialogThread = DirectoryDialogThread()

        # 连接子线程完成文件夹选择后的信号
        self.dialogThread.directorySelected.connect(self.updateVmsPath)
        self.dialogThread.start()

    def updateVmsPath(self, path):
        # 更新UI，设置选择的目录路径到lineEdit控件
        if path:
            print(f"选择的VMS目录路径: {path}")
            self.lineEdit_vmsPath.setText(path)
        else:
            print("没有选择文件夹")

    def readCfgThread(self, row, col):
        global  checkRow
        checkRow=row
        # 创建并启动子线程来读取模拟器配置
        self.read_cfg_thread = ReadCfgThread(self.ld, checkRow)
        self.read_cfg_thread.finished_signal.connect(self.updateCfg)  # 信号连接到槽函数
        self.read_cfg_thread.start()

    def updateCfg(self, para):
        if para:
            # 如果获取到参数，则更新界面
            self.textBrowser_log.append(f'点击{self.checkRow + 1}行成功，成功获取模拟器参数，详情请查看参数配置界面')
            # 设置获取到的模拟器参数
            self.lineEdit_IMEI.setText(para[0])  # 模拟器IMEI
            self.lineEdit_IMSI.setText(para[1])  # 模拟器IMSI
            self.lineEdit_SIM.setText(para[2])  # 模拟器SIM
            self.lineEdit_androidID.setText(para[3])  # 模拟器安卓ID
        else:
            # 获取参数失败的错误信息
            error_message = ('adb异常，无法获取模拟器参数信息, '
                             '输入 netstat -ano | find "5037" 查询占用信息， '
                             '使用 taskkill /pid pid 结束进程')
            self.textBrowser_log.append(error_message)

    def readCfg(self):
        global checkRow
        try:
            if not self.ld.emulatorIsRunning(checkRow):
                # 模拟器未运行的错误信息
                self.textBrowser_log.append('模拟器未运行，无法获取模拟器参数')
                print('模拟器未运行，无法获取模拟器参数')
                return

            para = self.ld.getEmulatorParameter(checkRow)
            print(para)
            if para:
                # 如果获取到参数，则更新界面
                self.textBrowser_log.append(f'点击{checkRow + 1}行成功，成功获取模拟器参数，详情请查看参数配置界面')

                # 设置获取到的模拟器参数
                self.lineEdit_IMEI.setText(para[0])  # 模拟器IMEI
                self.lineEdit_IMSI.setText(para[1])  # 模拟器IMSI
                self.lineEdit_SIM.setText(para[2])  # 模拟器SIM
                self.lineEdit_androidID.setText(para[3])  # 模拟器安卓ID
            else:
                # 获取参数失败的错误信息
                error_message = ('adb异常，无法获取模拟器参数信息, '
                                 '输入 netstat -ano | find "5037" 查询占用信息， '
                                 '使用 taskkill /pid pid 结束进程')
                self.textBrowser_log.append(error_message)
                print(error_message)
        except Exception as e:
            # 捕获并记录任何可能的异常
            self.textBrowser_log.append(f'读取配置时发生异常: {str(e)}')
            print(f'读取配置时发生异常: {str(e)}')

    # 随机参数
    def randomCfg(self):
        global checkRow
        # 创建并启动子线程来设置随机参数
        self.random_cfg_thread = RandomCfgThread(self.ld, checkRow)
        self.random_cfg_thread.finished_signal.connect(self.updateCfg)  # 连接信号到更新配置函数
        self.random_cfg_thread.start()
        self.textBrowser_log.append('设置随机参数成功')

    def saveCfg(self):
        global checkRow
        paraList = []
        if self.ld.emulatorIsRunning(checkRow):
            paraList.append(self.lineEdit_IMEI.text())
            paraList.append(self.lineEdit_IMSI.text())
            paraList.append(self.lineEdit_SIM.text())
            paraList.append(self.lineEdit_androidID.text())
            self.ld.setEmulatorParameter(checkRow, paraList)
            self.textBrowser_log.append("模拟器参数修改完成，请在运行时更改参数")
        else:
            self.textBrowser_log.append("模拟器未运行，请在运行时更改参数")

    def sortWnd(self):
        self.textBrowser_log.append("模拟器排列窗口成功")
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
    # 展示窗口
    w = MyWindow()
    w.ui.show()
    app.exec()
