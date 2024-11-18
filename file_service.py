# file_service.py

import json
import os
import logging

logger = logging.getLogger(__name__)


# Load file
def load_file(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return json.load(f)
    return {}


# Полностью перезаписывает файл новыми данными.
def save_file(data, file_name):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)
