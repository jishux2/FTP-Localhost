# 导入Qt模块
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit

# 定义一个UserInput类，继承自QPlainTextEdit
class UserInput(QPlainTextEdit):
    # 初始化方法
    def __init__(self, parent):
        # 调用父类的初始化方法
        super().__init__(parent)
        # 把父窗口对象赋值给self.parent
        self.parent = parent

    # 重写按键事件的处理方法
    def keyPressEvent(self, event):
        # 获取按键的值
        key = event.key()
        # 获取按键的修饰符
        modifiers = event.modifiers()
        # 判断按键是否是Enter或Return
        if key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
            # 判断父窗口的发送模式是否是Enter
            if self.parent.send_mode == "Enter":
                # 判断修饰符是否是无修饰符
                if modifiers == Qt.KeyboardModifier.NoModifier:
                    # 调用父窗口的发送按钮的点击事件
                    self.parent.send_button.click()
                # 判断修饰符是否是Ctrl修饰符
                elif modifiers == Qt.KeyboardModifier.ControlModifier:
                    # 在光标位置插入一个换行符
                    self.insertPlainText("\n")
                else:
                    # 调用父类的按键事件处理方法
                    super().keyPressEvent(event)
            # 判断父窗口的发送模式是否是Ctrl+Enter
            elif self.parent.send_mode == "Ctrl+Enter":
                # 判断修饰符是否是Ctrl修饰符
                if modifiers == Qt.KeyboardModifier.ControlModifier:
                    # 调用父窗口的发送按钮的点击事件
                    self.parent.send_button.click()
                else:
                    # 调用父类的按键事件处理方法
                    super().keyPressEvent(event)
        else:
            # 调用父类的按键事件处理方法
            super().keyPressEvent(event)