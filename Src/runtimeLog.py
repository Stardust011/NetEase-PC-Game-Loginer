"""运行时日志记录器"""

import datetime
import logging
import sys
from pathlib import Path
from typing import Optional, Any

from rich.logging import RichHandler

from Src.init import app_dir_path


class RuntimeLogger:
    def __init__(self):
        self._logger = logging.getLogger("runtime_log")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
        self.log_filename = None  # 存储自动生成的日志文件名

        # 保存原始异常处理钩子
        self._original_excepthook = sys.excepthook
        self._setup_global_exception_handler()

        # 初始化标志
        self._console_handler_set = False
        self._file_handler_set = False

    def _setup_global_exception_handler(self):
        """配置全局异常捕获"""

        def exception_handler(exc_type, exc_value, exc_traceback):
            # 提取异常发生位置
            tb = exc_traceback
            while tb.tb_next:
                tb = tb.tb_next
            frame = tb.tb_frame

            # 手动创建精准的日志记录
            record = self._logger.makeRecord(
                name=self._logger.name,
                level=logging.CRITICAL,
                fn=frame.f_code.co_filename,
                lno=tb.tb_lineno,
                msg="未捕获的异常",
                args=None,
                exc_info=(exc_type, exc_value, exc_traceback),
                func=frame.f_code.co_name,
                extra=None,
                sinfo=None,
            )
            self._logger.handle(record)
            self._original_excepthook(exc_type, exc_value, exc_traceback)

        sys.excepthook = exception_handler

    def _ensure_console_handler(self):
        """配置Rich控制台处理器"""
        if not self._console_handler_set:
            console_handler = RichHandler(
                level=logging.DEBUG,
                show_time=True,
                show_level=True,
                show_path=True,
                markup=True,
                log_time_format="[%Y-%m-%d %H:%M:%S]",
                rich_tracebacks=True,  # 启用富文本堆栈跟踪
                tracebacks_show_locals=True,  # 显示本地变量
            )
            self._logger.addHandler(console_handler)
            self._console_handler_set = True

    def _ensure_file_handler(self, file_path: str):
        """配置文件处理器"""
        if not self._file_handler_set:
            file_handler = logging.FileHandler(
                filename=file_path, encoding="utf-8", mode="a"
            )
            file_handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
            self._file_handler_set = True

    def setup(self, file_path: Optional[str] = None):
        """初始化日志处理器并清理旧日志"""
        self._ensure_console_handler()

        if file_path is None:
            # 生成时间戳文件名
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_filename = f"runtime_errors_{current_time}.log"
            logs_path = app_dir_path / "log"
            logs_path.mkdir(exist_ok=True)
            file_path = logs_path / self.log_filename
            self._ensure_file_handler(file_path)
            self._cleanup_old_logs(logs_path)
        else:
            self._ensure_file_handler(file_path)

        self._ensure_file_handler(file_path or "runtime_errors.log")

    def _cleanup_old_logs(self, log_dir: Path, keep: int = 10):
        """清理旧日志文件，保留最近10个"""
        if self.log_filename is None:
            return

        pattern = "runtime_errors_*.log"
        files = list(log_dir.glob(pattern))
        # print(log_dir)

        # 按修改时间排序（旧→新）
        files.sort(key=lambda f: f.stat().st_mtime)

        # 删除超出保留数量的文件
        if len(files) > keep:
            for old_file in files[:-keep]:
                try:
                    old_file.unlink()
                except Exception as e:
                    self._logger.error(
                        f"删除旧日志失败: {str(old_file)}", exc_info=True
                    )

    def _log_with_caller(
        self, level: int, message: str, stacklevel: int = 3, **kwargs: Any
    ):
        """智能日志记录方法"""
        # 自动检测异常上下文
        if level >= logging.ERROR and not kwargs.get("exc_info"):
            kwargs.setdefault("exc_info", sys.exc_info())

        self._logger.log(
            level, message, stacklevel=stacklevel, **kwargs  # 显示实际调用位置
        )

    def debug(self, message: str, **kwargs: Any):
        self._log_with_caller(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any):
        self._log_with_caller(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any):
        self._log_with_caller(logging.WARNING, message, **kwargs)

    def error(self, message: str, exc_info: bool = True, **kwargs: Any):
        self._log_with_caller(
            logging.ERROR, message, exc_info=exc_info and sys.exc_info(), **kwargs
        )

    def critical(self, message: str, exc_info: bool = True, **kwargs: Any):
        self._log_with_caller(
            logging.CRITICAL, message, exc_info=exc_info and sys.exc_info(), **kwargs
        )


# 创建全局实例并自动初始化
runtime_log = RuntimeLogger()
runtime_log.setup()

# 便捷访问方法
debug = runtime_log.debug
info = runtime_log.info
warning = runtime_log.warning
error = runtime_log.error
critical = runtime_log.critical
