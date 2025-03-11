# setup_logger.py
import json
import logging
from logging import Formatter


class JsonFormatter(Formatter):
    EXTRA_KEYS = ["custom-key"]

    def __init__(self):
        super(JsonFormatter, self).__init__()

    def format(self, record):
        json_record = {}
        json_record["message"] = record.getMessage()
        json_record["level"] = str.replace(str.replace(record.levelname, "WARNING", "WARN"), "CRITICAL", "FATAL")
        if hasattr(self, "EXTRA_KEYS"):
            for key in self.EXTRA_KEYS:
                if val := record.__dict__.get(key, None):
                    json_record[key] = val

        return json.dumps(json_record)


logHandler = logging.StreamHandler()
logHandler.setFormatter(JsonFormatter())

logger = logging.getLogger('uploader')
logger.propagate = False
logger.addHandler(logHandler)
logger.setLevel(logging.DEBUG)
