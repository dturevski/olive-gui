#!/usr/bin/env python

"""olive - GUI for popeye
Usage:
    olive.py [filename]
    filename - YAML collection
"""

import sys
from PyQt4 import QtGui
import gui

def main():
    # loading configs
    gui.Conf.read()
    gui.Lang.read()

    # Qt bootstrap
    app = QtGui.QApplication(sys.argv)

    # loading fonts 
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004d_.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004x_.ttf')
    QtGui.QFontDatabase.addApplicationFont('resources/fonts/gc2004y_.ttf')

    mainframe = gui.Mainframe()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()  