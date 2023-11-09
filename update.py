import subprocess
from UI.utils import kill_subprocess
import time

def update(command,timeout = 5):
    while True:
        cmd = subprocess.Popen(command, shell=True)
        time.sleep(timeout)
        if cmd.poll() is None:
            kill_subprocess(command)
            cmd.communicate()
        else:
            break

if __name__ == "__main__":
    command = "git pull -f"
    update(command)