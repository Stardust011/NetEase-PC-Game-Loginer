# coding:utf-8
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon
from qfluentwidgets import NavigationItemPosition, FluentWindow

from Src.GUI.interface.account import AccountInterface
from Src.GUI.interface.home import HomeInterface
from Src.GUI.interface.setting import SettingsInterface
from Src.init import dir_path_prefix
from Src.runtimeLog import debug, info, critical


# class Widget(QFrame):
#     """初始化Widget类，继承自QFrame"""
#     def __init__(self, text: str, parent=None):
#         super().__init__(parent=parent)  # 调用父类的构造函数
#         self.label = SubtitleLabel(text, self)  # 创建一个子标题标签，文本为传入的text
#         self.hBoxLayout = QHBoxLayout(self)  # 创建一个水平布局
#
#         setFont(self.label, 24)  # 设置标签的字体大小为24
#         self.label.setAlignment(Qt.AlignCenter)  # 设置标签的文本对齐方式为居中
#         self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)  # 将标签添加到水平布局中，并设置对齐方式为居中
#
#         # 给子界面设置全局唯一的对象名，对象名由传入的text转换而来，空格替换为'-'
#         self.setObjectName(text.replace(' ', '-'))


class Main(FluentWindow):
    """主界面"""

    def __init__(self):
        super().__init__()

        # 创建子界面
        self.homeInterface = HomeInterface(parent=self)  # 主页面
        self.accountInterface = AccountInterface(parent=self)  # 账号管理页面
        # self.videoInterface = Widget('Video Interface', self)
        self.settingInterface = SettingsInterface(parent=self)  # 设置页面

        self.init_navigation()
        self.init_window()

    def init_navigation(self):
        """添加子界面到导航栏"""
        self.addSubInterface(self.homeInterface, FluentIcon.HOME, "主页")
        self.addSubInterface(
            self.accountInterface, FluentIcon.FINGERPRINT, "渠道服账号管理"
        )
        # self.addSubInterface(self.videoInterface, FluentIcon.VIDEO, 'Video library')
        self.navigationInterface.addSeparator()
        self.addSubInterface(
            self.settingInterface,
            FluentIcon.SETTING,
            "设置",
            NavigationItemPosition.BOTTOM,
        )

    def init_window(self):
        self.resize(800, 494)
        self.setWindowTitle("网易手游PC端登录器")
        icon_path = str(dir_path_prefix / "Assets" / "logo.png")
        self.setWindowIcon(QIcon(icon_path))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # # 创建翻译器实例，生命周期必须和 app 相同
    # translator = FluentTranslator()
    # app.installTranslator(translator)

    # 创建主界面实例
    debug("GUI启动")
    _ = Main()
    try:
        _.show()
        app.exec()
    except Exception as e:
        critical(f"GUI程序异常退出: {e}")
    info("GUI退出")
