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

# 3rd party
from PyQt4 import QtGui, QtCore

# local
import gui

def main():

    # trick to make Windows 7 display the app icon in the taskbar:
    if 'nt' == os.name:
        try:
            myappid = 'OrgYacpdb.OliveShmolive.CurrentVersion'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
            
    # loading configs
    gui.Conf.read()
    gui.Lang.read()

    # Qt bootstrap
    app = QtGui.QApplication(sys.argv)
    
    # required for QSetting to work properly
    QtCore.QCoreApplication.setOrganizationName("OSS");
    QtCore.QCoreApplication.setOrganizationDomain("yacpdb.org");
    QtCore.QCoreApplication.setApplicationName("olive");

     # loading fonts 
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004d_.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004x_.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004y_.ttf')

    mainframe = gui.Mainframe()
    
    # if invoked with "olive.py filename.olv" - read filename.olv
    if len(sys.argv) and sys.argv[-1][-4:] == '.olv':
        mainframe.openCollection(sys.argv[-1])
    
    # entering main loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()  
