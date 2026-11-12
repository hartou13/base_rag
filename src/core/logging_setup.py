"""Application logging with secret redaction and a separate, rotated, permission-restricted audit log."""
import logging
import os
import re
import stat
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.rag.services import rag_config as cfg

_REDACTIONS = [
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[REDACTED]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"), "[REDACTED_JWT]"),
    (re.compile(r"(?i)((?:password|passwd|secret|token|api[_-]?key|authorization|sig)[\"']?\s*[=:]\s*)[\"']?[^\s,;\"'&]+"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)([a-z+]+://[^:/\s]+:)[^@\s]+@"), r"\1[REDACTED]@"),
]


def redact(text: str) -> str:
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        return True


def _restrict(path: Path) -> None:
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0600 on POSIX; limited effect on Windows (use folder ACLs)
    except OSError:
        pass


class _SecureTimedHandler(TimedRotatingFileHandler):
    def _open(self):
        stream = super()._open()
        _restrict(Path(self.baseFilename))
        return stream


def setup_logging() -> None:
    log_dir = Path(cfg.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(log_dir, stat.S_IRWXU)
    except OSError:
        pass

    redactor = RedactionFilter()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    def make(name: str, filename: str, level: int) -> None:
        logger = logging.getLogger(name)
        if logger.handlers:
            return
        handler = _SecureTimedHandler(
            log_dir / filename, when="midnight", backupCount=cfg.LOG_RETENTION_DAYS, encoding="utf-8"
        )
        handler.setFormatter(fmt)
        handler.addFilter(redactor)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    make("app", "app.log", logging.INFO)
    # Holds questions and chunks: only readable on the server filesystem, never exposed by the API.
    make("rag.audit", "rag_audit.log", logging.INFO)


def get_logger(name: str = "app") -> logging.Logger:
    return logging.getLogger(name)
