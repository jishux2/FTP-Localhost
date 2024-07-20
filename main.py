# 创建一个main.py文件，用于启动FTP客户端程序
# 导入PySide6模块
import PySide6
# 导入sys模块
import sys
# 从ftp_client模块导入FTPClient类
from client import FTPClient

# 定义一个主函数
if __name__ == "__main__":
    # 创建一个应用对象
    app = PySide6.QtWidgets.QApplication(sys.argv)
    # 创建一个FTP客户端对象
    ftp_client = FTPClient()
    # 显示FTP客户端窗口
    ftp_client.gui.show()
    # 进入应用的主循环
    sys.exit(app.exec_())