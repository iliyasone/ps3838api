import logging
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parent
ROOT_MODULE_DIR = MODULE_DIR.parent.parent

logging.getLogger(__name__).addHandler(logging.NullHandler())
