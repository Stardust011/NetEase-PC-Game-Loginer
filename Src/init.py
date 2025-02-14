import ctypes
import os
import sys
from pathlib import Path


def _is_admin():
    """检查当前进程是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def _run_as_admin():
    """尝试以管理员权限重新运行当前脚本"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )


def _dir_prefix():
    """检查是否在临时文件夹, 返回完整路径"""
    if getattr(sys, "frozen", False):
        # Running in a bundle
        bundle_dir = Path(sys._MEIPASS)
    else:
        bundle_dir = Path(".")
    return bundle_dir


def get_programdata_path():
    """获取系统ProgramData路径（兼容Windows/Linux）"""
    program_data = Path(os.environ.get("PROGRAMDATA"))
    if not program_data:  # 非Windows系统回退到/etc或用户目录
        if os.name == "posix":
            program_data = Path("/etc")
        else:
            program_data = Path.home()
    return program_data


def get_app_dir():
    """获取应用配置目录的完整路径"""
    app_dir = get_programdata_path() / "NetEase_PC_Game_Loginer"
    app_dir.mkdir(exist_ok=True)  # 自动创建目录
    return app_dir


"""初始化"""
try:
    # 检查管理员权限
    if not _is_admin():
        _run_as_admin()
    dir_path_prefix = _dir_prefix()
    app_dir_path = get_app_dir()
except Exception as e:
    print(f"初始化失败: {e}")
    sys.exit(1)

if __name__ == "__main__":
    print(_dir_prefix())
