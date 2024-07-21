# login_window.py
# 这是一个登录窗口类，使用PySide6创建了一个图形化界面，可以连接到FTP服务器，登录或注册用户
from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialog # 新增
)
from PySide6.QtCore import Qt
from client import FTPClient
# 导入RegisterWindow类，这是一个自定义的注册窗口控件
from register_window import RegisterWindow

# 定义一个登录窗口类，继承自QWidget
class LoginWindow(QWidget):

    # 初始化方法
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()
        # 设置窗口的标题
        self.setWindowTitle('欢迎登录')
        # 设置窗口的大小
        self.resize(450, 300)
        # 增加一个属性，用于存储用户名
        self.username = ""
        # 增加一个属性，用于存储服务器信息
        self.server_info = ""
        # 增加一个属性，用于标识是否处于已连接未认证的状态
        self.connected = False
        # 调用创建界面的方法
        self.create_ui()

    # 创建界面的方法
    def create_ui(self):
        # 创建一个网格布局对象，用于放置控件
        layout = QGridLayout()
        # 设置布局的间距和边距
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        # 创建一个标签对象，用于显示IP地址
        label_ip = QLabel('IP地址')
        # 创建一个标签对象，用于显示端口号
        label_port = QLabel('端口号')
        # 创建一个标签对象，用于显示用户名
        label_username = QLabel('用户名')
        # 创建一个标签对象，用于显示密码
        label_password = QLabel('密  码')
        # 创建一个输入框对象，用于输入IP地址
        self.entry_ip = QLineEdit()
        # 设置输入框的默认值为127.0.0.1
        self.entry_ip.setText('127.0.0.1')
        # 创建一个输入框对象，用于输入端口号
        self.entry_port = QLineEdit()
        # 设置输入框的默认值为8888
        self.entry_port.setText('8888')
        # 创建一个输入框对象，用于输入用户名
        self.entry_username = QLineEdit()
        # 设置输入框的默认值为请输入用户名
        self.entry_username.setText('请输入用户名')
        # 设置输入框的状态为不可用
        self.entry_username.setEnabled(False)
        # 创建一个输入框对象，用于输入密码
        self.entry_password = QLineEdit()
        # 设置输入框的显示模式为密码模式
        self.entry_password.setEchoMode(QLineEdit.Password)
        # 设置输入框的状态为不可用
        self.entry_password.setEnabled(False)
        # 创建一个按钮对象，用于连接服务器
        self.btn_connect = QPushButton('连  接')
        # 绑定按钮的点击事件，调用connect_server方法
        self.btn_connect.clicked.connect(self.connect_server)
        # 创建一个按钮对象，用于登录用户
        self.btn_login = QPushButton(' 登  录 ')
        # 绑定按钮的点击事件，调用login_user方法
        self.btn_login.clicked.connect(self.login_user)
        # 设置按钮的状态为不可用
        self.btn_login.setEnabled(False)
        # 创建一个按钮对象，用于注册用户
        self.btn_register = QPushButton(' 注  册 ')
        # 绑定按钮的点击事件，调用show_register_window方法
        self.btn_register.clicked.connect(self.show_register_window)
        # 设置按钮的状态为不可用
        self.btn_register.setEnabled(False)
        # 将控件添加到布局中，指定行列和对齐方式
        layout.addWidget(label_ip, 0, 0, Qt.AlignRight)
        layout.addWidget(self.entry_ip, 0, 1, Qt.AlignLeft)
        layout.addWidget(label_port, 1, 0, Qt.AlignRight)
        layout.addWidget(self.entry_port, 1, 1, Qt.AlignLeft)
        layout.addWidget(self.btn_connect, 1, 2, Qt.AlignCenter)
        layout.addWidget(label_username, 2, 0, Qt.AlignRight)
        layout.addWidget(self.entry_username, 2, 1, Qt.AlignLeft)
        layout.addWidget(label_password, 3, 0, Qt.AlignRight)
        layout.addWidget(self.entry_password, 3, 1, Qt.AlignLeft)
        layout.addWidget(self.btn_login, 4, 0, Qt.AlignCenter)
        layout.addWidget(self.btn_register, 4, 1, Qt.AlignCenter)
        # 将布局设置为窗口的布局
        self.setLayout(layout)

    # 连接服务器的方法
    def connect_server(self):
        # 获取IP地址和端口号
        ip = self.entry_ip.text()
        port = int(self.entry_port.text())  # 确保端口号是整数类型
        # 创建一个FTP客户端对象
        self.ftp_client = FTPClient(ip, port)
        # 尝试连接到FTP服务器
        try:
            self.ftp_client.connect_server()
            # 如果连接成功，弹出提示框，并把用户名和密码的输入框和按钮设置为可用
            QMessageBox.information(self, '提示', '连接成功')
            self.entry_username.setEnabled(True)
            self.entry_password.setEnabled(True)
            self.btn_login.setEnabled(True)
            self.btn_register.setEnabled(True)
            # 如果连接成功，就把connected属性设置为True
            self.connected = True
        # 如果发生异常，弹出错误提示框，并把用户名和密码的输入框和按钮设置为不可用
        except Exception as e:
            QMessageBox.critical(self, '错误', str(e))
            self.entry_username.setEnabled(False)
            self.entry_password.setEnabled(False)
            self.btn_login.setEnabled(False)
            self.btn_register.setEnabled(False)

    # 登录用户的方法
    def login_user(self):
        # 获取用户名和密码
        username = self.entry_username.text()
        password = self.entry_password.text()
        # 调用ftp_client对象的send_command方法，传入登录请求
        result = self.ftp_client.send_command(f"login {username} {password}")
        # 如果结果为True，表示登录成功，弹出提示框，并关闭登录窗口，显示FTP客户端界面
        if result:
            QMessageBox.information(self, '欢迎', '登录成功')
            # 把用户名赋值给属性
            self.username = username
            # 把服务器信息赋值给属性
            self.server_info = f"{self.entry_ip.text()}:{self.entry_port.text()}"
            # 如果登录成功，就把connected属性设置为False
            self.connected = False
            # 关闭登录窗口
            self.close()
            # 把用户名和服务器信息传递给FTP客户端界面类
            self.ftp_client.gui.set_user_and_server(self.username, self.server_info)
            # 显示FTP客户端界面
            self.ftp_client.gui.show()
        # 否则，表示登录失败，弹出错误提示框
        else:
            QMessageBox.warning(self, '警告', '用户名或密码错误')

    # 在LoginWindow类中，增加一个方法，用于弹出注册窗口
    def show_register_window(self):
        # 创建一个注册窗口对象
        self.register_window = RegisterWindow(self)
        # 显示注册窗口
        self.register_window.show()

    # 处理窗口关闭事件的方法
    def closeEvent(self, event):
        # 判断是否已经连接了服务器但未认证，如果是，就发送quit命令
        if self.connected:
            # 调用FTP客户端的发送命令的方法，把quit命令作为参数传递
            self.ftp_client.send_command("quit")
        # 调用父类的closeEvent方法，完成窗口关闭的操作
        super().closeEvent(event)