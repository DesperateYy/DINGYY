# **利用vivado对b210mini进行编程**
## **器件连接**：

目前给我的器材有B210mini,Xilinx下载线。先将b210mini通过tpyec接口连接到电脑，保证vivado可以检测到硬件。然后将下载线的JTAG1*8针脚连接到b210mini的JTAG输出线，根据原理图和实物的对应可知。从B210min引出的端口分别是对应原理图的8号口到13号口，14号口接地可悬空。分别是从8号口的TDO到13号口的GND。为了对应下载线端的针脚，将线的另一端按照下载线针脚的顺序排列，分别是从TMS到VREF，其中NC悬空。最后Xilinx下载线的另一端必须连接到笔记本电脑，这样可以控制代码的写入。
## **程序编写**：

基于vivado编程，需要先下载vivado，然后创建工程，并且选择b210mini的芯片（查看用户手册应该是采用 XC7A200T/XC7A100T ），然后编写代码，完成synthesis和implement，最后生成bit文件，这也是烧入b210mini的最终文件。然后进入 Vivado Hardware Manager，选择fpga设备后烧入bit文件即可。
