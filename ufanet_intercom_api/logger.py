import logging
from typing import Any


class SafeLogger(logging.Logger):
    SENSITIVE_KEYS = {
        'password', 'access', 'refresh', 'authorization'
    }

    def __init__(self, name: str):
        super().__init__(name)
        if not self.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: %(name)s %(message)s', style='%')
            handler.setFormatter(formatter)
            self.addHandler(handler)
            self.propagate = False

    def mask_sensitive(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: ('***' if k.lower() in self.SENSITIVE_KEYS and v is not None else self.mask_sensitive(v))
                    for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.mask_sensitive(v) for v in obj]
        return obj

    def safe(self, level: int, msg: str, *args: Any, **kwargs: Any):
        safe_args = tuple(self.mask_sensitive(arg) for arg in args)
        safe_kwargs = {k: self.mask_sensitive(v) for k, v in kwargs.items()}
        super().log(level, msg, *safe_args, **safe_kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any):
        self.safe(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg: str, *args: Any, **kwargs: Any):
        self.safe(logging.DEBUG, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any):
        self.safe(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any):
        self.safe(logging.ERROR, msg, *args, **kwargs)
