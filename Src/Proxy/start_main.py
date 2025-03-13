"""用于启动代理进程"""

import sys
from typing import Optional

from Src.Proxy.ssl_cert_manager import (
    check_ca_certs_install,
    check_ca_certs_exist,
    build_new_ca_certs,
    install_certificate,
)
from Src.ThirdPartyManager.mihomo import (
    download_main,
    create_config_mihomo_yaml,
    check_mihomo_exist,
    MihomoManager,
)
from Src.ThirdPartyManager.mitmproxy import (
    check_mitmproxy_exist,
    move_plugin_to_app_dir_path,
    MitmproxyManager,
)
from Src.config import cfg
from Src.runtimeLog import info, warning


def check_completeness():
    need_check_again_flag = False
    # 检查CA证书
    if check_ca_certs_install() is False:
        need_check_again_flag = True
        warning("CA证书未安装")
        # 检查是否已有证书文件
        if check_ca_certs_exist() is False:
            if build_new_ca_certs() is False:
                sys.exit(2)
        install_certificate(cfg["certs_path"]["ca_cert"])
    else:
        info("CA证书完整")

    # 检查mihomo核心与配置文件
    _ = check_mihomo_exist()
    if _ != 0:
        need_check_again_flag = True

    if _ == 1:
        # 缺失mihomo.exe
        warning("缺失mihomo.exe, 自动下载")
        download_main()
    elif _ == 2:
        warning("缺失mihomo配置文件，自动创建")
        create_config_mihomo_yaml()
    elif _ == 3:
        warning("缺失mihomo相关组件, 自动处理中")
        download_main()
        create_config_mihomo_yaml()
    else:
        info("mihomo核心与配置文件完整")

    # 检查mitmproxy核心与配置文件
    _ = check_mitmproxy_exist()
    if _ != 0:
        need_check_again_flag = True

    if _ == 1:
        # 缺失mitmdump.exe
        warning("缺失mitmdump.exe, 自动下载")
        # TODO: 未完成
        pass
    elif _ == 2:
        warning("缺失plugin文件，自动创建")
        move_plugin_to_app_dir_path()
    elif _ == 3:
        warning("缺失mitmproxy相关组件, 自动处理中")

        move_plugin_to_app_dir_path()
    else:
        info("mitmproxy核心与配置文件完整")

    if need_check_again_flag:
        return check_completeness()
    else:
        return


Mihomo: Optional[MihomoManager] = None
Mitmproxy: Optional[MitmproxyManager] = None


def start_all():
    global Mihomo, Mitmproxy
    check_completeness()
    # 启动Mihomo
    Mihomo = MihomoManager()
    Mihomo.start_mihomo()

    # 启动Mitmproxy
    Mitmproxy = MitmproxyManager()
    Mitmproxy.start_mitmproxy()

    pass


def stop_all():
    global Mihomo, Mitmproxy
    if Mihomo is not None:
        Mihomo.stop_mihomo()
    if Mitmproxy is not None:
        Mitmproxy.stop_mitmproxy()
    pass


if __name__ == "__main__":
    from rich import print

    start_all()
    while True:
        _ = input()
        if _ == "log":
            m_out = Mihomo.get_output()
            print(f"Mihomo: {m_out}")
            p_out = Mitmproxy.get_output()
            print(f"Mitm: {p_out}")
        else:
            break
    stop_all()
