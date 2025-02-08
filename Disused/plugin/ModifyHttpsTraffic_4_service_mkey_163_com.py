"""
This is for Proxy.py.
This module contains plugins for modifying HTTPS traffic for the service.mkey.163.com domain.
由于无法正确解析IP与域名的关系，因此无法正确拦截service.mkey.163.com的请求。
"""

import re
from typing import Optional
from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser, httpParserTypes


class service_mkey_163_com(HttpProxyBasePlugin):
    def __init__(self, *args, **kwargs):
        self.needModify = False  # 是否需要修改内容
        self.tempRequest = None  # 临时存储请求
        self.target_paths = [
            re.compile(b"/mpay/games/.*/login_methods"),
            re.compile(b"/mpay/games/.*/devices/.*/users/.*"),
            re.compile(
                b"/mpay/games/pc_config",
            ),
        ]  # 目标路径
        super().__init__(*args, **kwargs)

    def before_upstream_connection(self, request: HttpParser) -> HttpParser:
        print(request.is_http_1_1_keep_alive)

        # 也许去除b'proxy-connection': (b'Proxy-Connection', b'Keep-Alive')会更好
        request.del_header(b"proxy-connection")  # 无效

        if request.path is None:
            print("空路径请求：")

            # print(request.protocol)
            # print(request.headers)
            print(request.headers)
            print(request.path)
            return request  # 忽略空路径请求

        # # 修改请求（示例：修改请求头）
        # if request.host == b'service.mkey.163.com':
        #     print("[+] 拦截到目标域名请求，准备修改内容...")
        #     request.add_header(b'X-Modified-By-Proxy', b'yes')

        # 检查目标域名是否为 service.mkey.163.com
        print("请求：")
        # print(request.protocol)
        print(request.headers)
        print(request.path)

        return request

        # if request.header(b"Host") == b'service.mkey.163.com' and \
        #         any(path.match(request.path) for path in self.target_paths):
        #     print(f"检测到目标请求路径，准备修改内容... {request.path.decode()}")
        #     self.needModify = True
        # self.tempRequest = request # 保存请求
        # return request

    def handle_upstream_chunk(self, chunk: memoryview) -> Optional[memoryview]:
        # return chunk

        # if not self.needModify:
        #     return chunk

        # 解析原始响应
        parser = HttpParser(httpParserTypes.RESPONSE_PARSER)
        response = parser.response(chunk.tobytes())

        print("响应：")
        print(response.is_http_1_1_keep_alive)
        print(response.code)  # 响应状态码
        print(response.headers)  # 响应头
        print(response.body)  # 响应体

        # 修改响应（示例：替换响应体）

        # # 仅处理JSON响应
        # if b"application/json" not in response.header(b"Content-Type"):
        #     return chunk
        #
        # print(self.tempRequest.path)
        #
        # try:
        #     modified = False
        #     json_data = json.loads(response.body.decode('utf-8'))
        #
        #     # 路径1: 登录方式修改 /mpay/games/.*/login_methods
        #     if self.target_paths[0].match(self.tempRequest.path):
        #         print("修改登录方式响应")
        #         json_data["entrance"] = [loginMethod]  # TODO: 移植loginMethod数据结构
        #         json_data["select_platform"] = True
        #         json_data["qrcode_select_platform"] = True
        #         for _ in json_data["config"]:
        #             json_data["config"][_]["select_platforms"] = [0, 1, 2, 3, 4]
        #         modified = True
        #
        #     # 路径2: PC配置修改
        #     elif self.target_paths[2].match(parser.path):
        #         print("[+] 修改PC配置响应")
        #         if "game" in json_data and "config" in json_data["game"]:
        #             json_data["game"]["config"]["cv_review_status"] = 1
        #             modified = True
        #
        #     # 路径3: 用户登录信息
        #     elif self.target_paths[1].match(parser.path):
        #         print("[+] 修改用户登录响应")
        #         if "user" in json_data and "pc_ext_info" in json_data["user"]:
        #             json_data["user"]["pc_ext_info"] = ...  # TODO: 移植pcInfo数据结构
        #             modified = True
        #
        #     if modified:
        #         # 重建响应头和内容
        #         new_body = json.dumps(json_data).encode()
        #         parser.body = new_body
        #         parser.update_header(b"Content-Length", str(len(new_body)).encode())
        #         return memoryview(parser.build_response())
        #
        # except Exception as e:
        #     print(f"响应修改失败: {str(e)}")
        #
        # # 重新封装为 memoryview 对象(chunk)
        # response.parse(chunk)

        return chunk


class Test_http1_1(HttpProxyBasePlugin):
    def before_upstream_connection(self, request: HttpParser) -> HttpParser:
        print(request.is_http_1_1_keep_alive)
        return request

    def handle_upstream_chunk(self, chunk: memoryview) -> Optional[memoryview]:
        return chunk

    def handle_client_request(self, request: HttpParser) -> Optional[HttpParser]:
        print(request.is_http_1_1_keep_alive)
        return request

    def handle_client_data(self, raw: memoryview) -> Optional[memoryview]:
        parser = HttpParser(httpParserTypes.RESPONSE_PARSER)
        response = parser.response(raw.tobytes())
        print(response.is_http_1_1_keep_alive)
        return raw
