# Desc: Hosts文件管理和DNS-over-HTTPS解析模块
import asyncio
import os
import shutil

from python_hosts import Hosts, HostsEntry

from Src.runtimeLog import info, warning


# --------------------------
# hosts文件管理函数
# --------------------------
def backup_hosts():
    """备份原始 Hosts 文件"""
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    backup_path = r"C:\Windows\System32\drivers\etc\hosts.bak"
    if not os.path.exists(backup_path):
        shutil.copyfile(hosts_path, backup_path)
        info("Hosts 文件已备份到 hosts.bak")


def modify_hosts(operation="add"):
    """添加或删除 Hosts 条目
    - add: 添加条目
    - remove: 删除条目
    """
    hosts = Hosts()
    entry = HostsEntry(
        entry_type="ipv4", address="127.0.0.1", names=["service.mkey.163.com"]
    )

    if operation == "add":
        # 检查是否已存在相同条目
        exists = any(
            e for e in hosts.entries if e.names and "service.mkey.163.com" in e.names
        )
        if not exists:
            hosts.add([entry])
            hosts.write()
            info("Hosts 条目已添加")
        else:
            warning("条目已存在，无需重复添加")
    elif operation == "remove":
        hosts.remove_all_matching(name="service.mkey.163.com")
        hosts.write()
        info("Hosts 条目已删除")
    else:
        warning("无效的操作类型（仅支持 add/remove）")


def restore_hosts():
    """从备份恢复 Hosts 文件"""
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    backup_path = r"C:\Windows\System32\drivers\etc\hosts.bak"
    if os.path.exists(backup_path):
        shutil.copyfile(backup_path, hosts_path)
        info("Hosts 文件已从备份恢复")
    else:
        warning("未找到备份文件")


# --------------------------
# 异步DNS-over-HTTPS解析模块
# --------------------------
from typing import Optional, List
import httpx
import ipaddress


class DoHResolver:
    """DNS-over-HTTPS解析器"""

    def __init__(self, doh_servers: List[str] = None):
        if doh_servers is None:
            doh_servers = [
                "https://doh.pub/dns-query",  # 腾讯云
                "https://dns.alidns.com/dns-query",  # 阿里云
                "https://cloudflare-dns.com/dns-query",  # Cloudflare
                "https://dns.google/dns-query",  # Google
            ]
        self.doh_servers = doh_servers
        self.client = httpx.AsyncClient()
        self.cache = {}  # 简单缓存（生产环境建议使用TTL）

    async def resolve(self, domain: str, record_type: str = "A") -> Optional[str]:
        """
        异步DNS解析（支持A/AAAA记录）

        Args:
            domain: 要解析的域名
            record_type: DNS记录类型（A或AAAA）

        Returns:
            首个有效IP地址（IPv4/IPv6）或None
        """
        if cached := self.cache.get((domain, record_type)):
            return cached

        for server in self.doh_servers:
            try:
                response = await self.client.get(
                    url=server,
                    params={
                        "name": domain,
                        "type": record_type,
                        "ct": "application/dns-json",
                    },
                    headers={"Accept": "application/dns-json"},
                    timeout=3,
                )

                if response.status_code == 200:
                    data = response.json()
                    for answer in data.get("Answer", []):
                        if answer["type"] == (1 if record_type == "A" else 28):
                            ip = answer["data"]
                            if self._validate_ip(ip, record_type):
                                self.cache[(domain, record_type)] = ip
                                return ip
            except Exception as e:
                warning(f"{server} 解析失败: {str(e)}")
                continue

        warning(f"所有服务器解析失败: {domain}")
        return None

    @staticmethod
    def _validate_ip(ip: str, record_type: str) -> bool:
        """验证IP地址格式"""
        try:
            if record_type == "A":
                return isinstance(ipaddress.IPv4Address(ip), ipaddress.IPv4Address)
            elif record_type == "AAAA":
                return isinstance(ipaddress.IPv6Address(ip), ipaddress.IPv6Address)
            return False
        except ipaddress.AddressValueError:
            return False


def doh_resolve(
    domain: str = "service.mkey.163.com", record_type: str = "A"
) -> Optional[str]:
    """同步DNS-over-HTTPS解析"""
    resolver = DoHResolver()
    resolved_ip = asyncio.run(resolver.resolve(domain, record_type))
    if resolved_ip:
        info(f"{domain} 解析结果: {resolved_ip}")
    else:
        warning(f"{domain} 解析失败")
        if domain == "service.mkey.163.com":
            info("检测到默认域名，尝试使用备用IP")
            resolved_ip = "42.186.193.21"  # 默认IP 42.186.193.21 or 42.186.120.246
        else:
            return None
    return resolved_ip


if __name__ == "__main__":
    # import argparse
    # parser = argparse.ArgumentParser(description="管理 Hosts 文件")
    # parser.add_argument("--op", choices=["add", "remove"], required=True, help="操作类型：add 或 remove")
    # args = parser.parse_args()

    # backup_hosts()  # 操作前备份
    # modify_hosts(operation="add")  # 添加条目
    modify_hosts(operation="remove")  # 删除条目
    # modify_hosts(operation=args.op)

    # print(doh_resolve())  # 测试DNS解析

    pass
