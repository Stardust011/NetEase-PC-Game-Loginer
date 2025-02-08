"""
使用proxy.py库，无法拦截并成功建立HTTPS/1.1连接，但是可以拦截并成功建立HTTP/1.1连接。
Host字段无法被正确解析为域名，导致无法正确建立连接。
放弃使用proxy.py库，使用mitmproxy库。
"""

import ipaddress
import proxy
from proxy.plugin import (
    ProgramNamePlugin,
    ModifyRequestHeaderPlugin,
    RedirectToCustomServerPlugin,
)

from Src.Proxy.plugin.ModifyHttpsTraffic_4_service_mkey_163_com import (
    service_mkey_163_com,
    Test_http1_1,
)

if __name__ == "__main__":
    with proxy.Proxy(
        [
            "--log-level",
            "i",
            "--hostname",
            "0.0.0.0",
            "--port",
            "8443",
            "--ca-key-file",
            "./ca.key",
            "--ca-cert-file",
            "./ca.crt",
            "--ca-signing-key-file",
            "./server.key",
            "--insecure-tls-interception",
            # "--enable-dashboard",
        ],
        plugins=[
            # ProgramNamePlugin,
            # service_mkey_163_com,
            # Test_http1_1,
        ],
    ) as p:
        proxy.sleep_loop()
