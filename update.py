import subprocess
from UI.utils import kill_subprocess

command = "git pull -f"
while True:
    cmd = subprocess.Popen(command, shell=True)
    try:
        cmd.wait(3)
        break
    except:
        kill_subprocess(command)