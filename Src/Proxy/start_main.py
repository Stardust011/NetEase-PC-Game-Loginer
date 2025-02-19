"""用于启动代理进程"""

import sys

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
)
from Src.ThirdPartyManager.mitmproxy import (
    check_mitmproxy_exist,
    move_plugin_to_app_dir_path,
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


def start_all():
    check_completeness()

    pass


if __name__ == "__main__":
    start_all()
