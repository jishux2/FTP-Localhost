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
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, QThread, Signal

# 定义一些常量
HOST = "127.0.0.1"  # FTP服务器的IP地址，可以修改为其他值
PORT = 8888  # FTP服务器的端口号，可以修改为其他值
BUFFER_SIZE = 1024  # 缓冲区大小，用于接收和发送数据
COMMANDS = ["ls", "cd", "get", "put", "quit"]  # 支持的FTP命令


# 定义一个FTP客户端类，继承自QWidget
class FTPClient(QWidget):
    # 定义一个信号，用于在子线程中更新进度条的值
    progress_signal = Signal(int)
    # 定义一个信号，用于在主线程中弹出文件对话框，并传递文件名给子线程
    file_dialog_signal = Signal(str)
    # 定义一个信号，用于在主线程中弹出错误提示框，并传递错误信息给子线程
    error_signal = Signal(str)

    # 初始化方法
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 创建一个socket对象，用于和FTP服务器通信
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置socket的超时时间为10秒，如果超过10秒没有收到服务器的响应，就认为连接断开
        self.sock.settimeout(10)
        # 创建一个锁对象，用于同步多个线程的访问
        self.lock = threading.Lock()
        # 初始化一些属性，用于存储当前的目录，文件名，文件大小，已传输的字节数等信息
        self.current_dir = ""
        self.filename = ""
        self.filesize = 0
        self.sent = 0
        self.received = 0
        # 在FTPClient类中，创建一个队列对象，用于存储主线程发送的文件名
        self.file_queue = queue.Queue()
        # 调用创建界面的方法
        self.create_ui()
        # 调用连接服务器的方法
        self.connect_server()

    # 创建界面的方法
    def create_ui(self):
        # 设置窗口的标题，大小，居中显示
        self.setWindowTitle("FTP客户端")
        self.resize(600, 400)
        self.center()
        # 创建一个网格布局对象，用于放置各种控件
        self.layout = QGridLayout()
        # 创建一个标签对象，用于显示当前的目录
        self.dir_label = QLabel("当前目录：")
        # 创建一个文本框对象，用于显示和输入当前的目录
        self.dir_edit = QLineEdit()
        # 创建一个按钮对象，用于切换目录
        self.dir_button = QPushButton("切换")
        # 创建一个标签对象，用于显示文件列表
        self.file_label = QLabel("文件列表：")
        # 创建一个文本框对象，用于显示文件列表
        self.file_edit = QLineEdit()
        # 创建一个按钮对象，用于下载文件
        self.download_button = QPushButton("下载")
        # 创建一个按钮对象，用于上传文件
        self.upload_button = QPushButton("上传")
        # 创建一个标签对象，用于显示进度条
        self.progress_label = QLabel("传输进度：")
        # 创建一个进度条对象，用于显示传输进度
        self.progress_bar = QProgressBar()
        # 创建一个按钮对象，用于退出程序
        self.quit_button = QPushButton("退出")
        # 把各个控件按照网格布局添加到窗口中
        self.layout.addWidget(self.dir_label, 0, 0)
        self.layout.addWidget(self.dir_edit, 0, 1, 1, 3)
        self.layout.addWidget(self.dir_button, 0, 4)
        self.layout.addWidget(self.file_label, 1, 0)
        self.layout.addWidget(self.file_edit, 1, 1, 1, 3)
        self.layout.addWidget(self.download_button, 1, 4)
        self.layout.addWidget(self.upload_button, 2, 4)
        self.layout.addWidget(self.progress_label, 3, 0)
        self.layout.addWidget(self.progress_bar, 3, 1, 1, 4)
        self.layout.addWidget(self.quit_button, 4, 4)
        # 设置窗口的布局为网格布局
        self.setLayout(self.layout)
        # 绑定各个按钮的点击事件到对应的槽函数
        self.dir_button.clicked.connect(self.change_dir)
        self.download_button.clicked.connect(self.download_file)
        self.upload_button.clicked.connect(self.upload_file)
        self.quit_button.clicked.connect(self.quit)
        # 绑定进度信号到进度条的setValue方法，用于更新进度条的值
        self.progress_signal.connect(self.progress_bar.setValue)
        # 绑定信号和槽函数
        self.file_dialog_signal.connect(self.show_file_dialog)
        # 绑定信号和槽函数
        self.error_signal.connect(self.show_error)

    # 连接服务器的方法
    def connect_server(self):
        # 尝试连接到FTP服务器
        try:
            self.sock.connect((HOST, PORT))
            # 接收服务器的欢迎消息
            msg = self.sock.recv(BUFFER_SIZE).decode()
            # 在控制台打印欢迎消息
            print(msg)
            # 发送一个ls命令，获取当前目录和文件列表
            self.send_command("ls")
        # 如果发生异常，弹出错误提示框
        except Exception as e:
            self.show_error(str(e))

    # 发送命令的方法
    def send_command(self, command):
        # 尝试发送命令到服务器
        try:
            # 在控制台打印发送的命令
            print("发送命令：", command)
            # 把命令编码为字节串，发送到服务器
            self.sock.send(command.encode())
            # 初始化响应为空字符串
            response = ""
            # 接收一部分响应
            data = self.sock.recv(BUFFER_SIZE).decode()
            # 循环接收服务器的响应，直到没有数据可读
            while data:
                # 将收到的数据拼接起来
                response += data
                # 检查是否还有数据可读
                readable, _, _ = select.select([self.sock], [], [], 0)
                if readable:
                    # 如果有数据，继续接收
                    data = self.sock.recv(BUFFER_SIZE).decode()
                else:
                    # 如果数据为空，说明接收完毕，跳出循环
                    break
            # 在控制台打印服务器的响应
            print("接收响应：", response)
            # 根据不同的命令，执行不同的操作
            if command == "ls":
                # 如果是ls命令，就更新当前目录和文件列表
                self.update_dir_and_file(response)
            elif command.startswith("cd"):
                # 如果是cd命令，就更新当前目录
                self.update_dir(response)
            elif command.startswith("get"):
                # 如果是get命令，就创建一个子线程，执行下载文件的操作
                threading.Thread(target=self.receive_file, args=(response,)).start()
            elif command.startswith("put"):
                # 如果是put命令，就创建一个子线程，执行上传文件的操作
                threading.Thread(target=self.send_file, args=(response,)).start()
            elif command == "quit":
                # 如果是quit命令，就关闭socket，退出程序
                self.sock.close()
                sys.exit()
        # 如果发生异常，弹出错误提示框
        except Exception as e:
            self.show_error(str(e))

    # 更新当前目录和文件列表的方法
    def update_dir_and_file(self, response):
        # 把响应分割为两部分，第一部分是当前目录，第二部分是文件列表
        dir, file = response.split("\n", 1)
        # 把当前目录赋值给属性
        self.current_dir = dir
        # 把当前目录显示在文本框中
        self.dir_edit.setText(self.current_dir)
        # 把文件列表显示在文本框中
        self.file_edit.setText(file)

    # 更新当前目录的方法
    def update_dir(self, response):
        # 如果响应以OK开头，说明切换目录成功
        if response.startswith("OK"):
            # 把响应的第二部分赋值给当前目录
            self.current_dir = response.split(" ", 1)[1]
            # 把当前目录显示在文本框中
            self.dir_edit.setText(self.current_dir)
            # 发送一个ls命令，更新文件列表
            self.send_command("ls")
        # 否则，说明切换目录失败，弹出错误提示框
        else:
            self.show_error(response)

    # 切换目录的槽函数
    def change_dir(self):
        # 获取文本框中输入的目录
        dir = self.dir_edit.text()
        # 如果目录不为空，就发送一个cd命令，切换到该目录
        if dir:
            self.send_command("cd " + dir)
        # 否则，弹出错误提示框
        else:
            self.show_error("请输入目录")

    # 下载文件的槽函数
    def download_file(self):
        # 获取文本框中输入的文件名
        filename = self.file_edit.text()
        # 如果文件名不为空，就发送一个get命令，下载该文件
        if filename:
            self.send_command("get " + filename)
        # 否则，弹出错误提示框
        else:
            self.show_error("请输入文件名")

    # 上传文件的槽函数
    def upload_file(self):
        # 弹出一个文件选择对话框，让用户选择要上传的文件
        filename, _ = QFileDialog.getOpenFileName(self, "选择文件", ".", "所有文件 (*)")
        # 如果文件名不为空，就发送一个put命令，上传该文件
        if filename:
            self.send_command("put " + filename)
        # 否则，在控制台打印取消上传的消息
        else:
            print("取消上传")

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
            # 把响应分割为三部分，第一部分是OK，第二部分是文件名，第三部分是文件大小
            _, self.filename, self.filesize= response.split(" ")
            # 把文件大小转换为整数
            self.filesize = int(self.filesize)
            # 初始化已接收的字节数为0
            self.received = 0
            # 发送一个信号给主线程，让主线程弹出文件对话框，并传递文件名
            self.file_dialog_signal.emit(self.filename)
            # 从队列中取出文件名
            filename = self.file_queue.get()
            print(filename)
            # 如果文件名不为空，就打开该文件，准备写入数据
            if filename:
                with open(filename, "wb") as f:
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
                        self.progress_signal.emit(percent)
                # 在控制台打印下载完成的消息
                print("下载完成：", self.filename)
            # 否则，如果文件名为空，就丢弃服务器发送的文件内容
            else:
                # 循环接收数据，直到文件接收完毕
                while self.received < self.filesize:
                    # 接收数据
                    data = self.sock.recv(BUFFER_SIZE)
                    # 累加已接收的字节数
                    self.received += len(data)
                # 在控制台打印取消下载的消息
                print("取消下载：", self.filename)
        # 否则，说明文件不存在，弹出错误提示框
        else:
            # 在子线程中，不再直接调用show_error方法，而是发送一个信号给主线程，并传递错误信息
            # self.show_error(response)
            self.error_signal.emit(response)
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
            print(self.filesize)
            # 发送文件大小
            self.sock.send(str(self.filesize).encode())
            # 初始化已发送的字节数为0
            self.sent = 0
            # 打开文件，准备读取数据
            with open(self.filename, "rb") as f:
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
                    self.progress_signal.emit(percent)
            # 在控制台打印上传完成的消息
            print("上传完成：", self.filename)
        # 否则，说明文件已存在，弹出错误提示框
        else:
            self.error_signal.emit(response)
        # 释放锁，让其他线程可以访问
        self.lock.release()

    # 定义一个槽函数，用于接收信号的参数，并弹出文件对话框
    # 在show_file_dialog方法中，不再发送文件名给子线程，而是把它们放入队列中
    def show_file_dialog(self, filename):
        # 弹出一个文件保存对话框，让用户选择保存的位置和文件名
        filename, _ = QFileDialog.getSaveFileName(self, '保存文件', filename, '所有文件 (*)')
        # 如果文件名不为空，就把文件名放入队列中
        if filename:
            self.file_queue.put(filename)
        # 否则，如果文件名为空，就把一个空字符串放入队列中，表示用户没有选择文件
        else:
            self.file_queue.put('')

    # 定义一个槽函数，用于接收信号的参数，并弹出错误提示框
    def show_error(self, error):
        # 创建一个消息框对象，设置标题，图标，文本，按钮等属性
        msg_box = QMessageBox()
        msg_box.setWindowTitle('错误')
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(error)
        msg_box.setStandardButtons(QMessageBox.Ok)
        # 显示消息框
        msg_box.exec_()

    # 把窗口居中显示的方法
    def center(self):
        # 获取窗口的几何形状
        qr = self.frameGeometry()
        # 获取屏幕对象
        screen = QApplication.primaryScreen()
        # 获取屏幕的中心点
        cp = screen.availableGeometry().center()
        # 把窗口的中心点移动到屏幕的中心点
        qr.moveCenter(cp)
        # 把窗口移动到qr的位置
        self.move(qr.topLeft())


# 主函数
if __name__ == "__main__":
    # 创建一个应用对象
    app = QApplication(sys.argv)
    # 创建一个FTP客户端对象
    ftp_client = FTPClient()
    # 显示FTP客户端窗口
    ftp_client.show()
    # 进入应用的主循环
    sys.exit(app.exec_())
