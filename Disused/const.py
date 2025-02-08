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
