# -*- coding: utf-8 -*-

# standard
import os

# 3rd party
from PyQt4 import QtGui, QtCore

# local
        
class ChestView(QtGui.QSplitter):
    
    def __init__(self, Conf, Lang, Mainframe):
        self.Conf, self.Lang, self.Mainframe = Conf, Lang, Mainframe
        super(ChestView, self).__init__(QtCore.Qt.Horizontal)
        
        self.input = InputWidget()
        self.input.setReadOnly(True)
        self.output = OutputWidget(self)
        self.output.setReadOnly(True)
        
        self.btnRun = QtGui.QPushButton('')
        self.btnRun.clicked.connect(self.onRun)
        self.btnStop = QtGui.QPushButton('')
        self.btnStop.clicked.connect(self.onStop)
        
        self.initLayout()
        
        self.Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
 
        self.setActionEnabled(True)
        self.onLangChanged()
        
    def initLayout(self):
        w = QtGui.QWidget()        
        grid = QtGui.QGridLayout()
        grid.addWidget(self.input, 0, 0, 1, 2)
        
        grid.addWidget(self.btnRun, 1, 0)
        grid.addWidget(self.btnStop, 1, 1)
        
        # stretcher
        grid.addWidget(QtGui.QWidget(), 2, 2)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(2, 1)

        w.setLayout(grid)
        self.addWidget(self.output)
        self.addWidget(w)
        self.setStretchFactor(0, 1)    
        
    def onRun(self):
        self.setActionEnabled(False)
        self.output.insertPlainText(QtCore.QString(self.Conf.value('chest-executable')[os.name] + "\n"))
        
    def onStop(self):
        self.setActionEnabled(True)

    def onModelChanged(self):
        self.input.setText(self.Mainframe.model.board.toFen() + " " + self.Mainframe.model.cur()['stipulation'])
    
    def onLangChanged(self):
        self.btnRun.setText(self.Lang.value('CHEST_Run'))
        self.btnStop.setText(self.Lang.value('CHEST_Stop'))
        
    def setActionEnabled(self, status):
        self.btnRun.setEnabled(status)
        self.btnStop.setEnabled(not status)
        
class OutputWidget(QtGui.QTextEdit):
    def __init__(self,  parentView):
        self.parentView = parentView
        super(OutputWidget, self).__init__()

class InputWidget(QtGui.QTextEdit):
    def __init__(self):
        super(InputWidget, self).__init__()
