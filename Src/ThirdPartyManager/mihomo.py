import platform
import subprocess
import threading
import zipfile
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, List, Dict

import httpx
import yaml

from Src.init import app_dir_path
from Src.runtimeLog import debug, info, warning, error

_ARCH_MAPPING = {
    "x86_64": "amd64",
    "amd64": "amd64",
    "i386": "386",
    "armv7l": "armv7",
    "aarch64": "arm64",
    "armv6": "armv6",
    "armv5": "armv5",
}

_EXTENSION_PRIORITY = {
    "linux": [".deb", ".rpm", ".gz"],
    "windows": [".zip"],
    "darwin": [".gz", ".zip"],
}


def normalize_arch(raw_arch: str) -> str:
    """标准化架构名称"""
    arch = raw_arch.lower()
    return _ARCH_MAPPING.get(arch, arch)


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
            _EXTENSION_PRIORITY[os_type].index(ext)
            for ext in _EXTENSION_PRIORITY[os_type]
            if name.endswith(ext)
        ),
        len(_EXTENSION_PRIORITY[os_type]),
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


async def download_main(use_mirror: str = None):
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

    output_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo.zip"
    output_path.parent.mkdir(exist_ok=True)

    info(f"Downloading {selected['name']}...")
    try:
        await download_file(download_url, output_path)
        info(f"Successfully downloaded to {output_path}")
    except Exception as e:
        error(f"Download failed: {str(e)}")
        output_path.unlink(missing_ok=True)

    # 解压ZIP, 并覆盖原先的程序
    if _unzip_and_clean_and_rename(output_path) is False:
        return


def _unzip_and_clean_and_rename(zip_path: Path) -> bool:
    """解压下载来的zip文件，并清理原始zip，修改解压后的文件名称"""
    # 解压
    try:
        with zipfile.ZipFile(zip_path, mode="r") as z:
            z.extractall(zip_path.parent)
    except Exception as e:
        error(f"解压失败 {e}")
        return False
    # 清理原始文件
    zip_path.unlink(missing_ok=True)
    # 重命名为mihomo.exe
    files = [path for path in zip_path.parent.glob("mihomo-*.exe")]
    if len(files) > 1:
        warning("检测到有多个mihomo核心文件，自动取最新创建的文件")
        files.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    elif not files:
        error("未找到 mihomo 核心文件")
        return False

    # 重命名文件
    target_file = files[0]
    target_file.replace(zip_path.parent / "mihomo.exe")
    info(f"重命名(或覆盖) {target_file} 为 mihomo.exe")
    return True


def create_config_mihomo_yaml(ports: int = 8443, tun: bool = True):
    config = {
        "mixed-port": 17890,
        "mode": "rule",
        "tun": {
            "enable": tun,
            "stack": "mixed",
            "dns-hijack": ["any:53"],
            "auto-route": True,
            "auto-detect-interface": True,
        },
        "proxies": [
            {
                "name": "Proxy_HTTP",
                "server": "127.0.0.1",
                "port": ports,
                "type": "http",
                # "tls": True,
                # "skip-cert-verify": True,
                # "alpn": ["http/1.1"],
            }
        ],
        "rules": [
            "PROCESS-NAME, dwrg.exe, Proxy_HTTP",
            # "DOMAIN-SUFFIX,mkey.163.com, Proxy_HTTP",
            "MATCH,DIRECT",
        ],
        "external-controller": "127.0.0.1:9090",
        "external-controller-cors": {
            "allow-origins": ["*"],
            "allow-private-network": True,
        },
    }
    config_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo_config.yaml"
    yaml.dump(config, config_path.open("w", encoding="utf-8"))


def add_process_to_config(process_name: str):
    config_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo_config.yaml"
    c = yaml.full_load(config_path.open("r", encoding="utf-8"))
    c["rules"] = [f"PROCESS-NAME, {process_name}, Proxy_HTTP"] + c["rules"]
    yaml.dump(c, config_path.open("w", encoding="utf-8"))


