# ftp_client.py
# 这是一个FTP客户端，使用PySide6创建了一个图形化界面，可以连接到FTP服务器，上传和下载文件，实现断点续传功能
# 导入所需的模块
import socket
import os
import sys
import threading
import time
import select
import queue
# 从gui模块导入FTPClientGUI类
from gui import FTPClientGUI

# 定义一些常量
HOST = "127.0.0.1"  # FTP服务器的IP地址，可以修改为其他值
PORT = 8888  # FTP服务器的端口号，可以修改为其他值
BUFFER_SIZE = 1024  # 缓冲区大小，用于接收和发送数据
COMMANDS = ["ls", "cd", "get", "put", "restart", 'login', 'register', "quit"]  # 支持的FTP命令


# 定义一个FTP客户端类
class FTPClient():

    # 初始化方法，接受IP地址和端口号作为参数
    def __init__(self, host, port):
        # 调用父类的初始化方法
        super().__init__()
        # 增加一个属性，用于存储FTP服务器的IP地址
        self.host = host
        # 增加一个属性，用于存储FTP服务器的端口号
        self.port = port
        # 创建一个socket对象，用于和FTP服务器通信
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置socket的超时时间为10秒，如果超过10秒没有收到服务器的响应，就认为连接断开
        self.sock.settimeout(10)
        # 创建一个锁对象，用于同步多个线程的访问
        self.lock = threading.Lock()
        # 创建一个GUI对象，用于创建和布局控件，以及处理一些界面相关的事件
        self.gui = FTPClientGUI()
        # 增加一个属性，用于标记是否已经断开连接
        self.stopped = False
        # 调用创建界面的方法
        self.gui.create_ui(self)
        # 调用初始化数据的方法
        self.init_data()

    # 连接服务器的方法，返回一个布尔值，表示是否连接成功
    def connect_server(self):
        # 尝试连接到FTP服务器
        try:
            self.sock.connect((self.host, self.port))
            # 接收服务器的欢迎消息
            msg = self.sock.recv(BUFFER_SIZE).decode()
            # 在控制台打印欢迎消息
            self.gui.write_output(f"<font color='black'>{msg}</font>")
            # 发送一个ls命令，获取当前目录和文件列表
            self.send_command("ls")
            # 返回True，表示连接成功
            return True
        # 如果发生异常，抛出异常
        except Exception as e:
            self.stopped = True
            self.gui.change_icon('play')
            raise e
            
    # 初始化数据的方法
    def init_data(self):
        # 初始化一些属性，用于存储当前的目录，文件名，文件大小，已传输的字节数等信息
        self.current_dir = ""
        self.filename = ""
        self.filesize = 0
        self.sent = 0
        self.received = 0
        # 增加一个属性，用于存储断点的位置
        self.breakpoint = 0
        # 增加一个属性，用于存储文件的下载位置
        self.download_filename = ''
        # 创建一个队列对象，用于存储主线程发送的文件名
        self.file_queue = queue.Queue()
        # 创建一个队列对象，用于存储注册登录的执行结果
        self.result_queue = queue.Queue()
        # 清空进度条
        self.gui.progress_bar.setValue(0)

    # 发送命令的方法
    def send_command(self, command):
        # 尝试发送命令到服务器
        try:
            # 把命令的内容拼接成一个字符串，用HTML标签设置字体颜色为蓝色
            text = f"<font color='blue'>发送命令：{command}</font>"
            # 调用GUI类的write_output方法，把字符串传递给它
            self.gui.write_output(text)
            # 把命令编码为字节串，发送到服务器
            self.sock.send(command.encode())
            # 初始化响应为空字节串
            response = b""
            # 接收一部分响应
            data = self.sock.recv(BUFFER_SIZE)
            # 循环接收服务器的响应，直到没有数据可读
            while data:
                # 将收到的数据拼接起来
                response += data
                # 检查是否还有数据可读
                readable, _, _ = select.select([self.sock], [], [], 0)
                if readable:
                    # 如果有数据，继续接收
                    data = self.sock.recv(BUFFER_SIZE)
                else:
                    # 如果数据为空，说明接收完毕，跳出循环
                    break
            # 把响应解码为字符串
            response = response.decode()
            # 把响应的内容拼接成一个字符串，用HTML标签设置字体颜色为绿色
            text = f"<font color='green'>接收响应：</font><pre>{response}</pre>"
            # 调用GUI类的write_output方法，把字符串传递给它
            self.gui.write_output(text)
            # 如果无法解码的字节列表不为空，就在控制台打印出来
            # 根据不同的命令，执行不同的操作
            if command == "ls":
                # 如果是ls命令，就更新当前目录和文件列表
                self.update_dir_and_file(response)
            elif command.startswith("cd"):
                # 如果是cd命令，就更新当前目录
                self.update_dir(response)
            elif command.startswith("get"):
                # 如果是get命令，就创建一个子线程，把接收文件的方法作为目标函数，把服务器的响应作为参数
                threading.Thread(target=self.receive_file, args=(response,)).start()
            elif command.startswith("put"):
                # 如果是put命令，就创建一个子线程，把发送文件的方法作为目标函数，把服务器的响应作为参数
                threading.Thread(target=self.send_file, args=(response,)).start()
            elif command.startswith('restart'):
                # 如果是restart命令，就设置断点
                self.restart(response)
            # 如果是login或register命令，表示是登录或注册请求
            elif command.startswith('login') or command.startswith('register'):
                # 返回一个布尔值，表示服务器的响应是否以OK开头，OK表示成功，ERROR表示失败
                return response.startswith('OK')
            elif command == "quit":
                # 如果是quit命令，就关闭socket，退出程序
                self.sock.close()
                sys.exit()
        # 如果发生异常，弹出错误提示框
        except Exception as e:
            self.gui.show_error(str(e))

    # 更新当前目录和文件列表的方法
    def update_dir_and_file(self, response):
        # 调用GUI类的update_dir_and_file方法
        self.gui.update_dir_and_file(response)
        # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
        self.gui.result.emit(True)

    # 更新当前目录的方法
    def update_dir(self, response):
        # 如果响应以OK开头，说明切换目录成功
        if response.startswith("OK"):
            # 把响应的第二部分赋值给当前目录
            self.current_dir = response.split(" ", 1)[1]
            # 把当前目录显示在文本框中
            self.gui.dir_edit.setText(self.current_dir)
            # 发送一个ls命令，更新文件列表
            self.send_command("ls")
            # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
            self.gui.result.emit(True)
        # 否则，说明切换目录失败，弹出错误提示框
        else:
            self.gui.show_error(response)
            # 调用GUI对象的result信号对象的emit方法，传递一个False值，表示当前命令执行失败
            self.gui.result.emit(False)

    # 处理restart命令的方法
    def restart(self, response):
        # 把响应转换为整数，并赋值给断点的位置
        self.breakpoint = int(response)
        # 在控制台打印同步成功的消息
        self.gui.write_output(f"<font color='black'>断点同步成功：{self.breakpoint}</font>")
        # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
        self.gui.result.emit(True)

    # 切换目录的槽函数
    def change_dir(self):
        # 获取文本框中输入的目录
        dir = self.gui.dir_edit.text()
        # 如果目录不为空，就发送一个cd命令，切换到该目录
        if dir:
            self.send_command("cd " + dir)
        # 否则，弹出错误提示框
        else:
            self.gui.show_error("请输入目录")

    # 下载文件的槽函数
    def download_file(self):
        # 获取文本框中输入的文件名
        filename = self.gui.file_edit.text()
        # 如果文件名不为空，就发送一个get命令，下载该文件
        if filename:
            self.send_command("get " + filename)
        # 否则，弹出错误提示框
        else:
            self.gui.show_error("请输入文件名")

    # 上传文件的槽函数
    def upload_file(self):
        # 调用GUI类的select_file方法，获取文件名
        filename = self.gui.select_file()
        # 如果文件名不为空，就发送一个put命令，上传该文件
        if filename:
            self.send_command("put " + filename)
        # 否则，在控制台打印取消上传的消息
        else:
            self.gui.write_output("<font color='red'>取消上传</font>")

    # 退出的槽函数
    def quit(self):
        # 发送一个quit命令，退出程序
        self.send_command("quit")

    # 接收文件的方法
    def receive_file(self, response):
        # 获取锁，防止多个线程同时访问
        self.lock.acquire()
        # 如果响应以OK开头，说明文件存在，可以下载
        if response.startswith("OK"):
            # 把响应分割为三部分，第一部分是OK，第二部分是文件大小，第三部分是文件名
            _, self.filesize, self.filename = response.split(" ", 2)
            # 把文件大小转换为整数
            self.filesize = int(self.filesize)
            # 如果文件名为空
            if not self.download_filename:
                # 发送一个信号给主线程，让主线程弹出文件对话框，并传递文件名
                self.gui.file_dialog_signal.emit(self.filename)
                # 从队列中取出文件名
                self.download_filename = self.file_queue.get()
            self.gui.output_signal.emit(self.download_filename)
            # 如果文件名不为空，就打开该文件，准备写入数据
            if self.download_filename:
                try:
                    # 在开始下载前，把除connect_button外的所有控件设置为不可用
                    self.gui.set_enabled(False)
                    self.gui.connect_button.setEnabled(True)
                    # 记录开始下载的时间
                    start_time = time.time()
                    # 记录开始下载的断点
                    start_breakpoint = self.breakpoint
                    # 以追加模式或写入模式打开文件
                    with open(self.download_filename, 'ab' if self.breakpoint != 0 else 'wb') as f:
                        # 从断点处开始累加已接收的字节数
                        self.received = self.breakpoint
                        # 循环接收数据，直到文件接收完毕
                        while self.received < self.filesize:
                            # 接收数据
                            data = self.sock.recv(BUFFER_SIZE)
                            # 写入数据
                            f.write(data)
                            # 累加已接收的字节数
                            self.received += len(data)
                            # 计算传输进度百分比
                            percent = int(self.received / self.filesize * 100)
                            # 发送进度信号，更新进度条的值
                            self.gui.progress_signal.emit(percent)
                    # 记录结束下载的时间
                    end_time = time.time()
                    # 记录结束下载的断点
                    self.gui.output_signal.emit(self.received)
                    end_breakpoint = self.received
                    # 计算下载用时
                    duration = end_time - start_time
                    # 如果下载用时小于0.01秒，就把它设为0.01秒
                    if duration < 0.01:
                        duration = 0.01
                    # 计算下载数据量
                    received = end_breakpoint - start_breakpoint
                    # 在控制台打印下载完成的消息，包括下载用时、下载数据量和下载速度
                    self.gui.output_signal.emit(f"<font color='purple'>下载完成：{self.filename}</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>在{duration:.2f}秒内下载了{self.format_size(received)}数据</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>下载速度：{received / duration / 1024:.2f}KB/s</font>")
                    # 清除下载文件信息
                    self.filename = ''
                    self.download_filename = ''
                    self.filesize = 0
                    self.received = 0
                    # 将断点同步清零
                    self.clear_breakpoint()
                    # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
                    self.gui.result.emit(True)
                # 如果发生异常，就打印异常信息
                except Exception as e:
                    # 设置中断标志为True
                    self.stopped = True
                    # 发送一个信号给主线程，让主线程修改按钮的图标为继续
                    self.gui.icon_signal.emit('play')
                    # 修改服务器信息
                    self.gui.server_info_signal.emit('已断开连接，点击右下角按钮重连')
                    # 在控制台打印下载异常的内容
                    self.gui.output_signal.emit(f"<font color='red' face='bold'>下载异常：{e}</font>")
                    # 记录结束下载的时间
                    end_time = time.time()
                    # 记录结束下载的断点
                    end_breakpoint = self.received
                    # 计算下载用时
                    duration = end_time - start_time
                    # 如果下载用时小于0.01秒，就把它设为0.01秒
                    if duration < 0.01:
                        duration = 0.01
                    # 计算下载数据量
                    received = end_breakpoint - start_breakpoint
                    # 在控制台打印下载异常的消息，包括下载用时、下载数据量和下载速度
                    self.gui.output_signal.emit(f"<font color='purple'>在{duration:.2f}秒内下载了{self.format_size(received)}数据</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>下载速度：{received / duration / 1024:.2f}KB/s</font>")
                    # 调用GUI对象的result信号对象的emit方法，传递一个False值，表示当前命令执行失败
                    self.gui.result.emit(False)
                # 在结束下载后，把所有控件恢复为可用
                self.gui.set_enabled(True)
            # 否则，如果文件名为空，就丢弃服务器发送的文件内容
            else:
                self.gui.write_output("<font color='black'>正在清空缓冲区...</font>")
                # 在清空缓冲区前，把所有控件设置为不可用
                self.gui.set_enabled(False)
                # 循环接收数据，直到文件接收完毕
                while self.received < self.filesize:
                    # 接收数据
                    data = self.sock.recv(BUFFER_SIZE)
                    # 累加已接收的字节数
                    self.received += len(data)
                    # 计算清空进度百分比
                    percent = int(self.received / self.filesize * 100)
                    # 在GUI对象中，发射信号对象，并传递清空进度的百分比
                    self.gui.clear_signal.emit(percent)
                    # 输出清空进度，使用\r回到行首，覆盖之前的输出
                    # print(f'\r清空进度：{percent}%', end='')
                # 在控制台打印取消下载的消息
                self.gui.write_output(f"<font color='red'>取消下载：{self.filename}</font>")
                # 清除下载文件信息
                self.filename = ''
                self.download_filename = ''
                self.filesize = 0
                self.received = 0
                # 将断点同步清零
                self.clear_breakpoint()
                # 在清空缓冲区后，把所有控件恢复为可用
                self.gui.set_enabled(True)
                # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
                self.gui.result.emit(True)
        # 否则，说明文件不存在，弹出错误提示框
        else:
            # 在子线程中，不再直接调用show_error方法，而是发送一个信号给主线程，并传递错误信息
            # self.gui.show_error(response)
            self.gui.error_signal.emit(response)
            # 调用GUI对象的result信号对象的emit方法，传递一个False值，表示当前命令执行失败
            self.gui.result.emit(False)
        # 释放锁，让其他线程可以访问
        self.lock.release()

    # 发送文件的方法
    def send_file(self, response):
        # 获取锁，防止多个线程同时访问
        self.lock.acquire()
        # 如果响应以OK开头，说明文件可以上传
        if response.startswith("OK"):
            # 把响应分割为两部分，第一部分是OK，第二部分是文件名
            _, self.filename = response.split(" ", 1)
            # 获取文件的大小
            self.filesize = os.path.getsize(self.filename)
            self.gui.output_signal.emit(self.filesize)
            # 发送文件大小
            self.sock.send(str(self.filesize).encode())
            # 初始化已发送的字节数为0
            self.sent = 0
            # 打开文件，准备读取数据
            with open(self.filename, "rb") as f:
                # 增加一个try-except语句，用于捕获异常
                try:
                    # 在开始上传前，把除connect_button外的所有控件设置为不可用
                    self.gui.set_enabled(False)
                    self.gui.connect_button.setEnabled(True)
                    # 记录开始上传的时间
                    start_time = time.time()
                    # 记录开始上传的断点
                    start_breakpoint = self.breakpoint
                    # 如果断点不为0，就从断点处开始读取数据
                    if self.breakpoint != 0:
                        # 移动文件指针到断点处
                        f.seek(self.breakpoint)
                        # 从断点处开始累加已发送的字节数
                        self.sent = self.breakpoint
                    # 循环读取数据，直到文件发送完毕
                    while self.sent < self.filesize:
                        # 读取数据
                        data = f.read(BUFFER_SIZE)
                        # 发送数据
                        self.sock.send(data)
                        # 累加已发送的字节数
                        self.sent += len(data)
                        # 计算传输进度百分比
                        percent = int(self.sent / self.filesize * 100)
                        # 发送进度信号，更新进度条的值
                        self.gui.progress_signal.emit(percent)
                    # 记录结束上传的时间
                    end_time = time.time()
                    # 记录结束上传的断点
                    end_breakpoint = self.sent
                    # 计算上传用时
                    duration = end_time - start_time
                    # 如果上传用时小于0.01秒，就把它设为0.01秒
                    if duration < 0.01:
                        duration = 0.01
                    # 计算上传数据量
                    sent = end_breakpoint - start_breakpoint
                    # 在控制台打印上传完成的消息，包括上传用时、上传数据量和上传速度
                    self.gui.output_signal.emit(f"<font color='purple'>上传完成：{self.filename}</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>在{duration:.2f}秒内上传了{self.format_size(sent)}数据</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>上传速度：{sent / duration / 1024:.2f}KB/s</font>")
                    # 清除上传文件信息
                    self.filename = ''
                    self.filesize = 0
                    self.sent = 0
                    # 将断点同步清零
                    self.clear_breakpoint()
                    # 调用GUI对象的result信号对象的emit方法，传递一个True值，表示当前命令执行成功
                    self.gui.result.emit(True)
                # 如果发生异常，就打印异常信息
                except Exception as e:
                    # 设置中断标志为True
                    self.stopped = True
                    # 发送一个信号给主线程，让主线程修改按钮的图标为继续
                    self.gui.icon_signal.emit('play')
                    # 修改服务器信息
                    self.gui.server_info_signal.emit('已断开连接，点击右下角按钮重连')
                    # 在控制台打印上传异常的内容
                    self.gui.output_signal.emit(f"<font color='red' face='bold'>上传异常：{e}</font>")
                    # 记录结束上传的时间
                    end_time = time.time()
                    # 记录结束上传的断点
                    end_breakpoint = self.sent
                    # 计算上传用时
                    duration = end_time - start_time
                    # 如果上传用时小于0.01秒，就把它设为0.01秒
                    if duration < 0.01:
                        duration = 0.01
                    # 计算上传数据量
                    sent = end_breakpoint - start_breakpoint
                    # 在控制台打印上传异常的消息，包括上传用时、上传数据量和上传速度
                    self.gui.output_signal.emit(f"<font color='purple'>在{duration:.2f}秒内上传了{self.format_size(sent)}数据</font>")
                    self.gui.output_signal.emit(f"<font color='purple'>上传速度：{sent / duration / 1024:.2f}KB/s</font>")
                    # 调用GUI对象的result信号对象的emit方法，传递一个False值，表示当前命令执行失败
                    self.gui.result.emit(False)
                # 在结束上传后，把所有控件恢复为可用
                self.gui.set_enabled(True)
        # 否则，说明文件已存在，弹出错误提示框
        else:
            self.gui.error_signal.emit(response)
            # 调用GUI对象的result信号对象的emit方法，传递一个False值，表示当前命令执行失败
            self.gui.result.emit(False)
        # 释放锁，让其他线程可以访问
        self.lock.release()

    # 定义一个函数，根据文件大小选择合适的单位，并返回一个格式化的字符串
    def format_size(self, size):
        # 定义一个列表，存储不同的单位
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        # 初始化单位的索引为0
        index = 0
        # 循环除以1024，直到文件大小小于1024或者单位索引达到最大值
        while size >= 1024 and index < len(units) - 1:
            # 除以1024
            size /= 1024
            # 索引加一
            index += 1
        # 返回一个保留两位小数的字符串，加上对应的单位
        return '{:.2f} {}'.format(size, units[index])

    # 定义一个槽函数，用于清除断点
    def clear_breakpoint(self):
        self.send_command("restart 0")
        if self.breakpoint == 0:
            # 在控制台打印设置断点的消息
            self.gui.write_output("<font color='black'>已清除断点</font>")