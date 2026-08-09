"""
日志系统 — 集中配置，控制台+文件双输出

设计目标：只看日志能还原 90% 的运行现场。

## 用法

```python
from src.core.logging_config import setup_logging
setup_logging()  # 在入口处调用一次
```

## 日志文件

- 位置: `logs/sb-two-tops_YYYY-MM-DD.log`
- 保留: 最近 30 天
- 格式: `[LEVEL] YYYY-MM-DD HH:MM:SS,mmm [module] message`

## 日志约定

| 级别 | 使用场景 |
|------|----------|
| DEBUG | 截图诊断、OCR 原文、模板匹配值 |
| INFO | 状态切换、操作执行、检测结果 |
| WARNING | 截图失败、重试、未预期但可恢复 |
| ERROR | 致命错误、连续失败、截图全黑 |
"""

import logging
import logging.handlers
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# 日志格式
_CONSOLE_FORMAT = (
    "[%(levelname)s] %(asctime)s [%(name)s] %(message)s"
)
_FILE_FORMAT = (
    "[%(levelname)s] %(asctime)s %(name)s: %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志目录
_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"

# 会话 ID（每个进程唯一）
_SESSION_ID: Optional[str] = None


def _session_id() -> str:
    global _SESSION_ID
    if _SESSION_ID is None:
        _SESSION_ID = uuid.uuid4().hex[:8]
    return _SESSION_ID


def _log_dir() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def _log_file_path() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    return _log_dir() / f"sb-two-tops_{today}.log"


def setup_logging(
    level: str = "INFO",
    console: bool = True,
    log_file: bool = True,
    file_level: str = "DEBUG",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 30,
) -> logging.Logger:
    """配置日志系统

    Args:
        level: 控制台日志级别（默认 INFO）
        console: 是否输出到控制台
        log_file: 是否写入文件
        file_level: 文件日志级别（默认 DEBUG）
        max_bytes: 单个日志文件最大字节
        backup_count: 保留日志文件数

    Returns:
        root logger
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # 清除已有 handlers（避免重复调用）
    for h in list(root.handlers):
        root.removeHandler(h)

    # ── 控制台输出 ──
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(ch)

    # ── 文件输出 ──
    if log_file:
        log_path = str(_log_file_path())
        fh = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        fh.setLevel(file_level)
        fh.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
        root.addHandler(fh)

    # 压制 RapidOCR 的详细日志
    logging.getLogger("RapidOCR").setLevel(logging.WARNING)

    # 打印会话头
    logger = logging.getLogger("sb-two-tops.system")
    session = _session_id()
    logger.info("─" * 50)
    logger.info(f"sb-two-tops 会话启动  session={session}")
    logger.info(f"日志级别: level={level} file={file_level}")
    logger.info(f"日志文件: {_log_file_path()}")
    if log_file:
        logger.info(f"日志文件模式: max_bytes={max_bytes} backup={backup_count}")
    logger.info("─" * 50)

    return root


def get_session_id() -> str:
    """获取当前会话 ID"""
    return _session_id()


def get_log_file() -> Optional[Path]:
    """获取当前日志文件路径"""
    p = _log_file_path()
    return p if p.exists() else None