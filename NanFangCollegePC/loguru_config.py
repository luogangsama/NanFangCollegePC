from loguru import logger
import logging
import os

# 日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置 loguru 日志文件
logger.add(
    os.path.join(LOG_DIR, "django_runtime.log"),
    rotation="1 day",  # 每天轮换日志
    retention="7 days",  # 保留 7 天的日志
    encoding="utf-8",
    level="DEBUG",
)

# 注册标准日志级别到 loguru
def register_log_levels():
    for level in logging._levelToName.values():
        level_name = level.lower()
        try:
            # 检查日志级别是否已存在
            logger.level(level_name)
        except ValueError:
            # 如果日志级别不存在，注册为与 "INFO" 同优先级的级别
            logger.level(level_name, no=logger.level("INFO").no)

# 自定义日志处理器，将 Django 日志转发到 loguru
class InterceptHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.setLevel(level)

    def emit(self, record):
        level = record.levelname.lower()
        try:
            logger.level(level)  # 检查级别是否存在
        except ValueError:
            level = "info"  # 默认降级到 info

        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(level, record.getMessage())

# 注册日志级别
register_log_levels()
