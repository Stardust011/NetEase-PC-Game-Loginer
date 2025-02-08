from pathlib import Path
import os
import tomllib
import tomli_w

from Src.runtimeLog import debug, info, warning, error, critical
from Src.init import dir_path_prefix, app_dir_path


# def get_programdata_path():
#     # 获取系统ProgramData路径（兼容Windows/Linux）
#     program_data = Path(os.environ.get('PROGRAMDATA', ''))
#     if not program_data:  # 非Windows系统回退到/etc或用户目录
#         if os.name == 'posix':
#             program_data = Path('/etc')
#         else:
#             program_data = Path.home()
#     return program_data
#
# def get_app_dir():
#     # 获取应用配置目录的完整路径
#     app_dir = get_programdata_path() / 'NetEase_PC_Game_Loginer'
#     try:
#         app_dir.mkdir(exist_ok=True)  # 自动创建目录
#         return app_dir
#     except Exception as e:
#         error(f'创建应用目录失败, 回退到当前工作目录', exc_info=True)
#         return Path.cwd()


class Config(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_file = app_dir_path / "config.toml"
        self._load_config()

    def _load_config(self):
        try:
            with self._config_file.open("rb") as f:
                self.update(tomllib.load(f))
            info(f"加载配置文件: {self._config_file}")
        except FileNotFoundError:
            # 文件不存在时创建一个新文件
            warning("配置文件不存在，创建新文件")
            self._save_config()

    def _save_config(self):
        try:
            with self._config_file.open("wb") as f:
                tomli_w.dump(self, f)
            debug(f"自动保存配置文件: {self._config_file}", stacklevel=5)
        except:
            error(f"保存配置文件失败")

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        debug(f"配置变更: {key}={value}", stacklevel=4)
        self._save_config()

    def __delitem__(self, key):
        super().__delitem__(key)
        debug(f"配置变更: 删除 {key}", stacklevel=4)
        self._save_config()

    def pop(self, key, default=None):
        value = super().pop(key, default)
        if value is not default:
            debug(f"配置变更: 删除 {key}", stacklevel=4)
            self._save_config()
        else:
            error(f"配置变更: 未找到 {key}", stacklevel=4)
        return value


# def get_config_path():
#     # 获取配置文件的完整路径
#     return app_dir_path / 'config.toml'
#
# def load_config():
#     """加载TOML配置"""
#     config_file = get_config_path()
#     info(f'加载配置文件: {config_file}')
#     try:
#         with config_file.open('rb') as f:
#             return tomllib.load(f)
#     except FileNotFoundError:
#         # 文件不存在时返回空配置并创建一个新文件
#         warning('配置文件不存在，创建新文件')
#         save_config({})
#         return load_config()
#
# def save_config(config):
#     """保存配置到TOML文件"""
#     config_file = get_config_path()
#     try:
#         with config_file.open('wb') as f:
#             tomli_w.dump(config, f)
#         info(f'保存配置文件: {config_file}')
#     except Exception as e:
#         error(f'保存配置文件失败: {e}')

# 初始化全局配置
cfg = Config()
if "app_dir" not in cfg:
    warning("配置文件缺少app_dir字段，自动添加")
    cfg["app_dir"] = str(app_dir_path)

# 初始化时可选：将目录路径存入配置（如果需要）
if __name__ == "__main__":
    cfg["proxy"]["port"] = 8000
    pass
    # config = load_config()
    # if 'app_dir' not in config:
    #     config['app_dir'] = str(get_app_dir())
    #     save_config(config)
