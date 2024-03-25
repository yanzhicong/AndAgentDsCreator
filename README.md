# 安卓Agent数据集生成工具




准备工作：

1. 下载adb（android platform-tools），保证命令行里面adb命令是可用的

2. 电脑连手机，设置调试权限，当运行adb devices时有以下输出，则表示手机设置好了：
```
PS C:\Users\yznzh> adb devices
List of devices attached
71aebac8        device
```
注意后面是device而不是unauthorized





数据集单个Task采集步骤：

1. 打开dataset_create.py， 设置task_id，task_description，和output_dir

2. 运行dataset_create.py

3. 等到屏幕输出“Start”后，开始操作手机。

4. 每次操作完一步后点回车再操作下一步

5. 当遇到需要输入文字的操作时，不要在手机屏幕上输入，在命令行内输入要输入的文字，然后点回车，此时该文字会传到手机屏幕上（支持中文输入）。

6. 当所有输入已经完成后，输入“e”或者“end”后回车，程序结束。


