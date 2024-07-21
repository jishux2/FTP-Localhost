# login_window.py
# 这是一个登录窗口类，使用PySide6创建了一个图形化界面，可以连接到FTP服务器，登录或注册用户
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QDialog # 新增
)
from PySide6.QtCore import Qt

# 定义一个注册窗口类，继承自QDialog
class RegisterWindow(QDialog):

    # 初始化方法，接受一个父窗口作为参数
    def __init__(self, parent):
        # 调用父类的初始化方法
        super().__init__(parent)
        # 设置窗口的标题
        self.setWindowTitle('欢迎注册')
        # 设置窗口的大小
        self.resize(300, 200)
        # 增加一个属性，用于存储父窗口的引用
        self.parent = parent
        # 调用创建界面的方法
        self.create_ui()

    # 创建界面的方法
    def create_ui(self):
        # 创建一个网格布局对象，用于放置控件
        layout = QGridLayout()
        # 设置布局的间距和边距
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        # 创建一个标签对象，用于显示用户名
        label_username = QLabel('用户名')
        # 创建一个标签对象，用于显示密码
        label_password = QLabel('密  码')
        # 创建一个标签对象，用于显示确认密码
        label_confirm = QLabel('确认密码')
        # 创建一个输入框对象，用于输入用户名
        self.entry_username = QLineEdit()
        # 创建一个输入框对象，用于输入密码
        self.entry_password = QLineEdit()
        # 设置输入框的显示模式为密码模式
        self.entry_password.setEchoMode(QLineEdit.Password)
        # 创建一个输入框对象，用于输入确认密码
        self.entry_confirm = QLineEdit()
        # 设置输入框的显示模式为密码模式
        self.entry_confirm.setEchoMode(QLineEdit.Password)
        # 创建一个按钮对象，用于提交注册
        self.btn_submit = QPushButton('提  交')
        # 绑定按钮的点击事件，调用submit_register方法
        self.btn_submit.clicked.connect(self.submit_register)
        # 将控件添加到布局中，指定行列和对齐方式
        layout.addWidget(label_username, 0, 0, Qt.AlignRight)
        layout.addWidget(self.entry_username, 0, 1, Qt.AlignLeft)
        layout.addWidget(label_password, 1, 0, Qt.AlignRight)
        layout.addWidget(self.entry_password, 1, 1, Qt.AlignLeft)
        layout.addWidget(label_confirm, 2, 0, Qt.AlignRight)
        layout.addWidget(self.entry_confirm, 2, 1, Qt.AlignLeft)
        layout.addWidget(self.btn_submit, 3, 0, 1, 2, Qt.AlignCenter)
        # 将布局设置为窗口的布局
        self.setLayout(layout)

    # 提交注册的方法
    def submit_register(self):
        # 获取用户名，密码和确认密码
        username = self.entry_username.text()
        password = self.entry_password.text()
        confirm = self.entry_confirm.text()
        # 如果用户名，密码或确认密码为空，弹出错误提示框
        if not username or not password or not confirm:
            QMessageBox.warning(self, '警告', '用户名，密码或确认密码不能为空')
            return
        # 如果密码和确认密码不一致，弹出错误提示框
        if password != confirm:
            QMessageBox.warning(self, '警告', '密码和确认密码不一致')
            return
        # 如果用户名或密码的长度小于6或大于20，弹出错误提示框
        if len(username) < 6 or len(username) > 20:
            QMessageBox.warning(self, '警告', '用户名的长度应在6到20之间')
            return
        if len(password) < 6 or len(password) > 20:
            QMessageBox.warning(self, '警告', '密码的长度应在6到20之间')
            return
        # 如果用户名或密码中包含除了字母，数字和下划线以外的字符，弹出错误提示框
        if not username.isalnum() and '_' not in username:
            QMessageBox.warning(self, '警告', '用户名只能包含字母，数字和下划线')
            return
        if not password.isalnum() and '_' not in password:
            QMessageBox.warning(self, '警告', '密码只能包含字母，数字和下划线')
            return
        # 调用父窗口的ftp_client对象的send_command方法，传入注册请求
        result = self.parent.ftp_client.send_command(f"register {username} {password}")
        # 如果结果为True，表示注册成功，弹出提示框，并关闭注册窗口，显示FTP客户端界面
        if result:
            QMessageBox.information(self, '欢迎', '注册成功')
            # 把用户名赋值给父窗口的属性
            self.parent.username = username
            # 把服务器信息赋值给父窗口的属性
            self.parent.server_info = f"{self.parent.entry_ip.text()}:{self.parent.entry_port.text()}"
            # 如果注册成功，就把connected属性设置为False
            self.connected = False
            # 关闭注册窗口
            self.close()
            # 关闭登录窗口
            self.parent.close()
            # 把用户名和服务器信息传递给FTP客户端界面类
            self.parent.ftp_client.gui.set_user_and_server(self.parent.username, self.parent.server_info)
            # 显示FTP客户端界面
            self.parent.ftp_client.gui.show()
        # 否则，表示注册失败，弹出错误提示框
        else:
            QMessageBox.warning(self, '警告', '用户名已存在')