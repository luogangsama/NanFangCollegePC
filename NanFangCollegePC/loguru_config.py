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

# 控制台输出（开发环境使用）- 启用 backtrace 和 diagnose
logger.add(
    sink=sys.stdout,
    format=log_format,
    level="DEBUG",  # 设置为 DEBUG 以确保捕获所有级别
    colorize=True,
    enqueue=True,  # 线程安全
    backtrace=True,  # 启用异常堆栈跟踪
    diagnose=True,   # 启用变量值诊断信息
    catch=True,      # 捕获所有未处理的异常
)

# 按年月日分目录存储 - 所有级别日志，同样启用 backtrace 和 diagnose
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
    catch=True,      # 捕获所有未处理的异常
)

# 错误日志单独存储（保留更久）- 同样启用 backtrace 和 diagnose
logger.add(
    sink=os.path.join(LOG_DIR, "{time:YYYY}", "{time:MM}", "{time:DD}", "error.log"),
    format=log_format,
    level="ERROR",
    rotation="00:00",
    retention="90 days",  # 错误日志保留90天
    compression="zip",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,  # 记录异常堆栈
    diagnose=True,   # 显示变量值
    catch=True,      # 捕获所有未处理的异常
)

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
    def emit(self, record):
        # 获取对应的 Loguru 级别
        level = record.levelname.lower()
        
        # 查找对应的日志记录函数
        log_function = getattr(logger, level, logger.info)
        
        # 如果有异常信息，确保它被传递
        if record.exc_info:
            # 使用 opt(exception=...) 来记录异常
            log_function.opt(exception=record.exc_info).log(level, record.getMessage())
        else:
            log_function(record.getMessage())

# 配置Django日志拦截
def setup_django_logging():
    """设置Django日志拦截"""
    # 获取所有已有的logger
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    
    # 添加根日志记录器
    root_logger = logging.getLogger()
    root_logger.handlers = [InterceptHandler()]
    root_logger.setLevel(logging.DEBUG)  # 设置为 DEBUG 以捕获所有级别
    
    # 为所有现有logger设置处理器
    for logger_instance in loggers:
        logger_instance.handlers = [InterceptHandler()]
        logger_instance.propagate = False  # 避免重复记录

# 注册日志级别
register_log_levels()

# 自动设置Django日志
setup_django_logging()

# 设置全局异常钩子，确保所有未捕获的异常都被 Loguru 处理:cite[3]
def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局未捕获异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        # 允许键盘中断正常退出
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    # 使用 Loguru 记录异常，包括完整的堆栈跟踪
    logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical("未捕获的全局异常")

# 设置全局异常钩子
sys.excepthook = global_exception_handler

# 示例：测试异常记录
if __name__ == "__main__":
    # 测试1: 直接记录异常
    try:
        1 / 0
    except Exception as e:
        logger.error("发生了一个错误（测试1）")  # 现在即使不使用 opt(exception=True) 也会记录堆栈
    
    # 测试2: 使用 catch 装饰器自动捕获异常:cite[9]
    @logger.catch
    def faulty_function():
        return 1 / 0
    
    faulty_function()  # 这将自动记录异常