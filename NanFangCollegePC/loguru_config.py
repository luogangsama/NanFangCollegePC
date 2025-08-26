from loguru import logger
import logging
import os
import sys
from datetime import datetime

# 日志根目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 自定义日志格式
log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 移除所有默认处理器（避免重复日志）
logger.remove()

# 控制台输出（开发环境使用）
logger.add(
    sink=sys.stdout,
    format=log_format,
    level="INFO",
    colorize=True,
    enqueue=True,  # 线程安全
)

# 按年月日分目录存储 - 所有级别日志
logger.add(
    sink=os.path.join(LOG_DIR, "{time:YYYY}", "{time:MM}", "{time:DD}", "all.log"),
    format=log_format,
    level="DEBUG",
    rotation="00:00",  # 每天午夜自动轮转
    retention="30 days",  # 保留30天日志
    compression="zip",  # 自动压缩旧日志
    encoding="utf-8",
    enqueue=True,
    backtrace=True,  # 记录异常堆栈
    diagnose=True,   # 显示变量值
)

# 错误日志单独存储（保留更久）
logger.add(
    sink=os.path.join(LOG_DIR, "{time:YYYY}", "{time:MM}", "{time:DD}", "error.log"),
    format=log_format,
    level="ERROR",
    rotation="00:00",
    retention="90 days",  # 错误日志保留90天
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

# INFO级别日志单独存储
logger.add(
    sink=os.path.join(LOG_DIR, "{time:YYYY}", "{time:MM}", "{time:DD}", "info.log"),
    format=log_format,
    level="INFO",
    rotation="00:00",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    enqueue=True,
)

# 调试日志（可选，按需开启）
# logger.add(
#     sink=os.path.join(LOG_DIR, "{time:YYYY}", "{time:MM}", "{time:DD}", "debug.log"),
#     format=log_format,
#     level="DEBUG",
#     rotation="00:00",
#     retention="7 days",
#     compression="zip",
#     encoding="utf-8",
#     enqueue=True,
# )

# 注册标准日志级别到 loguru
def register_log_levels():
    """注册所有标准日志级别"""
    standard_levels = {
        'DEBUG': logger.level('DEBUG').no,
        'INFO': logger.level('INFO').no,
        'WARNING': logger.level('WARNING').no,
        'ERROR': logger.level('ERROR').no,
        'CRITICAL': logger.level('CRITICAL').no,
    }
    
    for level_name, level_no in standard_levels.items():
        try:
            logger.level(level_name.lower(), level_no)
        except ValueError:
            # 级别已存在，跳过
            pass

# 自定义日志处理器，将 Django 日志转发到 loguru
class InterceptHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.setLevel(level)

    def emit(self, record):
        try:
            # 获取对应的 loguru 级别
            level = record.levelname.lower()
            
            # 查找对应的日志记录函数
            log_function = {
                'debug': logger.debug,
                'info': logger.info,
                'warning': logger.warning,
                'error': logger.error,
                'critical': logger.critical,
            }.get(level, logger.info)
            
            # 记录日志，包含额外的上下文信息
            log_function(
                "[Django] {message}",
                message=record.getMessage(),
                extra={
                    'name': record.name,
                    'module': record.module,
                    'funcName': record.funcName,
                    'lineno': record.lineno,
                    'pathname': record.pathname,
                }
            )
            
        except Exception as e:
            # 避免日志处理本身出错导致循环
            logger.error(f"日志处理错误: {e}")

# 注册日志级别
register_log_levels()

# 配置Django日志拦截
def setup_django_logging():
    """设置Django日志拦截"""
    # 获取所有已有的logger
    loggers = [
        logging.getLogger(name) for name in logging.root.manager.loggerDict
        if not name.startswith('loguru')
    ]
    
    # 添加根日志记录器
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(logging.INFO)
    
    # 为所有现有logger设置处理器
    for logger_instance in loggers:
        logger_instance.handlers = [InterceptHandler()]
        logger_instance.propagate = False  # 避免重复记录

# 自动设置Django日志
setup_django_logging()

# 工具函数：获取日志文件路径
def get_log_file_path(level="all", date=None):
    """获取指定级别和日期的日志文件路径"""
    if date is None:
        date = datetime.now()
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")
    
    return os.path.join(LOG_DIR, year, month, day, f"{level}.log")

# 示例使用
if __name__ == "__main__":
    logger.info("日志系统初始化完成")
    logger.debug("调试信息示例")
    logger.error("错误信息示例")
    
    # 测试获取日志文件路径
    today_log = get_log_file_path("all")
    print(f"今天的日志文件: {today_log}")