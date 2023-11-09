import subprocess
from UI.utils import kill_subprocess
import time

command = "git pull -f"
while True:
    cmd = subprocess.Popen(command, shell=True)
    time.sleep(5)
    if cmd.poll() is None:
        kill_subprocess(command)
        cmd.communicate()
    else:
        break