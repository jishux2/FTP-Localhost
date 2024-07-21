# 创建一个main.py文件，用于启动FTP客户端登录界面
# 从PySide6模块导入QApplication类
from PySide6.QtWidgets import QApplication
# 导入sys模块
import sys
# 导入LoginWindow类，这是一个自定义的登录窗口控件
from login_window import LoginWindow

# 定义一个主函数
if __name__ == "__main__":
    # 创建一个应用对象
    app = QApplication(sys.argv)
    # 创建一个登录窗口对象
    login_window = LoginWindow()
    # 显示登录窗口
    login_window.show()
    # 进入应用的事件循环
    app.exec_()