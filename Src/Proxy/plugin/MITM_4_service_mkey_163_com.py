"""
This is for mitmproxy.
This module contains plugins for modifying HTTPS traffic for the service.mkey.163.com domain.
功能：修改游戏登录相关API的请求/响应，添加cv参数，管理登录渠道和二维码登录状态
"""

import json
import re
from urllib.parse import urlencode

from mitmproxy import http

# 常量开始
loginMethod = [
    {
        "name": "手机账号",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 7,
        "icon_url_large": "",
    },
    {
        "name": "快速游戏",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 2,
        "icon_url_large": "",
    },
    {
        "login_url": "",
        "name": "网易邮箱",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 1,
        "icon_url_large": "",
    },
    {
        "login_url": "",
        "name": "扫码登录",
        "icon_url": "",
        "text_color": "",
        "hot": True,
        "type": 17,
        "icon_url_large": "",
    },
]


class PCInfo(dict):
    def __init__(
        self,
        from_game_id: str = "h55",
        src_app_channel: str = "netease",
        src_jf_game_id: str = "h55",
        src_sdk_version: str = "3.15.0",
    ):
        super().__init__()
        self.update(
            {
                "extra_unisdk_data": "",
                "from_game_id": from_game_id,
                "src_app_channel": src_app_channel,
                "src_client_ip": "",
                "src_client_type": 1,
                "src_jf_game_id": src_jf_game_id,
                "src_pay_channel": "netease",
                "src_sdk_version": src_sdk_version,
                "src_udid": "",
            }
        )


pcInfo = PCInfo()
DOMAIN = "service.mkey.163.com"
ExceptAddCVHeaderPaths = [
    r"/mpay/api/users/login/qrcode/exchange_token",
    r"/mpay/api/qrcode",
    r"/mpay/api/reverify",
]


# 常量结束


