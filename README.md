### 安装依赖
执行`pip install PySide6`命令，安装PySide6模块

由于网络限制，中国大陆用户在安装依赖时可能需要设置代理，或者使用清华大学提供的镜像源`-i https://pypi.tuna.tsinghua.edu.cn/simple`来加速下载。

### 使用
运行`python server.py`命令，开启FTP服务器。该服务器是一个后台程序，负责接收和处理客户端的FTP请求。

运行`python main.py`命令，弹出登录窗口。该窗口可以让你连接到FTP服务器，登录或注册用户。

### 功能
- 左侧文件列表显示当前目录的内容，双击文件夹可进入，双击文件可下载，双击返回项可回到上级目录。右键单击文件，即可弹出菜单，显示文件的大小
- 右上控制台呈现FTP客户端的输出，如命令结果，传输信息，错误提示等
- 右下输入框可输入FTP命令，如`ls`, `cd`, `get`, `put`等。`Ctrl+Enter`换行，`Enter`或发送按钮执行。发送按钮菜单可选`Enter`或`Ctrl+Enter`发送模式
- 状态栏位于窗口的底部，用一个进度条展示文件传输的百分比。另外一个标签显示取消下载后释放缓冲区的状态。一个按钮可以切换传输的暂停或继续
- 菜单栏提供了菜单选项，点击后可弹出Changelog或帮助对话框，分别展示程序的更新日志和功能说明

### 运行截图
![image](https://github.com/user-attachments/assets/6357f58c-04c7-4390-9c58-cc848ffc6375)
![image](https://github.com/user-attachments/assets/369d4b9c-a7b2-4d38-a807-6872997b698c)
![image](https://github.com/user-attachments/assets/fd751958-142a-4c58-a85f-19d3a9b996d2)
