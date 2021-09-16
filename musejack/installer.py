import os
import sys

import logging
logging.basicConfig(level=logging.INFO)

Log = logging.getLogger(__name__)
class Installer:

    def check_jack_installed_version(self):
        pass

class WindowsInstaller(Installer):

    def __init__(self):
        Log.info("Detected Windows system")

    def check_jack_installed_version(self):
        #open a commandline, and run
        stream = os.popen('cmd /c "jackd --version"')
        out = stream.readline()
        #if jackd is installed, it will return something like 'jackdmp version 1.9.19 tmpdir server protocol 9'
        if out.startswith("jackdmp version "): #version found
            version = out.removeprefix("jackdmp version ").split()[0]
            return version
        else:
            return None





class MacOSInstaller(Installer):
    pass


if sys.platform.startswith("win"):
    installer = WindowsInstaller()
else:
    installer = MacOSInstaller()



version = installer.check_jack_installed_version()

if version is None:
    #install jack
    pass
else:
    Log.info(f"Jack version found! version={version}")