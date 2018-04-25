#!/usr/bin/env python

"""olive - GUI for popeye
Usage:
    olive.py [filename.olv]
    filename.olv - YAML collection
"""

# standard
import sys
import os
import ctypes
import logging

# 3rd party
from PyQt5 import QtGui, QtCore, QtWidgets

# local
import resources
import base
import gui

# logging uncaught exceptions
def excepthook(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sysexcepthook(exc_type, exc_value, exc_traceback)
sysexcepthook = sys.excepthook
sys.excepthook = excepthook

def main():

    # loading configs
    gui.Conf.read()
    gui.Lang.read()

    # trick to make Windows 7 display the app icon in the taskbar:
    if 'nt' == os.name:
        try:
            myappid = 'OrgYacpdb.Olive.CurrentVersion.' + gui.Conf.value('version')
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass


    # Qt bootstrap
    gui.Mainframe.app = QtWidgets.QApplication(sys.argv)

    # required for QSetting to work properly
    QtCore.QCoreApplication.setOrganizationName("OSS")
    QtCore.QCoreApplication.setOrganizationDomain("yacpdb.org")
    QtCore.QCoreApplication.setApplicationName("olive-" + gui.Conf.value('version'))

    # loading fonts
    QtGui.QFontDatabase.addApplicationFont(':/fonts/gc2004d_.ttf')
    QtGui.QFontDatabase.addApplicationFont(':/fonts/gc2004x_.ttf')
    QtGui.QFontDatabase.addApplicationFont(':/fonts/gc2004y_.ttf')

    mainframe = gui.Mainframe()

    # if invoked with "olive.py filename.olv" - read filename.olv
    if len(sys.argv) and sys.argv[-1][-4:] == '.olv':
        mainframe.openCollection(sys.argv[-1])

    # entering main loop
    sys.exit(gui.Mainframe.app.exec_())

if __name__ == '__main__':
    main()
