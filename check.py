# 导入sys模块
import sys

# 打印出已安装的模块列表
print(sys.modules)

# 检查mysql模块是否在列表中
if 'mysql' in sys.modules:
  print('你已经安装了mysql模块')
else:
  print('你还没有安装mysql模块')