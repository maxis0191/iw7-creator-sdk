"""Plain Python launcher of rdoc_inspect.py: python -B rdoc_run.py request.json [--qrenderdoc EXE]."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
QRD = os.environ.get("IWZ_QRENDERDOC", r"C:\Users\ezvalo\Documents\IW7-Paris-Server\tools\renderdoc\RenderDoc_1.46_64\qrenderdoc.exe")
req = os.path.abspath(sys.argv[1])
env = dict(os.environ, IWZ_RDOC_INSPECT=req)
subprocess.run([QRD, "--python", os.path.join(HERE, "rdoc_inspect.py")], env=env, timeout=900, check=False)
