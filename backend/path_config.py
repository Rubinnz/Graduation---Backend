import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

def img(path):
    return os.path.join(IMAGES_DIR, path)

def data(path):
    return os.path.join(DATA_DIR, path)

def backend_path(path):
    return os.path.join(BACKEND_DIR, path)
