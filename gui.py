# gui.py
# 这是一个GUI类，用于创建和布局控件，以及处理一些界面相关的事件
# 导入PySide6等模块
import socket
import os
import html
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
    QListWidget,  # 新增
    QListWidgetItem,  # 新增
    QStyle,  # 新增
    QSizePolicy,
    QMenuBar,  # 新增
    QMenu,  # 新增
    QDialog,  # 新增
    QTextEdit,  # 新增
    QVBoxLayout,  # 新增
    QInputDialog,
    QSplitter,  # 新增
    QFrame,  # 新增
    QToolButton,  # 新增
    QHBoxLayout,
    QStatusBar,
    QMainWindow
)
from PySide6.QtCore import Qt, Signal, QSize
# 导入QAction
from PySide6.QtGui import QAction, QTextCursor, QFont
# 导入UserInput类，这是一个自定义的输入框控件，用于接收用户的命令
from user_input import UserInput
# 导入ChangelogDialog类，这是一个自定义的对话框控件，用于显示各种信息
from info_dialog import InfoDialog

# 定义一个常量，用于存储Changelog的内容
CHANGELOG = """
版本 1.0.0
- 实现了基本的FTP协议功能，包括ls, cd, get, put, quit
- 使用PySide6创建了一个图形化界面，可以显示当前目录和文件列表，可以上传和下载文件，可以切换目录
- 使用QProgressBar显示了传输进度
- 使用QListWidget优化了文件列表的显示，可以双击文件或目录进行操作
- 增加了Changelog的功能，可以查看版本更新的信息

版本 1.1.0
- 在文件列表中存储文件大小，并提供文件菜单选项，方便用户查看
- 为发送和接收文件的方法增加异常处理机制，并在传输结束后显示相关信息
- 支持restart命令，可以根据需要自动或手动地设置和清除断点
- 在必要的时机及时清除客户端相关数据，避免对后续操作造成影响
- 实现文件的断点续传功能，通过QPushButton控件，将中断和重连的操作集成到一个按钮上
- 完善对各控件的控制逻辑，避免用户在传输过程中进行错误或冲突的操作
- 修复若干bug

版本 1.1.1
- 客户端在完整接收数据后再进行解码，防止多字节字符因被截断而导致解码错误
- 将GUI部分的代码封装为一个独立的文件gui.py，实现代码的清晰性和模块化
- 将选择文件的操作委托给GUI类，使客户端类与PySide6模块解耦
- 将主函数的代码拆分为main.py文件，使client.py文件仅负责FTP客户端的逻辑
- 在传输完成后及时同步删除断点，防止对后续传输造成干扰

版本 2.1.0
- 重建用户界面
  - 主窗口改为由QMainWindow类派生，并使用多层窗口部件和不同类型的布局（垂直、水平、网格）来构建界面
  - 删除冗余的控件和属性配置，精简代码逻辑
  - 通过引入菜单栏、状态栏、分割器等组件，优化了界面布局的效果和美感
  - 添加命令行界面，定义用户输入文本框类，支持快捷发送、多行输入和在主窗口保持响应的同时按顺序执行
  - 创建控制台界面，将之前在控制台输出的信息以富文本形式呈现在文本框控件里
  - 用一个实时更新的标签来显示清空进度，替代原来的单行覆盖输出
  - 将原有的ChangelogDialog类重构为一个通用的InfoDialog类，增加一个title参数，用于展示不同主题的信息对话框
  - 将gui.py文件中的一些自定义控件类分离出来，并各自保存在单独的文件中
  - 按照代码结构的逻辑，把布局或功能相近的控件代码分组排列，增强代码的可读性
- 调整部分控件的启用/禁用状态的逻辑，以兼容全新UI下findChildren方法的变化（详见GUI类的set_enabled方法的注释）
- 在窗口关闭按钮的点击事件中，执行发送quit命令的方法，以保证在窗口关闭前，与服务器正确地断开连接
- 修改若干bug
- 待实现：登录功能
"""

# 定义一个常量，用于存储帮助的内容
HELP = """
本文档是FTP客户端的使用指南，介绍了它的主要功能和操作步骤：
- 左侧文件列表显示当前目录的内容，双击文件夹可进入，双击文件可下载，双击返回项可回到上级目录
- 右上控制台呈现FTP客户端的输出，如命令结果，传输信息，错误提示等
- 右下输入框可输入FTP命令，如ls, cd, get, put等。Ctrl+Enter换行，Enter或发送按钮执行。发送按钮菜单可选Enter或Ctrl+Enter发送模式
- 状态栏位于窗口的底部，用一个进度条展示文件传输的百分比。另外一个标签显示取消下载后释放缓冲区的状态。一个按钮可以切换传输的暂停或继续
- 菜单栏提供了菜单选项，点击后可弹出Changelog或帮助对话框，分别展示程序的更新日志和功能说明
"""