class Proxy_service_mkey_163_com:
    def __init__(self):
        # self.channel_account_selected = ""
        # self.pending_login_info = None
        # self.cached_qrcode_queue = []

        self.pc_info = pcInfo
        self.login_methods = loginMethod

    # def running(self, loader):
    #     """插件开始运行"""
    #     print("<INFO>插件开始运行</INFO>")

    def request(self, flow: http.HTTPFlow):
        """请求处理入口"""
        DoNotAddCVHeader = False
        # 特殊路径处理开始
        # 外传QRCode创建参数
        if re.compile(r"/mpay/api/qrcode/create_login").match(flow.request.path):
            print(f"<CreateLoginQRCode>{flow.request.path}</CreateLoginQRCode>")
        # 排除不需要添加cv参数的请求
        for path in ExceptAddCVHeaderPaths:
            if re.compile(path).match(flow.request.path):
                DoNotAddCVHeader = True
                break
        # 特殊路径处理结束

        # 修改cv参数到所有非空路径请求, Host: service.mkey.163.com
        if (
            flow.request.path != "/"
            and flow.request.headers.get("Host") == DOMAIN
            and not DoNotAddCVHeader
        ):
            self._add_cv_param(flow)
            print(f"<REQUEST>{flow.request.path}</REQUEST>")

    def response(self, flow: http.HTTPFlow):
        """响应处理入口"""
        # if flow.request.path != "/":
        #     print(f"<REQUEST>{flow.request.path}</REQUEST>")

        try:
            # 处理PC配置 path: /mpay/games/pc_config
            if re.compile(r"/mpay/games/pc_config").match(flow.request.path):
                self._handle_pc_config(flow)

            # 处理登录方法配置 path: /mpay/games/{game_id}/login_methods
            if re.compile(r"/mpay/games/.*/login_methods").match(flow.request.path):
                self._handle_login_methods(flow)

            # 处理设备信息 path: /mpay/games/{game_id}/devices/{device_id}/users/{user_id}
            # 对于 h55 不处理也可
            # if re.compile(r"/mpay/games/.*/devices/.*/users").match(flow.request.path):
            #     self._handle_device_info(flow)

            # 外传QRCode创建参数
            if re.compile(r"/mpay/api/qrcode/create_login").match(flow.request.path):
                self._handle_qrcode_create(flow)

            # 处理QRCODE登录
            if re.compile(r"/mpay/api/users/login/qrcode/exchange_token").match(
                flow.request.path
            ):
                self._handle_qrcode_login(flow)

        except Exception as e:
            print(f"<ERROR>{str(e)}</ERROR>")

    @staticmethod
    def _add_cv_param(flow: http.HTTPFlow, cv: str = "i4.7.0"):
        """为请求修改cv参数
        必要, 不修改登录时会返回不支持错误
        """
        # if "cv" not in flow.request.query:
        #     flow.request.query["cv"] = cv
        # flow.request.query["cv"] = cv

        # 处理POST请求
        if flow.request.method == "POST":
            try:
                if "json" in flow.request.headers.get("Content-Type"):
                    data = json.loads(flow.request.content)
                    data["cv"] = cv
                    data.pop("arch", None)
                    flow.request.content = json.dumps(data).encode()
                else:  # form-data处理
                    body = flow.request.urlencoded_form
                    body["cv"] = cv
                    body.pop("arch", None)
                    flow.request.content = bytes(urlencode(body), "utf-8")
            except Exception as e:
                print(f"<ERROR>POST请求cv参数添加失败:{e}</ERROR>")

    @staticmethod
    def _handle_pc_config(flow: http.HTTPFlow):
        """处理PC配置 path: /mpay/games/pc_config"""
        try:
            response = json.loads(flow.response.content)
            response["game"]["config"]["cv_review_status"] = 1  # 原始数据就是1
            flow.response.content = json.dumps(response).encode()
            # print(f"<PC_CONFIG>{response}</PC_CONFIG>")
            print(f"<INFO>PC CONFIG 已修改</INFO>")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"<ERROR>PC CONFIG 响应格式异常:{e}</ERROR>")

    @staticmethod
    def _handle_login_methods(flow: http.HTTPFlow):
        """处理登录方法配置"""
        try:
            response = json.loads(flow.response.content)
            response["entrance"] = [loginMethod]
            response["select_platform"] = True
            response["qrcode_select_platform"] = True

            # 修改平台配置
            for key in response.get("config", {}):
                response["config"][key]["select_platforms"] = [0, 1, 2, 3, 4]

            flow.response.content = json.dumps(response).encode()

            print(f"<INFO>登录方法配置已修改</INFO>")
        except json.JSONDecodeError:
            print(f"<ERROR>登录方法配置响应不是有效JSON</ERROR>")

    def _handle_device_info(self, flow: http.HTTPFlow):
        """处理设备信息，可能可以实现绕过防沉迷"""
        try:
            response = json.loads(flow.response.content)
            print(f"<DEVICE_INFO>{response}</DEVICE_INFO>")
            response["user"]["pc_ext_info"] = self.pc_info
            flow.response.content = json.dumps(response).encode()
            print(f"<INFO>设备信息已修改</INFO>")
        except (KeyError, json.JSONDecodeError) as e:
            print(f"<ERROR>PC CONFIG 响应格式异常:{e}</ERROR>")

    @staticmethod
    def _handle_qrcode_create(flow: http.HTTPFlow):
        """处理二维码创建"""
        try:
            response = json.loads(flow.response.content)
            print(f"<QRCode>{response}</QRCode>")
        except json.JSONDecodeError:
            print(f"<ERROR>二维码创建响应不是有效JSON</ERROR>")

    @staticmethod
    def _handle_qrcode_login(flow: http.HTTPFlow):
        """处理二维码登录结果，可能可以实现保存上次扫码记录"""
        try:
            response = json.loads(flow.response.content)
            print(f"<QRCodeLogin>{response}</QRCodeLogin>")
        except json.JSONDecodeError:
            print(f"<ERROR>二维码登录响应不是有效JSON</ERROR>")


# mitmproxy插件标准入口
addons = [Proxy_service_mkey_163_com()]
