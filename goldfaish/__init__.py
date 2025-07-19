import os
from pathlib import Path

# Path to the forge.exe binary, relative to the package root
#FORGE_BIN_PATH = Path(__file__).parent.parent / 'sandbox' / 'forge' / 'forge.cmd'
#FORGE_BIN_PATH = r"C:\Users\Greg Izatt\src\forge\forge-installer\target\forge-installer-2.0.05-SNAPSHOT\forge.cmd"
FORGE_BIN_DIR = r'C:\Users\Greg Izatt\src\forge\forge-installer\target\forge-installer-2.0.05-SNAPSHOT' "\\"
FORGE_CMD = """java -Xmx4096m "-Dio.netty.tryReflectionSetAccessible=true" "-Dfile.encoding=UTF-8" -jar forge-gui-desktop-2.0.05-SNAPSHOT-jar-with-dependencies.jar"""