# 定义一个常量字典，把图标的名字和对应的QStyle值映射起来
ICONS = {
    'play': QStyle.SP_MediaPlay,
    'pause': QStyle.SP_MediaPause,
    'stop': QStyle.SP_MediaStop,
    'next': QStyle.SP_MediaSkipForward,
    'previous': QStyle.SP_MediaSkipBackward
}

# 定义一个FTPClientGUI类，继承自QMainWindow
class FTPClientGUI(QMainWindow):
    # 定义一个信号，用于在子线程中更新进度条的值
    progress_signal = Signal(int)
    # 定义一个信号，用于在子线程中改变按钮的图标
    icon_signal = Signal(str)
    # 定义一个信号，用于在主线程中弹出文件对话框，并传递文件名给子线程
    file_dialog_signal = Signal(str)
    # 定义一个信号，用于在主线程中弹出错误提示框，并传递错误信息给子线程
    error_signal = Signal(str)
    # 定义一个信号，用于在子线程中发送命令的执行结果，True表示成功，False表示失败
    result = Signal(bool)
    # 定义一个信号，用于传递清空进度的百分比，参数类型为整数
    clear_signal = Signal(int)
    # 定义一个信号，用于传递要写入的文本
    output_signal = Signal(str)


    # 初始化方法
    def __init__(self):
        # 调用父类的初始化方法
        super().__init__()

    def create_ui(self, ftp_client):
        # 设置窗口的标题，大小，居中显示
        self.setWindowTitle("FTP客户端")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.resize(1000, 600)  # 修改窗口的初始大小
        self.center()
        # 把FTPClient对象赋值给self.ftp_client
        self.ftp_client = ftp_client
        # 定义一个属性，用于存储当前执行的命令的索引
        self.index = 0
        # 定义一个属性，用于存储用户输入的命令列表
        self.commands = []
        # 增加一个属性，用于存储清空进度的百分比
        # 初始值设为0，表示还没有开始清空
        self.clear_percent = 0
        
        # 创建一个菜单栏对象，用于放置菜单
        self.menu_bar = self.menuBar()
        # 设置菜单栏不使用本地样式，以便在MacOS上显示
        self.menu_bar.setNativeMenuBar(False)
        # 创建一个菜单对象，用于放置菜单项
        self.menu = QMenu("菜单")
        # 创建一个菜单项对象，在addAction方法里传入一个槽函数，用于显示Changelog
        self.changelog_action = self.menu.addAction("Changelog", self.show_changelog)
        # 增加一个菜单项对象，在addAction方法里传入一个槽函数，用于显示帮助
        self.help_action = self.menu.addAction("帮助", self.show_help)
        # 把菜单添加到菜单栏中
        self.menu_bar.addMenu(self.menu)
        # 设置菜单项的角色为应用程序特定的角色，以便在MacOS上显示
        self.changelog_action.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)
        self.help_action.setMenuRole(QAction.MenuRole.ApplicationSpecificRole)

        # 创建一个标签对象，用于显示当前的目录
        self.dir_label = QLabel("当前目录：")
        # 创建一个文本框对象，用于显示和输入当前的目录
        self.dir_edit = QLineEdit()
        # 创建一个按钮对象，用于切换目录
        self.dir_button = QPushButton("切换")
        
        # 创建一个文本框对象，用于显示文件列表
        # self.file_edit = QLineEdit()
        # 创建一个按钮对象，用于下载文件
        # self.download_button = QPushButton("下载")
        # 创建一个按钮对象，用于上传文件

        self.upload_button = QPushButton("上传")
        # 创建一个按钮对象，用于退出程序
        self.quit_button = QPushButton("退出")

        # 创建一个标签对象，用于显示文件列表
        self.file_label = QLabel("文件列表：")
        # 创建一个列表控件对象，用于显示文件列表
        self.file_list = QListWidget()
        # 设置列表控件的选择模式为单选
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        # 增加一个按钮对象，用于设置断点
        self.break_button = QPushButton("设置断点")
        # 增加一个按钮对象，用于清除断点
        self.clear_button = QPushButton("清除断点")

        # 创建一个标签对象，用于显示进度条
        self.progress_label = QLabel("传输进度：")
        # 创建一个进度条对象，用于显示传输进度
        self.progress_bar = QProgressBar()
        # 增加一个按钮对象，用于断开和重新连接
        self.connect_button = QPushButton()
        # 修改按钮对象的图标，用视频的暂停和继续的图标
        self.connect_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        # 增加一个按钮对象，用于清空输出
        self.clear_console_button = QPushButton("清空")
        # 增加一个按钮对象，用于初始化所有数据
        self.init_button = QPushButton("初始化")
        # 创建一个标签对象，用于显示控制台的输出
        self.output_label = QLabel("控制台：")
        # 增加一个文本编辑控件，用于显示各种输出
        self.output_edit = QTextEdit()
        # 设置文本编辑控件为只读，不可编辑
        self.output_edit.setReadOnly(True)
        # 设置文本编辑控件接受富文本格式
        self.output_edit.setAcceptRichText(True)
        # 把输出框的字体设置为微软雅黑，字号为11
        self.output_edit.setFont(QFont("Microsoft Yahei", 11))

        # 创建一个标签对象，用于提示用户输入命令
        self.input_label = QLabel("在此输入命令：")
        # 在创建发送按钮的菜单对象之前，定义一个属性，用于存储发送模式
        # 默认的发送模式是Enter
        self.send_mode = "Enter"
        # 创建一个UserInput对象，作为输入框控件，把自身作为父窗口对象传递给它
        self.input_edit = UserInput(self)
        # 把输入框的字体设置为微软雅黑，字号为11
        self.input_edit.setFont(QFont("Microsoft Yahei", 11))
        # 增加一个按钮对象，用于发送命令
        self.send_button = QToolButton()
        # 设置按钮对象的文本为"发送"
        self.send_button.setText("发送")
        # 设置按钮对象的弹出模式为菜单按钮弹出
        self.send_button.setPopupMode(QToolButton.MenuButtonPopup)
        # 增加一个菜单对象，用于放置发送按钮的选项
        self.send_menu = QMenu()
        # 创建两个菜单项对象，用于设置发送模式为Enter或Ctrl+Enter
        # 把菜单项设置为可选的
        # 绑定菜单项的触发事件到一个槽函数，用于设置发送模式
        # 用lambda表达式传递一个参数给槽函数
        self.send_enter_action = self.send_menu.addAction("Press Enter to send", lambda: self.set_send_mode("Enter"))
        self.send_enter_action.setCheckable(True)
        self.send_ctrl_enter_action = self.send_menu.addAction("Press Ctrl+Enter to send", lambda: self.set_send_mode("Ctrl+Enter"))
        self.send_ctrl_enter_action.setCheckable(True)
        # 把菜单对象设置为发送按钮的菜单
        self.send_button.setMenu(self.send_menu)
        # 默认把发送模式为"Enter"的菜单项设置为选中状态
        self.send_enter_action.setChecked(True)
        # 把发送按钮的点击事件绑定到上面定义的方法
        self.send_button.clicked.connect(self.send_button_clicked)

        # 创建一个垂直布局对象，用于放置文件标签和文件列表
        self.left_layout = QVBoxLayout()
        # 把文件标签和文件列表添加到垂直布局中
        self.left_layout.addWidget(self.file_label)
        self.left_layout.addWidget(self.file_list)
        # 创建一个网格布局对象，用于放置中断按钮和清除按钮
        self.left_buttons_layout = QGridLayout()
        # 把断点按钮和清除按钮添加到网格布局中，分别占据第一行第一列和第一行第二列
        self.left_buttons_layout.addWidget(self.break_button, 0, 0)
        self.left_buttons_layout.addWidget(self.clear_button, 0, 1)
        # 把网格布局添加到垂直布局中
        self.left_layout.addLayout(self.left_buttons_layout)
        # 创建一个窗口部件对象，用于容纳垂直布局
        self.left_layout_widget = QWidget()
        # 设置窗口部件的边距为0
        self.left_layout_widget.setContentsMargins(0, 0, 0, 0)
        # 把垂直布局设置为窗口部件的布局
        self.left_layout_widget.setLayout(self.left_layout)

        # 增加一个垂直分割器对象，用于分割右侧的上下两部分
        self.v_splitter = QSplitter(Qt.Vertical)
        # 设置分割器的手柄的宽度为10像素
        self.v_splitter.setHandleWidth(10)
        # 设置分割器中的框架不可以被折叠
        self.v_splitter.setChildrenCollapsible(False)

        # 创建一个窗口部件对象，用于放置上半部分的控件
        self.upper_half = QWidget()
        # 创建一个垂直布局对象，用于放置输出标签、退出按钮、初始化按钮、清空控制台按钮和输出框
        self.upper_half_layout = QVBoxLayout()
        # 创建一个水平布局对象，用于放置输出标签、退出按钮、初始化按钮和清空控制台按钮
        self.upper_half_buttons = QHBoxLayout()
        # 把输出标签添加到水平布局中
        self.upper_half_buttons.addWidget(self.output_label)
        # 在水平布局中添加一个弹性空间，用于让控制台标签靠左对齐，按钮靠右对齐
        self.upper_half_buttons.addStretch()
        # 把退出按钮、初始化按钮和清除控制台按钮添加到水平布局中
        self.upper_half_buttons.addWidget(self.quit_button)
        self.upper_half_buttons.addWidget(self.init_button)
        self.upper_half_buttons.addWidget(self.clear_console_button)
        # 把水平布局添加到垂直布局中
        self.upper_half_layout.addLayout(self.upper_half_buttons)
        # 把输出框添加到垂直布局中
        self.upper_half_layout.addWidget(self.output_edit)
        # 把垂直布局设置为窗口部件的布局
        self.upper_half.setLayout(self.upper_half_layout)

        # 创建一个窗口部件对象，用于放置下半部分的控件
        self.bottom_half = QWidget()
        # 创建一个垂直布局对象，用于放置输入标签、输入框和一些按钮
        self.bottom_half_layout = QVBoxLayout()
        # 创建一个水平布局对象，用于放置输入标签、上传按钮和发送按钮
        self.bottom_half_buttons = QHBoxLayout()
        # 把输入标签添加到水平布局中
        self.bottom_half_buttons.addWidget(self.input_label)
        # 在水平布局中添加一个弹性空间，用于让输入标签靠左对齐，按钮靠右对齐
        self.bottom_half_buttons.addStretch()
        # 把上传按钮和发送按钮添加到水平布局中
        self.bottom_half_buttons.addWidget(self.upload_button)
        self.bottom_half_buttons.addWidget(self.send_button)
        # 把水平布局添加到垂直布局中
        self.bottom_half_layout.addLayout(self.bottom_half_buttons)
        # 把输入框添加到垂直布局中
        self.bottom_half_layout.addWidget(self.input_edit)
        # 把垂直布局设置为窗口部件的布局
        self.bottom_half.setLayout(self.bottom_half_layout)

        # 创建一个标签对象，用于显示清空进度，初始文本为"清空进度：0%"
        self.clear_label = QLabel("清空进度：0%")

        # 创建一个状态栏对象，用于显示一些状态信息
        self.status_bar = QStatusBar()
        # 把清空进度标签对象添加到状态栏中
        self.status_bar.addWidget(self.clear_label)
        # 把进度条添加到状态栏中，设置其比例为1，表示占据状态栏的大部分空间
        self.status_bar.addWidget(self.progress_bar, 1)
        # 把连接按钮添加到状态栏中，设置其为永久部件，表示不会被其他部件替换
        self.status_bar.addPermanentWidget(self.connect_button)

        # 把状态栏添加到下半部分的垂直布局中
        self.bottom_half_layout.addWidget(self.status_bar)

        # 把两个框架对象添加到垂直分割器中
        self.v_splitter.addWidget(self.upper_half)
        self.v_splitter.addWidget(self.bottom_half)
        # 设置分割器中的框架的拉伸系数，让它们能够自适应窗口的大小变化
        self.v_splitter.setStretchFactor(0, 3)
        self.v_splitter.setStretchFactor(1, 1)
        # 设置分割器中的框架的初始大小，让上半部分占460像素，下半部分占140像素
        self.v_splitter.setSizes([460, 140])

        # 创建一个水平布局对象，用于放置目录标签、目录编辑框和切换目录按钮
        self.dir_layout = QHBoxLayout()
        # 把目录标签、目录编辑框和切换目录按钮添加到水平布局中
        self.dir_layout.addWidget(self.dir_label)
        self.dir_layout.addWidget(self.dir_edit)
        self.dir_layout.addWidget(self.dir_button)
        # 设置水平布局的内容边距为8像素，上下边距为0像素
        self.dir_layout.setContentsMargins(8, 0, 8, 0)

        # 创建一个水平布局对象，用于放置左侧的文件列表和右侧的分割器
        self.main_layout = QHBoxLayout()
        # 把左侧的文件列表部件添加到水平布局中，设置其比例为1，表示占据较小的空间
        self.main_layout.addWidget(self.left_layout_widget, 1)
        # 把右侧的分割器部件添加到水平布局中，设置其比例为6，表示占据较大的空间
        self.main_layout.addWidget(self.v_splitter, 6)
        # 设置水平布局的内容边距为0像素，表示没有空隙
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个垂直布局对象，用于放置目录布局和主布局
        self.frame_layout = QVBoxLayout()
        # 设置垂直布局的内容边距为0像素，表示没有空隙
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        # 把目录布局添加到垂直布局中
        self.frame_layout.addLayout(self.dir_layout)
        # 把主布局添加到垂直布局中
        self.frame_layout.addLayout(self.main_layout)

        # 创建一个窗口部件对象，用于容纳垂直布局
        self.frame_widget = QWidget()
        # 把垂直布局设置为窗口部件的布局
        self.frame_widget.setLayout(self.frame_layout)
        # 把窗口部件设置为主窗口的中心部件
        self.setCentralWidget(self.frame_widget)

        # 设置窗口的布局为网格布局
        # self.setLayout(self.layout)
        
        # 设置菜单栏的高度为25像素
        self.menu_bar.setFixedHeight(25)
        # 设置菜单栏的宽度为200像素
        self.menu_bar.setFixedWidth(200)
        # 设置“dir_button”的宽度为80像素
        self.dir_button.setFixedWidth(80)
        # 设置“dir_label”的宽度为80像素
        self.dir_label.setFixedWidth(80)
        # 设置“dir_button”的宽度为80像素
        self.dir_button.setFixedWidth(80)
        # 设置按钮的宽高为80x25
        self.break_button.setFixedSize(80, 25)
        self.clear_button.setFixedSize(80, 25)
        # 设置发送按钮和其选项的大小为80x25
        self.send_button.setFixedSize(80, 25)
        # 设置清空按钮的大小为80x25
        self.clear_console_button.setFixedSize(80, 25)
        # 设置标签的高度为25像素
        self.input_label.setFixedHeight(25)
        self.output_label.setFixedHeight(25)
        self.file_label.setFixedHeight(25)


        # 绑定各个按钮的点击事件到对应的槽函数
        self.dir_button.clicked.connect(ftp_client.change_dir)
        self.upload_button.clicked.connect(ftp_client.upload_file)
        self.quit_button.clicked.connect(ftp_client.quit)
        self.clear_console_button.clicked.connect(self.output_edit.clear)
        # 绑定按钮的点击事件到一个槽函数，用于断开和重新连接
        self.connect_button.clicked.connect(self.toggle_connect)
        # 绑定断点按钮的点击事件到槽函数，用于设置和清除断点
        self.break_button.clicked.connect(self.set_breakpoint)
        self.clear_button.clicked.connect(ftp_client.clear_breakpoint)
        # 绑定按钮的点击事件到一个槽函数，用于处理初始化的操作
        self.init_button.clicked.connect(self.init_data)

        # 绑定信号和槽函数
        # 绑定进度信号到进度条的setValue方法，用于更新进度条的值
        self.progress_signal.connect(self.progress_bar.setValue)
        self.file_dialog_signal.connect(self.show_file_dialog)
        self.error_signal.connect(self.show_error)
        self.icon_signal.connect(self.change_icon)
        # 把信号和一个槽函数连接起来，用于处理命令的执行结果
        self.result.connect(self.handle_result)
        # 把信号和一个槽函数连接起来，用于更新清空进度标签的文本
        self.clear_signal.connect(self.update_clear_label)
        # 把信号和一个槽函数连接起来，用于更新output_edit的内容
        self.output_signal.connect(self.write_output)

        # 绑定列表控件的双击事件到一个槽函数，用于处理双击文件或目录的操作
        self.file_list.itemDoubleClicked.connect(self.double_click_file)
        # 绑定列表控件的右击事件到一个槽函数，用于弹出菜单
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_menu)

    # 定义一个方法，用于设置发送模式
    def set_send_mode(self, key):
        # 判断参数是否是"Enter"
        if key == "Enter":
            # 设置发送模式为"Enter"
            self.send_mode = "Enter"
            # 把发送模式为"Enter"的菜单项设置为选中状态
            self.send_enter_action.setChecked(True)
            # 把发送模式为"Ctrl+Enter"的菜单项设置为未选中状态
            self.send_ctrl_enter_action.setChecked(False)
        else:
            # 设置发送模式为"Ctrl+Enter"
            self.send_mode = "Ctrl+Enter"
            # 把发送模式为"Enter"的菜单项设置为未选中状态
            self.send_enter_action.setChecked(False)
            # 把发送模式为"Ctrl+Enter"的菜单项设置为选中状态
            self.send_ctrl_enter_action.setChecked(True)

    # 处理发送按钮的点击事件的方法
    def send_button_clicked(self):
        # 获取输入框中的内容，去掉首尾的空白字符
        command = self.input_edit.toPlainText().strip()
        # 如果命令不为空
        if command:
            # 把命令按照换行符分割成一个列表，存储到self.commands中
            self.commands = command.split("\n")
            # 把当前执行的命令的索引重置为0
            self.index = 0
            # 清空输入框中的内容
            self.input_edit.clear()
            # 调用一个方法，用于执行命令
            self.execute_command()
        else:
            # 如果命令为空，就什么都不做
            pass

    # 执行一条命令的方法
    def execute_command(self):
        # 如果当前执行的命令的索引小于命令列表的长度，说明还有命令没有执行完
        if self.index < len(self.commands):
            # 获取当前执行的命令
            cmd = self.commands[self.index]
            # 调用FTP客户端对象的方法，把命令发送给服务器
            self.ftp_client.send_command(cmd)
        else:
            # 如果当前执行的命令的索引等于或大于命令列表的长度，说明所有命令都执行完了
            # 把当前执行的命令的索引重置为0
            self.index = 0
            # 把命令列表清空
            self.commands = []

    # 处理命令的执行结果的方法
    def handle_result(self, result):
        # 如果结果为True，说明命令执行成功
        if result:
            # 把当前执行的命令的索引加1，准备执行下一条命令
            self.index += 1
            # 调用一个方法，用于执行命令
            self.execute_command()
        else:
            # 如果结果为False，说明命令执行失败
            # 获取命令列表中剩余的命令
            remaining_commands = self.commands[self.index + 1:]
            # 如果剩余的命令不为空
            if remaining_commands:
                # 把剩余的命令用逗号分隔，拼接成一个字符串
                remaining_commands_str = ", ".join(remaining_commands)
                # 在output_edit中显示一条消息，告知用户后面取消执行的所有命令
                self.output_edit.append(f"由于上一条命令执行失败，以下命令将不会执行：{remaining_commands_str}")
            # 把当前执行的命令的索引重置为0
            self.index = 0
            # 把命令列表清空
            self.commands = []
        
    # 处理窗口关闭事件的方法
    def closeEvent(self, event):
        # 调用FTP客户端的发送命令的方法，把quit命令作为参数传递
        self.ftp_client.send_command("quit")
        # 调用父类的closeEvent方法，完成窗口关闭的操作
        super().closeEvent(event)

    # 更新当前目录和文件列表的方法
    def update_dir_and_file(self, response):
        # 把响应分割为两部分，第一部分是当前目录，第二部分是文件列表
        dir, file = response.split("\n", 1)
        # 把当前目录赋值给属性
        self.ftp_client.current_dir = dir
        # 把当前目录显示在文本框中
        self.dir_edit.setText(self.ftp_client.current_dir)
        # 把文件列表显示在文本框中
        # self.file_edit.setText(file)
        # 清空列表控件中的所有项目
        self.file_list.clear()
        # 创建一个列表项目对象，用于显示返回上级目录的选项
        back_item = QListWidgetItem('..')
        # 设置项目的图标为一个返回的图标
        back_item.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        # 设置项目类型为返回
        back_item.setData(Qt.UserRole, 'back') 
        # 把项目添加到列表控件的最上边
        self.file_list.insertItem(0, back_item)
        # 把文件列表用换行符分割成一个列表，赋值给files
        files = file.split('\n')
        # 循环遍历文件列表
        for file in files:
            # 如果当前目录是\\，就说明是所有磁盘，就直接显示磁盘名
            if self.ftp_client.current_dir == '\\':
                # 创建一个列表项目对象，用于显示磁盘名
                item = QListWidgetItem(file)
                # 设置项目的图标为一个磁盘的图标
                item.setIcon(self.style().standardIcon(QStyle.SP_DriveHDIcon))
                # 设置项目的类型为磁盘
                item.setData(Qt.UserRole, 'drive') 
                # 如果文件名以\结尾，说明是一个目录
            elif file.endswith('\\'):
                # 创建一个列表项目对象，用于显示目录名，去掉结尾的\
                item = QListWidgetItem(file.rstrip('\\'))
                # 设置项目的图标为一个文件夹的图标
                item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
                # 设置项目的类型为目录
                item.setData(Qt.UserRole, 'directory') 
            # 否则，说明是一个文件
            else:
                # 把文件名分割为两部分，第一部分是文件名，第二部分是文件大小（字节）
                size, filename = file.split(' ', 1)
                # 把文件大小转换为整数
                size = int(size)
                # 调用一个函数，根据文件大小选择合适的单位，并返回一个格式化的字符串
                size_str = self.ftp_client.format_size(size)
                # 把文件名和文件大小拼接起来，用括号分隔
                file = filename
                # 创建一个列表项目对象，用于显示文件名和文件大小
                item = QListWidgetItem(file)
                # 设置项目的图标为一个文件的图标
                item.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
                # 设置项目的类型为文件
                item.setData(Qt.UserRole, 'file') 
                # 设置项目的文件大小属性为字节单位的大小
                item.setData(Qt.UserRole + 1, size)
            # 把项目添加到列表控件中
            self.file_list.addItem(item)

    # 定义一个方法，用于设置所有控件的可用状态
    def set_enabled(self, enabled):
        # 为了避免findChildren方法在当前代码环境下覆盖后续单个控件的设置，这里采用逐个控件地设置的方式
        # 这样做可能会降低程序的效率和可读性，建议寻找更好的解决方案
        # 设置目录标签、目录编辑框和切换目录按钮的可用状态
        self.dir_label.setEnabled(enabled)
        self.dir_edit.setEnabled(enabled)
        self.dir_button.setEnabled(enabled)
        # 设置文件标签和文件列表的可用状态
        self.file_label.setEnabled(enabled)
        self.file_list.setEnabled(enabled)
        # 设置断点按钮和清除按钮的可用状态
        self.break_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        # 设置退出按钮、初始化按钮和清空控制台按钮的可用状态
        self.quit_button.setEnabled(enabled)
        self.init_button.setEnabled(enabled)
        self.clear_console_button.setEnabled(enabled)
        # 设置连接按钮的可用状态
        self.connect_button.setEnabled(enabled)
        # 设置上传按钮和发送按钮的可用状态
        self.upload_button.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        # 设置进度标签和进度条的可用状态
        self.progress_label.setEnabled(enabled)
        self.progress_bar.setEnabled(enabled)

    # 定义一个方法，用于弹出文件对话框，获取文件名，并返回给客户端类
    def select_file(self):
        # 弹出一个文件选择对话框，让用户选择要上传的文件
        filename, _ = QFileDialog.getOpenFileName(self, "选择文件", ".", "所有文件 (*)")
        # 返回文件名
        return filename

    # 定义一个槽函数，用于更新标签的文本
    def update_clear_label(self, percent):
        # 把百分比参数转换为字符串，写到标签的文本中
        self.clear_label.setText(f"清空进度：{percent}%")

    # 定义一个槽函数，用于接收信号的参数，并弹出文件对话框
    # 在show_file_dialog方法中，不再发送文件名给子线程，而是把它们放入队列中
    def show_file_dialog(self, filename):
        # 弹出一个文件保存对话框，让用户选择保存的位置和文件名
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存文件", filename, "所有文件 (*)"
        )
        # 如果文件名不为空，就把文件名放入队列中
        if filename:
            self.ftp_client.file_queue.put(filename)
        # 否则，如果文件名为空，就把一个空字符串放入队列中，表示用户没有选择文件
        else:
            self.ftp_client.file_queue.put("")

    # 定义一个槽函数，用于接收信号的参数，并弹出错误提示框
    def show_error(self, error):
        # 创建一个消息框对象，设置标题，图标，文本，按钮等属性
        msg_box = QMessageBox()
        msg_box.setWindowTitle("错误")
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setText(error)
        msg_box.setStandardButtons(QMessageBox.Ok)
        # 显示消息框
        msg_box.exec_()

    # 定义一个槽函数，用于处理双击文件或目录的操作
    def double_click_file(self, item):
        # 获取双击的项目的类型
        item_type = item.data(Qt.UserRole)
        # 如果类型是返回，说明是返回上级目录的选项，就发送一个cd ..命令，返回上一级目录
        if item_type == "back":
            self.ftp_client.send_command("cd ..")
        # 否则，如果类型是目录或磁盘，就发送一个cd命令，切换到该目录
        elif item_type == "directory" or item_type == "drive":
            self.ftp_client.send_command("cd " + item.text())
        # 否则，如果类型是文件，就发送一个get命令，下载该文件
        elif item_type == "file":
            self.ftp_client.send_command("get " + item.text())

    # 定义一个槽函数，用于接收信号的参数，并改变按钮的图标
    def change_icon(self, icon_name):
        # 从字典中获取对应的QStyle值，如果没有找到，就用默认的图标
        icon = ICONS.get(icon_name, QStyle.SP_DialogApplyButton)
        # 调用按钮的setIcon方法，传入对应的图标
        self.connect_button.setIcon(self.style().standardIcon(icon))

    # 定义一个槽函数，用于设置断点
    def set_breakpoint(self):
        # 如果当前正在传输文件，就询问是否要自动获取断点
        if self.ftp_client.filesize > 0:
            # 创建一个消息框对象，设置标题，图标，文本，按钮等属性
            msg_box = QMessageBox()
            msg_box.setWindowTitle('设置断点')
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setText('是否要自动获取断点？')
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            # 显示消息框，并获取用户的选择
            choice = msg_box.exec_()
            # 如果用户选择是，就自动获取断点
            if choice == QMessageBox.Yes:
                # 如果当前在上传文件，就获取已上传到服务器的文件大小，发送restart命令
                if self.ftp_client.sent > 0:
                    # 用os.path.basename函数来提取出文件名
                    base_filename = os.path.basename(self.ftp_client.filename)
                    # 获取当前文件名为base_filename的列表项目
                    self.write_output(base_filename)
                    items = self.file_list.findItems(base_filename, Qt.MatchExactly)
                    # 如果找到了列表项目，就取出第一个
                    if items:
                        item = items[0]
                        # 获取文件大小属性
                        breakpoint = item.data(Qt.UserRole + 1)
                        # 发送restart命令
                        self.ftp_client.send_command("restart " + str(breakpoint))
                    # 否则，说明没有找到列表项目，打印一个错误信息
                    else:
                        self.write_output(f"<font color='orange' face='underline'>没有找到文件名为{base_filename}的列表项目</font>")
                # 否则，如果当前在下载文件，就获取本地已下载的文件大小，发送restart命令
                elif self.ftp_client.received > 0:
                    self.ftp_client.send_command("restart " + str(os.path.getsize(self.ftp_client.download_filename)))
            # 否则，如果用户选择否，就弹出一个输入框，让用户自己输入断点的位置
            else:
                # 弹出一个输入对话框，让用户输入断点的位置（字节）
                breakpoint, ok = QInputDialog.getInt(self, '设置断点', '请输入断点的位置（字节）：')
                # 如果用户输入了一个有效的值，就发送restart命令
                if ok and breakpoint > 0:
                    self.ftp_client.send_command("restart " + str(breakpoint))
                # 否则，在控制台打印取消设置断点的消息
                else:
                    self.write_output("取消设置断点")
        # 否则，如果当前没有传输文件，就弹出一个输入框，让用户自己输入断点的位置
        else:
            # 弹出一个输入对话框，让用户输入断点的位置（字节）
            breakpoint, ok = QInputDialog.getInt(self, '设置断点', '请输入断点的位置（字节）：')
            # 如果用户输入了一个有效的值，就发送restart命令
            if ok and breakpoint > 0:
                self.ftp_client.send_command("restart " + str(breakpoint))
            # 否则，在控制台打印取消设置断点的消息
            else:
                self.write_output("取消设置断点")

    # 定义一个槽函数，用于中断传输，如果已经中断传输，就重新连接并继续传输
    def toggle_connect(self):
        # 如果当前正在传输文件
        if self.ftp_client.filesize > 0:
            # 如果没有中断传输，就关闭socket
            if not self.ftp_client.stopped:
                self.ftp_client.sock.close()
            # 否则，如果已经中断传输，就重新创建一个socket，重新连接服务器
            else:
                self.ftp_client.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.ftp_client.connect_server()
                # 弹出一个消息框对象，询问用户是否要续传文件
                msg_box = QMessageBox()
                msg_box.setWindowTitle('续传文件')
                msg_box.setIcon(QMessageBox.Question)
                msg_box.setText('是否要续传文件？')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                # 获取用户的选择
                choice = msg_box.exec_()
                # 如果用户选择是，就继续上传或下载文件
                if choice == QMessageBox.Yes:
                    self.set_breakpoint()
                    if self.ftp_client.sent > 0:
                        self.ftp_client.send_command("put " + self.ftp_client.filename)
                    elif self.ftp_client.received > 0:
                        self.ftp_client.send_command("get " + self.ftp_client.filename)
                # 否则，如果用户选择否，就什么也不做
                else:
                    pass
                # 设置中断标志为False，修改按钮的图标为暂停
                self.ftp_client.stopped = False
                self.connect_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        # 否则，弹出错误提示框
        else:
            self.show_error("没有正在传输的文件")

    # 定义一个槽函数，用于处理初始化的操作
    def init_data(self):
        # 弹出一个确认对话框，让用户确认是否要初始化所有数据
        msg_box = QMessageBox()
        msg_box.setWindowTitle('初始化')
        msg_box.setIcon(QMessageBox.Question) # 这里设置了图标为一个问号
        msg_box.setText('你确定要初始化所有数据吗？这将删除所有的客户端数据。')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        # 获取用户的选择
        reply = msg_box.exec_()
        # 如果用户选择了是，就初始化所有客户端数据
        if reply == QMessageBox.Yes:
            self.ftp_client.init_data()
        # 否则，如果用户选择了否，就在控制台打印取消初始化的消息
        else:
            self.write_output("取消初始化")

    # 定义一个槽函数，用于显示Changelog的对话框
    def show_changelog(self):
        # 创建一个ChangelogDialog对象，把CHANGELOG常量和自身作为父窗口对象传递给它
        self.changelog_dialog = InfoDialog("Changelog", CHANGELOG, self)
        # 显示ChangelogDialog
        self.changelog_dialog.show()

    # 定义一个槽函数，用于显示帮助对话框
    def show_help(self):
        # 创建一个InfoDialog对象，把"帮助"和HELP作为参数传递给它
        self.help_dialog = InfoDialog("帮助", HELP, self)
        # 显示对话框
        self.help_dialog.show()

    # 定义一个槽函数，用于弹出菜单
    def show_menu(self, pos):
        # 获取当前选中的项目
        item = self.file_list.itemAt(pos)
        # 如果项目不为空，且项目的类型是文件，就创建一个菜单对象
        if item and item.data(Qt.UserRole) == 'file':
            menu = QMenu()
            # 创建一个菜单项目对象，用于显示文件大小
            size_action = menu.addAction('文件大小')
            # 绑定菜单项目的触发事件到一个槽函数，用于弹出文件大小的框
            size_action.triggered.connect(lambda: self.show_size(item))
            # 在鼠标位置显示菜单
            menu.exec_(self.file_list.mapToGlobal(pos))

    # 定义一个槽函数，用于弹出文件大小的框
    def show_size(self, item):
        # 获取项目的文件大小
        size = item.data(Qt.UserRole + 1)
        # 创建一个消息框对象，设置标题，图标，文本，按钮等属性
        msg_box = QMessageBox()
        msg_box.setWindowTitle('文件大小')
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(f'{item.text()}的大小为{size}字节')
        msg_box.setStandardButtons(QMessageBox.Ok)
        # 显示消息框
        msg_box.exec_()

    # 定义一个槽函数，用于更新output_edit的内容
    def write_output(self, text):
        # 把文本追加到output_edit的末尾
        self.output_edit.append(text)
        # 把output_edit的光标移动到末尾，以便显示最新的文本
        self.output_edit.moveCursor(QTextCursor.End)

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