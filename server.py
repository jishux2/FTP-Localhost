# ftp_server.py
# 这是一个FTP服务器，使用socket方式编程，从创建socket、监听端口开始，实现FTP协议的功能
# 导入所需的模块
import socket
import os
import sys
import threading
import time

# 定义一些常量
HOST = '127.0.0.1' # FTP服务器的IP地址，可以修改为其他值
PORT = 8888 # FTP服务器的端口号，可以修改为其他值
BUFFER_SIZE = 1024 # 缓冲区大小，用于接收和发送数据
COMMANDS = ['ls', 'cd', 'get', 'put', 'quit'] # 支持的FTP命令
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # FTP服务器的根目录，可以修改为其他值

# 定义一个FTP服务器类
class FTPServer:
    # 初始化方法
    def __init__(self):
        # 创建一个socket对象，用于监听客户端的连接
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置socket的选项，允许重用地址，避免端口占用的问题
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定IP地址和端口号
        self.server_sock.bind((HOST, PORT))
        # 开始监听，设置最大连接数为5
        self.server_sock.listen(5)
        # 打印服务器启动的消息
        print('FTP服务器启动，监听地址：', HOST, ':', PORT)

    # 启动服务器的方法
    def start(self):
        # 循环接受客户端的连接
        while True:
            # 接受客户端的连接，返回一个客户端的socket对象和地址
            client_sock, client_addr = self.server_sock.accept()
            # 打印客户端连接的消息
            print('客户端连接：', client_addr)
            # 创建一个子线程，用于处理客户端的请求
            threading.Thread(target=self.handle_client, args=(client_sock, client_addr)).start()

    # 处理客户端的请求的方法
    def handle_client(self, client_sock, client_addr):
        # 发送一个欢迎消息给客户端
        client_sock.send('欢迎使用FTP服务器'.encode())
        # 初始化客户端的当前目录为服务器的根目录
        current_dir = BASE_DIR
        # 循环接收客户端的命令
        while True:
            # 尝试接收客户端的命令
            try:
                # 接收客户端的命令
                command = client_sock.recv(BUFFER_SIZE).decode()
                # 在控制台打印客户端的命令
                print('接收命令：', command)
                # 如果命令为空，就跳过本次循环
                if not command:
                    continue
                # 如果命令不是支持的FTP命令，就发送一个错误消息给客户端
                if command.split(' ')[0] not in COMMANDS:
                    client_sock.send('错误的命令'.encode())
                    continue
                # 根据不同的命令，执行不同的操作
                if command == 'ls':
                    # 如果是ls命令，就发送当前目录和文件列表给客户端
                    self.list_dir(client_sock, current_dir)
                elif command.startswith('cd'):
                    # 如果是cd命令，就切换当前目录，并发送结果给客户端
                    current_dir = self.change_dir(client_sock, command, current_dir)
                elif command.startswith('get'):
                    # 如果是get命令，就发送文件给客户端
                    self.send_file(client_sock, command, current_dir)
                elif command.startswith('put'):
                    # 如果是put命令，就接收文件并保存
                    self.receive_file(client_sock, command, current_dir)
                elif command == 'quit':
                    # 如果是quit命令，就关闭客户端的socket，退出循环
                    client_sock.close()
                    break
            # 如果发生异常，就关闭客户端的socket，退出循环
            except Exception as e:
                print('客户端断开：', client_addr)
                client_sock.close()
                break

    # 发送当前目录和文件列表给客户端的方法
    def list_dir(self, client_sock, current_dir):
        # 如果当前目录是\\，就列出所有磁盘
        if current_dir == '\\':
            # 获取所有磁盘的名称
            drives = os.popen('wmic logicaldisk get name').read().split()
            # 去掉列表中的第一个元素，它是一个标题
            drives.pop(0)
            # 把当前目录和磁盘列表拼接成一个字符串，用换行符分隔
            response = current_dir + '\n' + '\n'.join(drives)
        # 否则，就列出当前目录下的所有文件和文件夹
        else:
            # 获取当前目录下的所有文件和文件夹
            files = os.listdir(current_dir)
            # 创建一个空列表，用于存储加上/的目录名
            dir_files = []
            # 循环遍历文件列表
            for file in files:
                # 拼接当前目录和文件名，得到文件的完整路径
                filepath = os.path.join(current_dir, file)
                # 如果文件是一个目录，就在文件名后面加上/
                if os.path.isdir(filepath):
                    file += '\\'
                # 把文件名添加到列表中
                dir_files.append(file)
            # 把当前目录和文件列表拼接成一个字符串，用换行符分隔
            response = current_dir + '\n' + '\n'.join(dir_files)
        # 发送响应给客户端
        client_sock.send(response.encode())

    # 切换当前目录并发送结果给客户端的方法
    def change_dir(self, client_sock, command, current_dir):
        # 把命令分割为两部分，第一部分是cd，第二部分是目标目录
        _, target_dir = command.split(' ', 1)
        # 如果目标目录是..，就返回上一级目录
        if target_dir == '..':
            # 如果当前目录是磁盘的根目录，就返回一个特殊的目录，表示所有磁盘
            if current_dir.endswith(':\\'):
                current_dir = '\\'
            # 否则，就返回上一级目录
            else:
                current_dir = os.path.dirname(current_dir.rstrip('\\'))
        # 否则，就拼接当前目录和目标目录，得到新的目录
        else:
            current_dir = os.path.join(current_dir, target_dir + '\\')
        # 如果新的目录存在，就发送一个成功的响应给客户端
        if os.path.exists(current_dir):
            response = 'OK ' + current_dir
        # 否则，就发送一个失败的响应给客户端
        else:
            response = '目录不存在'
        # 发送响应给客户端  
        client_sock.send(response.encode())
        # 返回新的当前目录
        return current_dir

    # 发送文件给客户端的方法
    def send_file(self, client_sock, command, current_dir):
        # 把命令分割为两部分，第一部分是get，第二部分是文件名
        _, filename = command.split(' ', 1)
        # 拼接当前目录和文件名，得到文件的完整路径
        filepath = os.path.join(current_dir, filename)
        # 如果文件存在，就发送一个成功的响应给客户端，包括文件名和文件大小
        if os.path.exists(filepath):
            filesize = os.path.getsize(filepath)
            response = 'OK ' + filename + ' ' + str(filesize)
            client_sock.send(response.encode())
            # 打开文件，准备读取数据
            with open(filepath, 'rb') as f:
                # 初始化已发送的字节数为0
                sent = 0
                # 循环读取数据，直到文件发送完毕
                while sent < filesize:
                    # 读取数据
                    data = f.read(BUFFER_SIZE)
                    # 发送数据
                    client_sock.send(data)
                    # 累加已发送的字节数
                    sent += len(data)
            # 在控制台打印发送完成的消息
            print('发送完成：', filename)
        # 否则，就发送一个失败的响应给客户端
        else:
            response = '文件不存在'
            client_sock.send(response.encode())

    # 接收文件并保存的方法
    def receive_file(self, client_sock, command, current_dir):
        # 把命令分割为两部分，第一部分是put，第二部分是客户端的文件路径
        _, filename = command.split(' ', 1)
        # 用os.path.basename函数来提取出文件名
        base_filename = os.path.basename(filename)
        # 拼接当前目录和文件名，得到文件的完整路径
        filepath = os.path.join(current_dir, base_filename)
        print(current_dir)
        print(base_filename)
        print(filepath)
        # 如果文件不存在，就发送一个成功的响应给客户端，包括文件名
        if not os.path.exists(filepath):
            response = 'OK ' + filename
            client_sock.send(response.encode())
            # 接收客户端发送的文件大小
            filesize = int(client_sock.recv(BUFFER_SIZE).decode())
            # 打开文件，准备写入数据
            with open(filepath, 'wb') as f:
                # 初始化已接收的字节数为0
                received = 0
                # 循环接收数据，直到文件接收完毕
                while received < filesize:
                    # 接收数据
                    data = client_sock.recv(BUFFER_SIZE)
                    # 写入数据
                    f.write(data)
                    # 累加已接收的字节数
                    received += len(data)
            # 在控制台打印接收完成的消息
            print('接收完成：', filename)
        # 否则，就发送一个失败的响应给客户端
        else:
            response = '文件已存在'
            client_sock.send(response.encode())

# 主函数
if __name__ == '__main__':
    # 创建一个FTP服务器对象
    ftp_server = FTPServer()
    # 启动FTP服务器
    ftp_server.start()