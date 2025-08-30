from sys import stdout
from loguru import logger
import logging

logger.remove()
LOG_FLODER = "./logs"  # 改名为logs，避免与现有目录冲突


# 将 uvicorn 和标准日志转给 loguru
class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging():
    """配置日志记录器"""
    logger.remove()  # 移除默认的处理器，以便重新配置

    # 过滤掉文件变化的调试日志
    def filter_file_changes(record):
        message = str(record["message"])
        # 过滤掉包含 __pycache__ 或 .pyc 的文件变化日志
        if "changes detected" in message and (
            "__pycache__" in message or ".pyc" in message
        ):
            return False  # 过滤掉这些日志
        return True

    # 1. 配置终端输出
    logger.add(
        stdout,
        colorize=True,
        level="DEBUG",
        format="<y><b>{time:MM-DD HH:mm:ss}</b></y> <level><w>[</w>{level}<w>]</w></level> | <level>{message}</level>",
        filter=filter_file_changes,  # 添加过滤器
    )

    # 2. 配置文件输出
    logger.add(
        LOG_FLODER + "/sesame-serve.log",
        level="DEBUG",
        encoding="utf-8",
        format="{time:MM-DD HH:mm:ss} [{level}] {message} | {file} {line}",
        rotation="1 day",
        retention="7 days",
        mode="a",
        enqueue=True,  # 进程安全
        diagnose=False,  # 在多进程环境中建议关闭
        serialize=False,
        filter=filter_file_changes,  # 同样使用过滤器
    )

    # 3. 拦截标准日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 只拦截关键的日志记录器，让其他日志正常输出
    for name in ("fastapi",):
        logging.getLogger(name).handlers = [InterceptHandler()]
        logging.getLogger(name).propagate = False

    # 让 uvicorn 和 watchfiles 的日志正常显示在控制台
    # 但仍然会被我们的文件日志记录
