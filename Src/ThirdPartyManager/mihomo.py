import httpx
import platform
import argparse
import logging
import os
import asyncio
from typing import Optional, List, Dict
from pathlib import Path

from Src.config import cfg
from Src.init import app_dir_path
from Src.runtimeLog import debug, info, warning, error, critical

ARCH_MAPPING = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "i386": "386",
    "armv7l": "armv7",
    "aarch64": "arm64",
    "armv6": "armv6",
    "armv5": "armv5",
}

EXTENSION_PRIORITY = {
    "linux": [".deb", ".rpm", ".gz"],
    "windows": [".zip"],
    "darwin": [".gz", ".zip"],
}


def normalize_arch(raw_arch: str) -> str:
    """标准化架构名称"""
    arch = raw_arch.lower()
    return ARCH_MAPPING.get(arch, arch)


def get_system_info() -> tuple[str, str]:
    """获取系统信息"""
    system = platform.system().lower()
    machine = normalize_arch(platform.machine())
    return system, machine


def get_asset_key(name: str, os_type: str) -> tuple:
    """生成资源排序键值"""
    parts = name.split("-")

    # 扩展名优先级
    ext_priority = next(
        (
            EXTENSION_PRIORITY[os_type].index(ext)
            for ext in EXTENSION_PRIORITY[os_type]
            if name.endswith(ext)
        ),
        len(EXTENSION_PRIORITY[os_type]),
    )

    # 附加信息权重
    has_compatible = "compatible" in parts
    go_version = max(
        (int(p[2:]) for p in parts if p.startswith("go") and p[2:].isdigit()), default=0
    )

    return (
        ext_priority,  # 扩展名优先级
        len(parts),  # 文件名段数（越少越好）
        has_compatible,  # 是否包含兼容标记
        -go_version,  # Go版本（越高越好）
    )


async def fetch_releases() -> Dict:
    """获取最新版本信息"""
    async with httpx.AsyncClient() as client:
        url = "https://api.github.com/repos/MetaCubeX/mihomo/releases/latest"
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def select_asset(assets: List[Dict], os_type: str, arch: str) -> Optional[Dict]:
    """选择最适合的资源文件"""
    target_prefix = f"mihomo-{os_type}-{arch}"
    candidates = []

    for asset in assets:
        name = asset["name"]
        if target_prefix in name and "-" + os_type + "-" in name:
            candidates.append(asset)

    if not candidates:
        return None

    return min(candidates, key=lambda x: get_asset_key(x["name"], os_type))


async def download_file(url: str, path: Path):
    """下载文件并显示进度"""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", 0))
            path.touch(exist_ok=True)
            with open(path, "wb") as f:
                downloaded = 0
                last_reported_percent = 0
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent_complete = (downloaded / total) * 100
                    if percent_complete >= last_reported_percent + 10:
                        last_reported_percent = percent_complete
                        debug(
                            f"Downloaded {downloaded / 1024 / 1024:.1f}MB / {total / 1024 / 1024:.1f}MB"
                        )


async def main(use_mirror: str = None):
    """主函数"""
    os_type, arch = get_system_info()
    info(f"System detected: OS={os_type}, Arch={arch}")

    try:
        release = await fetch_releases()
        info(f"Latest release: {release['tag_name']}")
    except Exception as e:
        error(f"Failed to fetch releases: {str(e)}")
        return
    selected = select_asset(release["assets"], os_type, arch)
    if not selected:
        error("No matching asset found")
        return
    else:
        info(f"Ready to download {selected['name']}")

    # selected = None
    # if args.asset:
    #     selected = next((a for a in release['assets'] if a['name'] == args.asset), None)
    # else:
    #     selected = select_asset(release['assets'], os_type, arch)
    #
    # if not selected:
    #     error("No matching asset found")
    #     return

    download_url = selected["browser_download_url"]
    if use_mirror:
        download_url = download_url.replace("https://github.com", use_mirror)

    # output_path = os.path.join(args.output, selected['name'])
    # os.makedirs(args.output, exist_ok=True)
    output_path = Path(app_dir_path) / "ThirdParty" / "mihomo" / "mihomo.exe"
    output_path.parent.mkdir(exist_ok=True)

    info(f"Downloading {selected['name']}...")
    try:
        await download_file(download_url, output_path)
        info(f"Successfully downloaded to {output_path}")
    except Exception as e:
        error(f"Download failed: {str(e)}")
        output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser(
    #     description="Mihomo Release Downloader",
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter
    # )
    # parser.add_argument("--mirror", help="Mirror site URL")
    # parser.add_argument("--output", default=".", help="Output directory")
    # parser.add_argument("--asset", help="Specify exact asset name")
    # parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    #
    # args = parser.parse_args()

    asyncio.run(main())
