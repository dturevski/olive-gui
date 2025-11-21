import os
import sys
import logging

def we_are_frozen():
    """Returns whether we are frozen via py2exe or PyInstaller.
    This will affect how we find out where we are located."""
    return hasattr(sys, "frozen") or hasattr(sys, "_MEIPASS")

use_qt_resources = we_are_frozen()
#use_qt_resources = True

if use_qt_resources:
    from PyQt5 import QtCore

def module_path():
    """ This will get us the program's directory,
    even if we are frozen using py2exe or PyInstaller"""

    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        return sys._MEIPASS
    elif hasattr(sys, "frozen"):
        return os.path.dirname(sys.executable)

    return os.path.dirname(__file__)

def get_write_dir():
    if we_are_frozen():
        if local_data := os.getenv('LOCALAPPDATA'):
            return local_data + "/Olive"
        else:
            return os.path.dirname(__file__)
    return "."

def read_resource_file(path):
    if use_qt_resources:
        f, lines = QtCore.QFile(path), []
        f.open(QtCore.QIODevice.ReadOnly)
        text = QtCore.QTextStream(f)
        while not text.atEnd():
            lines.append(text.readLine())
        f.close()
        return lines
    else:
        path = "resources/" + path[1:]
        f, lines = open(path), []
        lines = f.readlines()
        f.close()
        return lines

basedir = module_path()
os.chdir(basedir)

# Ensure write directory exists
write_dir = get_write_dir()
if write_dir != "." and not os.path.exists(write_dir):
    os.makedirs(write_dir, exist_ok=True)

loglevel = logging.ERROR if we_are_frozen() else logging.DEBUG
logging.basicConfig(
    filename=write_dir + '/olive.log',
    level=loglevel,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M',
)