def check_mihomo_exist() -> int:
    """检查mihomo.exe, mihomo_config.yaml是否存在

    Returns:
        int:
        0: All files exist

        1: mihomo.exe missing

        2: mihomo_config.yaml missing

        3: All missing"""
    config_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo_config.yaml"
    exe_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo.exe"
    if (exe_path.exists() is False) and (config_path.exists() is False):
        return 3
    if exe_path.exists() is False:
        return 1
    if config_path.exists() is False:
        return 2
    return 0


class MihomoManager:
    def __init__(self, config_path: Path = None):
        self.mihomo_process: Optional[subprocess.Popen] = None
        self.mihomo_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo.exe"
        self.work_dir = app_dir_path / "ThirdParty" / "mihomo"

        # 默认配置文件路径
        self.config_path = config_path or self.work_dir / "mihomo_config.yaml"

        # 输出管理
        self.output_queue = Queue()
        self._capture_threads = []
        self._running = False

    def start_mihomo(self):
        """启动mihimo核心

        mihomo.exe -f mihomo_config.yaml -d .
        """
        if self.is_running():
            warning("mihomo已经启动")
            return

        if not self.mihomo_path.exists():
            error(f"mihomo核心文件不存在: {self.mihomo_path}")
            raise FileNotFoundError(f"mihomo.exe not found at {self.mihomo_path}")

        args = [
            str(self.mihomo_path),
            "-f",
            str(self.config_path),
            "-d",
            str(self.work_dir),
        ]

        try:
            self.mihomo_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并错误输出
                cwd=str(self.work_dir),
                bufsize=1,
                universal_newlines=True,
            )
        except Exception as e:
            error(f"启动mihomo失败: {str(e)}")
            raise

        self._running = True

        # 启动输出捕获线程
        self._capture_threads = [
            threading.Thread(
                target=self._enqueue_output,
                args=(self.mihomo_process.stdout,),
                daemon=True,
            )
        ]

        for t in self._capture_threads:
            t.start()

        info("mihomo核心已启动")

    def stop_mihomo(self):
        """停止mihomo进程"""
        if not self.is_running():
            return

        self._running = False

        try:
            # 优雅终止
            self.mihomo_process.terminate()
            self.mihomo_process.wait(timeout=3)
        except ProcessLookupError:
            pass  # 进程已终止
        except TimeoutError:
            warning("强制终止mihomo进程")
            self.mihomo_process.kill()
        finally:
            self.mihomo_process = None
            info("mihomo核心已停止")

    def is_running(self):
        """检查进程是否运行"""
        return self.mihomo_process and self.mihomo_process.poll() is None

    def _enqueue_output(self, stream):
        """输出捕获线程"""
        while self._running:
            try:
                line = stream.readline()
                if line:
                    self.output_queue.put(line.strip())
            except ValueError:
                break  # 流已关闭

    def get_output(self, timeout=0.1):
        """获取捕获的输出"""
        outputs = []
        while True:
            try:
                outputs.append(self.output_queue.get(timeout=timeout))
            except Empty:
                break
        return outputs

    def __del__(self):
        self.stop_mihomo()


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

    # asyncio.run(download_main())
    # create_config_mihomo_yaml()
    # add_process_to_config('test.exe')
    # output_path = app_dir_path / "ThirdParty" / "mihomo" / "mihomo.zip"
    # _unzip_and_clean_and_rename(output_path)

    # manager = MihomoManager()
    #
    # try:
    #     manager.start_mihomo()
    #     sleep(3)
    #     print("运行状态:", manager.is_running())
    #
    #     # 获取实时输出
    #     while manager.is_running():
    #         for line in manager.get_output():
    #             print("[mihomo]", line)
    #         sleep(0.5)
    #
    # finally:
    #     manager.stop_mihomo()

    print(check_exe_and_yaml_exist())
