import re
import shutil
import subprocess
import threading
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

from Src.Proxy.process_port_manager import (
    find_listening_pid,
    log_pid_details,
    force_kill,
)
from Src.init import app_dir_path
from Src.runtimeLog import debug, info, warning, error


def download():
    pass


def check_mitmproxy_exist():
    """检查mitmdump.exe, plugin是否存在

    Returns:
        int:
        0: All files exist

        1: mitmdump.exe missing

        2: plugin missing

        3: All missing"""
    exe_path = app_dir_path / "ThirdParty" / "mitmproxy" / "mitmdump.exe"
    plugin_path = (
        app_dir_path / "ThirdParty" / "mitmproxy" / "MITM_4_service_mkey_163_com.py"
    )
    if (exe_path.exists() is False) and (plugin_path.exists() is False):
        return 3
    if exe_path.exists() is False:
        return 1
    if plugin_path.exists() is False:
        return 2
    return 0


def move_plugin_to_app_dir_path():
    mv_to_file = (
        app_dir_path / "ThirdParty" / "mitmproxy" / "MITM_4_service_mkey_163_com.py"
    )
    # ../../Proxy/plugin/MITM_4_service_mkey_163_com.py
    original_file = (
        Path(__file__).parents[1]
        / "Proxy"
        / "plugin"
        / "MITM_4_service_mkey_163_com.py"
    )
    if not original_file.exists():
        # import sys
        # original_file = Path(sys.executable) / 'packup' / 'MITM_4_service_mkey_163_com.py'
        original_file = (
            Path(__file__).absolute().parent
            / "packup"
            / "MITM_4_service_mkey_163_com.py"
        )
    shutil.copy(original_file, mv_to_file)
    info("已将mitmproxy插件复制到应用目录下")


class MitmproxyManager:
    def __init__(self, port=8443):
        self.port = port
        self.mitmproxy_process: Optional[subprocess.Popen] = None
        self.mitmproxy_path = app_dir_path / "ThirdParty" / "mitmproxy" / "mitmdump.exe"

        # 输出管理相关属性
        self.output_queue = Queue()
        self._capture_threads = []
        self._running = False

    def start_mitmproxy(self):
        """启动mitmproxy并开始捕获输出"""
        if self.is_running():
            warning("[italic yellow] MITM :[/italic yellow] mitmproxy已经启动")
            return

        certs_dir = app_dir_path / "certs"
        script_path = self.mitmproxy_path.parent / "MITM_4_service_mkey_163_com.py"

        args = [
            str(self.mitmproxy_path),
            "--set",
            f"confdir={certs_dir}",
            "-k",  # 忽略SSL错误
            # "-q", # 静默运行
            "-p",
            str(self.port),
            "-s",
            str(script_path),
        ]

        try:
            self.mitmproxy_process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                bufsize=1,  # 行缓冲
                universal_newlines=True,
            )
        except FileNotFoundError:
            error(
                f"[italic yellow] MITM :[/italic yellow] mitmdump.exe not found at {self.mitmproxy_path}"
            )
            raise RuntimeError(f"mitmdump.exe not found at {self.mitmproxy_path}")

        self._running = True

        # 捕获stdout
        self._capture_threads = [
            threading.Thread(
                target=self._enqueue_output,
                args=(self.mitmproxy_process.stdout,),
                daemon=True,
            ),
            # threading.Thread(target=enqueue_output, args=(self.mitmproxy_process.stderr, 'STDERR'), daemon=True)
        ]

        for t in self._capture_threads:
            t.start()

        info(
            f"[italic yellow] MITM :[/italic yellow] mitmproxy started on port {self.port}"
        )

    def stop_mitmproxy(self):
        """停止mitmproxy进程"""
        if not self.is_running():
            return

        self._running = False  # 停止捕获线程

        try:
            # 先尝试优雅终止
            self.mitmproxy_process.terminate()
            self.mitmproxy_process.wait(timeout=2)  # 等待进程完全退出
        except ProcessLookupError:
            pass  # 进程已经结束
        except TimeoutError:
            # self._force_kill()
            pass  # 无论退不退出都需要强制关闭（可能是windows特性？）
        finally:
            self.mitmproxy_process = None
            self._force_kill()
            info("[italic yellow] MITM :[/italic yellow] mitmproxy stopped")

    def _force_kill(self):
        """
        查找指定TCP端口的LISTEN状态进程PID, 然后发送终止信号
        """

        pids = find_listening_pid(self.port)

        try:
            pid = pids[0]
            if len(pids) > 1:
                warning(
                    f"[italic yellow] MITM :[/italic yellow] 检测到多个pid占用，默认kill第一个 PID:{pid}"
                )
            log_pid_details(pid)
            force_kill(pid)
        except IndexError:
            warning("[italic yellow] MITM :[/italic yellow] 未检测到端口占用")
            pass

    def is_running(self):
        """检查进程是否正在运行"""
        return (
            self.mitmproxy_process is not None and self.mitmproxy_process.poll() is None
        )

    def _enqueue_output(self, stream):
        debug("[italic yellow] MITM :[/italic yellow] 捕获线程启动")
        p = re.compile(r"<.*>(.*)</.*>")
        s = re.compile(r".*proxy listening at.*")
        while self._running:
            try:
                line = stream.readline().strip()
                if s.match(line):
                    self._log_out(line)
                    self.output_queue.put(line.strip())
                if p.match(line):
                    self._log_out(line)
                    self.output_queue.put(line.strip())
            except ValueError:  # 当流关闭时可能发生
                break

    def _log_out(self, line):
        p = re.compile(r"<(.*)>(.*)</.*>")
        try:
            if p.match(line):
                name, msg = p.findall(line)[0]
                try:
                    eval(
                        f"{name.lower()}('[italic yellow] MITM :[/italic yellow] {msg}')"
                    )
                except NameError:
                    eval(
                        f"info('[italic yellow] MITM :[/italic yellow] {name}事件已捕获')"
                    )
                    # TODO: 处理捕获后事件
            else:
                eval(f"info('[italic yellow] MITM :[/italic yellow] {line}')")
        except Exception as e:
            error(f"[italic yellow] MITM :[/italic yellow] 未知错误: {e}")

    def get_output(self, timeout=0.1):
        """
        获取捕获的输出内容
        返回： message 的列表
        """
        outputs = []
        while True:
            try:
                outputs.append(self.output_queue.get(timeout=timeout))
            except Empty:
                break
        return outputs

    def __del__(self):
        self.stop_mitmproxy()


# 使用示例
if __name__ == "__main__":

    manager = MitmproxyManager()

    try:
        manager.start_mitmproxy()
        input()
        for message in manager.get_output():
            print(f"{message}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        manager.stop_mitmproxy()

    # sleep(10)
    # def run_mitmproxy(self):
    #     p = multiprocessing.Process(target=self.start_mitmweb)
    #     p.start()
    #     input("Press Enter to stop mitmweb...\n")
    #     self.stop_mitmweb()
    #     p.join()


# if __name__ == '__main__':
# #     # move_plugin_to_app_dir_path()
#     m = MitmproxyManager()
#     m.start_mitmproxy()
#     input()
# #     m.mitmproxy_process.communicate(input=None, timeout=1)
# #     print(m.mitmproxy_process.stdout)
#     m.stop_mitmproxy()
