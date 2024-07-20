# 导入PySide6模块
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar

# 创建一个主窗口类
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 设置窗口标题和大小
        self.setWindowTitle("我的窗口")
        self.resize(400, 300)
        # 创建一个状态栏控件
        self.statusBar = QStatusBar()
        # 把状态栏控件设置为主窗口的状态栏
        self.setStatusBar(self.statusBar)
        # 在状态栏上显示一些消息
        self.statusBar.showMessage("这是一个状态栏")

# 创建一个应用程序对象
app = QApplication([])
# 创建一个主窗口对象
window = MyWindow()
# 显示主窗口
window.show()
# 运行应用程序
app.exec_()