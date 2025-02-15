import os
import signal
import threading
from socket import SOCK_STREAM
from time import sleep

import psutil

from Src.runtimeLog import debug, warning


def find_listening_pid(port: int):
    """
    查找指定TCP端口的LISTEN状态进程PID
    :param port: 要查找的端口号
    :return: 找到的PID列表（可能有多个）
    """
    try:
        connections = psutil.net_connections()
    except psutil.AccessDenied:
        warning("需要管理员/root权限")
        return []

    pids = []
    for conn in connections:
        try:
            # 筛选条件：TCP协议、LISTEN状态、本地端口匹配
            if (
                conn.type == SOCK_STREAM
                and conn.status == "LISTEN"
                and conn.laddr.port == port
            ):
                debug(conn)
                pids.append(conn.pid)
        except (psutil.AccessDenied, AttributeError):
            continue

    return list(set(pids))  # 去重


def log_pid_details(pid: int):
    try:
        p = psutil.Process(pid)
        debug(f"PID: {pid}")
        debug(f"进程名: {p.name()}")
        debug(f"命令行: {' '.join(p.cmdline())}")
    except psutil.NoSuchProcess:
        warning(f"找不到指定PID进程, PID: {pid}")
        pass


def force_kill(pid: int):
    """
    非阻塞强制终止进程（SIGINT -> SIGKILL）
    通过后台线程实现，主线程不会阻塞
    """

    def _kill_worker():
        # 第一阶段：发送SIGINT
        try:
            debug(f"向进程 {pid} 发送 SIGINT")
            os.kill(pid, signal.SIGINT)
        except ProcessLookupError:
            debug(f"进程 {pid} 已退出")
            return
        except PermissionError:
            warning(f"无权限操作进程 {pid}")
            return
        except Exception as e:
            warning(f"终止进程 {pid} 时发生异常: {str(e)}")
            return

        # 等待1秒
        sleep(1)

        # 第二阶段：检查并发送SIGKILL
        if not psutil.pid_exists(pid):
            debug(f"进程 {pid} 已正常退出")
            return

        debug(f"进程 {pid} 仍在运行，发送强制终止信号")
        try:
            # Windows特殊处理
            if os.name == "nt":
                psutil.Process(pid).kill()
            else:
                os.kill(pid, signal.SIGKILL)
        except (psutil.NoSuchProcess, ProcessLookupError):
            debug(f"进程 {pid} 已终止")
        except Exception as e:
            warning(f"强制终止进程 {pid} 失败: {str(e)}")

    # 创建并启动后台线程
    thread = threading.Thread(
        target=_kill_worker, name=f"KillThread-{pid}", daemon=True  # 设置为守护线程
    )
    thread.start()


if __name__ == "__main__":
    force_kill(find_listening_pid(8443)[0])
