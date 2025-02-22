import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
LdConsole_path = r"E:\tools\leidian\LDPlayer9\ldconsole.exe"

class LdConsole:

    def getLdDevicesList(self):
        """ 获取模拟器列表 """
        print('获取模拟器列表')
        str = f'{LdConsole_path} list2'
        cmd = os.popen(str).read()
        devices = [line.split(",") for line in cmd.split('\n') if line]
        print(devices)
        return devices

    def startEmulator(self, index):
        """ 启动指定索引的模拟器 """
        str = f'{LdConsole_path} launch --index {index}'
        os.popen(str).read()

    def powerBootApp(self, index, packageName):
        """ 启动指定模拟器中的应用（开机自启） """
        str = f'{LdConsole_path} launchex --index {index} --packagename {packageName}'
        os.popen(str).read()

    def stopEmulator(self, index):
        """ 停止指定索引的模拟器 """
        str = f'{LdConsole_path} quit --index {index}'
        os.popen(str).read()

    def rebootEmulator(self, index):
        """ 重启指定索引的模拟器 """
        str = f'{LdConsole_path} reboot --index {index}'
        os.popen(str).read()

    def refreshEmulator(self):
        """ 刷新模拟器列表 """
        str = f'{LdConsole_path} list2'
        cmd = os.popen(str).read()
        devices = [line.split(",")[2:] for line in cmd.split('\n') if line]
        return devices

    def getEmulatorParameter(self, index):
        """ 获取指定模拟器的参数（如IMEI、IMSI等） """
        paraList = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        emulator_params = []
        for param in paraList:
            str = f'{LdConsole_path} getprop --index {index} --key {param}'
            cmd = os.popen(str).read().split('\n')[0]
            if 'adb server is out of date' in cmd:
                print('5037端口被占用，无法执行adb相关功能')
                break
            emulator_params.append(cmd)
            time.sleep(0.1)
        return emulator_params

    def setEmulatorParameter(self, index, newParaList):
        """ 设置指定模拟器的参数 """
        paraList = ['"phone.imei"', '"phone.imsi"', '"phone.simserial"', '"phone.androidid"']
        for i in range(len(paraList)):
            str = f'{LdConsole_path} setprop --index {index} --key {paraList[i]} --value "{newParaList[i]}"'
            os.popen(str).read()

    def emulatorIsRunning(self, index):
        """ 检查模拟器是否正在运行 """
        str = f'{LdConsole_path} isrunning --index {index}'
        cmd = os.popen(str).read()
        return cmd == 'running'

    def runApp(self, index, packageName):
        """ 在模拟器中运行指定的应用 """
        str = f'{LdConsole_path} runapp --index {index} --packagename {packageName}'
        os.popen(str).read()

    def killApp(self, index, packageName):
        """ 在模拟器中停止指定的应用 """
        str = f'{LdConsole_path} killapp --index {index} --packagename {packageName}'
        os.popen(str).read()

    def installAPP(self, index, filePath):
        """ 在指定模拟器中安装APK """
        str = f'{LdConsole_path} installapp --index {index} --filename {filePath}'
        os.popen(str).read()

    def appIsRunning(self, index, packageName):
        """ 检查指定应用是否在模拟器中运行 """
        str = f'{LdConsole_path} adb --index {index} --command "shell pidof {packageName}"'
        cmd = os.popen(str).read()
        return cmd != ''

    def inputText(self, index, text):
        """ 模拟器中输入文本 """
        str = f'{LdConsole_path} action --index {index} --key call.input --value {text}'
        os.popen(str).read()

    def sortWnd(self):
        """ 排列模拟器窗口 """
        str = f'{LdConsole_path} sortWnd'
        os.popen(str).read()\

    def startAnJianScript(self, index):
        """ 启动指定模拟器中的按键脚本 """
        str = f'{LdConsole_path} action --index {index} --key call.keyboard --value volumedown'
        os.popen(str).read()

    def ldShell(self, index, command):
        """ 在指定模拟器中执行shell命令 """
        str = f'ld -s {index} {command}'
        os.popen(str).read()

    def emulatorGlobalSet(self, index, fps, audio, fastplay, cleanmode, resolution, cpu, memory, downcpu):
        """ 配置模拟器的全局设置（如帧率、音频、清洁模式等） """
        str1 = f'{LdConsole_path} globalsetting --fps {fps} --audio {audio} --fastplay {fastplay} --cleanmode {cleanmode}'
        str2 = f'{LdConsole_path} modify --index {index} --resolution {resolution} --cpu {cpu} --memory {memory}'
        str3 = f'{LdConsole_path} downcpu --index {index} --rate {downcpu}'
        os.popen(str1).read()
        os.popen(str2).read()
        os.popen(str3).read()

# 示例使用
if __name__ == '__main__':
    ld = LdConsole()
    devices = ld.getLdDevicesList()
    print(devices)
