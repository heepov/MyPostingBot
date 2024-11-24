# file_service.py

import json
import logging
import os

logger = logging.getLogger(__name__)


# Load file
def load_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    else:
        with open(file_path, "w") as f:
            json.dump({}, f)
        return {}


# Полностью перезаписывает файл новыми данными.
def save_file(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
