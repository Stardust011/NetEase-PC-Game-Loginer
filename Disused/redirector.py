import pydivert
import threading
from Src.runtimeLog import debug, info, warning, error, critical
from Src.config import cfg


class RedirectorProcess:
    def __init__(self):
        self._running = threading.Event()
        self._thread = None
        self._filter_str = "tcp.DstPort == 443 and ip.DstAddr == 127.0.0.1"

    def _capture_loop(self):
        try:
            with pydivert.WinDivert(self._filter_str) as w:
                info(f"开始捕获HTTPS流量 :443 -> :{cfg['proxy']['port']}")
                for packet in w:
                    info(
                        f"捕获 {packet.src_addr}:{packet.src_port} -> {packet.dst_addr}:{packet.dst_port}"
                    )
                    # packet.dst_port = int(cfg["proxy"]["port"])
                    packet.dst_port = 8000
                    w.send(packet)  # 有可能是不支持多线程
        except Exception as e:
            critical(f"捕获进程异常终止: {str(e)}")
        finally:
            info("流量捕获线程已退出")

    def start(self):
        if self.is_running():
            warning("重定向进程已在运行")
            return False

        self._running.set()
        self._thread = threading.Thread(target=self._capture_loop)
        self._thread.start()
        info("流量重定向进程已启动")
        return True

    def stop(self):
        if not self.is_running():
            warning("重定向进程未运行")
            return False

        self._running.clear()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            error("停止进程超时")
            return False
        self._thread = None
        info("流量重定向进程已停止")
        return True

    def is_running(self):
        return self._thread and self._thread.is_alive()


# 单例进程实例
_redirector = RedirectorProcess()


# 公开接口函数
def start_redirector():
    """启动流量重定向进程"""
    return _redirector.start()


def stop_redirector():
    """停止流量重定向进程"""
    return _redirector.stop()


def check_redirector_status():
    """检查进程状态，返回 True 表示运行中"""
    return _redirector.is_running()


if __name__ == "__main__":
    start_redirector()
