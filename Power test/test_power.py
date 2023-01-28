def init_power():
    import shutil
    import os
    cmd=os.popen("lsusb")
    res=cmd.read()
    if os.path.exists("power.py"):
        os.remove("power.py")
    if "Future Technology Devices International, Ltd FT232 Serial (UART) IC" in res:
        shutil.copyfile(os.path.join(os.getcwd(),"power_DH.py"),os.path.join(os.getcwd(),"power.py"))
    elif "QinHeng Electronics HL-340 USB-Serial adapter" in res:
        shutil.copyfile(os.path.join(os.getcwd(),"power_PY.py"),os.path.join(os.getcwd(),"power.py"))
    else:
        print("power is not PY or DH")
        return False
    return True
    
init_power()