from PySide6.QtWidgets import QFrame


class AccountInterface(QFrame):
    # 初始化Widget类，继承自QFrame
    def __init__(self, parent=None):
        super().__init__(parent=parent)  # 调用父类的构造函数
        # 给子界面设置全局唯一的对象名
        self.setObjectName("AccountInterface")
