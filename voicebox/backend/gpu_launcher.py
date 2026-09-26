"""
GPU Launcher — replaces voicebox-server.exe.
Sets OpenVINO env vars, then delegates to venv312 Python which has openvino installed.
"""
import os
import sys
import subprocess

os.environ.setdefault("VOICEBOX_BACKEND", "openvino")
os.environ.setdefault("OPENVINO_DEVICE", "GPU")
os.environ.setdefault("VOICEBOX_DATA_DIR", r"C:\Users\Allen\AppData\Roaming\sh.voicebox.app")

VENV_PYTHON = r"C:\Users\Allen\AppData\Local\voicebox-venv312\Scripts\python.exe"
WORK_DIR    = r"C:\Users\Allen\OneDrive\Desktop\Voicebox\voicebox"

proc = subprocess.Popen(
    [VENV_PYTHON, "-m", "backend.server"] + sys.argv[1:],
    cwd=WORK_DIR,
)
proc.wait()
sys.exit(proc.returncode)
