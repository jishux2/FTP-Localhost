# info_dialog.py
# 这是一个InfoDialog类，用于显示各种信息的对话框
# 导入PySide6模块
from PySide6.QtWidgets import (
    QDialog,
    QTextEdit,
    QVBoxLayout,
    QStyle
)

# 定义一个InfoDialog类，继承自QDialog类
class InfoDialog(QDialog):
    # 初始化方法，增加一个title参数，用于设置窗口的标题
    def __init__(self, title, info, parent=None):
        # 调用父类的初始化方法
        super().__init__(parent)
        # 设置窗口的标题，大小，模态
        self.setWindowTitle(title)  # 用title参数来设置窗口的标题
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.resize(400, 300)
        self.setModal(True)
        # 创建一个文本编辑控件，用于显示信息的内容
        self.text_edit = QTextEdit()
        # 设置文本编辑控件为只读，不可编辑
        self.text_edit.setReadOnly(True)
        # 设置文本编辑控件的内容为传递进来的info
        self.text_edit.setText(info)
        # 创建一个垂直布局对象，用于放置文本编辑控件
        self.layout = QVBoxLayout()
        # 把文本编辑控件添加到布局中
        self.layout.addWidget(self.text_edit)
        # 设置窗口的布局为垂直布局
        self.setLayout(self.layout)