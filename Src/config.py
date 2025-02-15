import tomllib

import tomli_w

from Src.init import app_dir_path
from Src.runtimeLog import debug, info, warning, error

_config_file = app_dir_path / "config.toml"


def _load_config() -> dict:
    """保存文件，输入为空时保存全局"""
    try:
        with _config_file.open("rb") as f:
            data = tomllib.load(f)
        info(f"加载配置文件: {_config_file}")
        return data
    except FileNotFoundError:
        # 文件不存在时创建一个新文件
        warning("配置文件不存在，创建新文件")
        _save_config({})
        return _load_config()


def _save_config(data: dict = None):
    if data is None:
        data = cfg
    try:
        with _config_file.open("wb") as f:
            tomli_w.dump(data, f)
        debug(f"自动保存配置文件: {_config_file}", stacklevel=5)
    except:
        error(f"保存配置文件失败")


class AutoConfig(dict):
    def __init__(self, init_flag: bool = False, *args, **kwargs):
        self.init_flag = init_flag
        super().__init__(*args, **kwargs)
        # 将现有嵌套字典转换为Config实例
        for k, v in self.items():
            if isinstance(v, dict) and not isinstance(v, AutoConfig):
                self[k] = AutoConfig(False, v)
        self.init_flag = False

    def __setitem__(self, key, value):
        # 如果设置的是字典，自动转换为AutoDict实例
        if isinstance(value, dict):
            value = AutoConfig(False, value)
        super().__setitem__(key, value)
        if not self.init_flag:
            debug(f"配置变更: {key}={value}", stacklevel=4)
            _save_config()

    def __delitem__(self, key):
        super().__delitem__(key)
        debug(f"配置变更: 删除 {key}", stacklevel=4)
        _save_config()

    def pop(self, key, default=None):
        value = super().pop(key, default)
        if value is not default:
            debug(f"配置变更: 删除 {key}", stacklevel=4)
            _save_config()
        else:
            error(f"配置变更: 未找到 {key}", stacklevel=4)
        return value


# 初始化全局配置
cfg = AutoConfig(True, _load_config())
if "app_dir" not in cfg:
    warning("配置文件缺少app_dir字段，自动添加")
    cfg["app_dir"] = str(app_dir_path)

if "proxy" not in cfg:
    warning("配置文件缺少proxy字段，自动添加")
    cfg["proxy"] = {}

if "certs_path" not in cfg:
    warning("配置文件缺少certs_path字段，自动添加")
    cfg["certs_path"] = {}

# 初始化时可选：将目录路径存入配置（如果需要）
if __name__ == "__main__":
    # print(cfg["proxy"]["port"])
    cfg["proxy"]["port"] = 8443
    pass
    # config = load_config()
    # if 'app_dir' not in config:
    #     config['app_dir'] = str(get_app_dir())
    #     save_config(config)
