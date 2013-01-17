# -*- coding: utf-8 -*-

# standard
import os
import tempfile
import re

# 3rd party
from PyQt4 import QtGui, QtCore

# local
import model # really needs?

CHESTCONF = {"hash": 128, "in": "input.txt", "out": "output.txt"}
CHESTSTIPULATION = re.compile('^([sh]?)([#=])(\d+)(\.5)?$', re.IGNORECASE)

def isOrthodox(fen):
    result = True
    for chr in fen:
        if chr.lower() not in 'kqrbsp12345678/':
            result = False
    # print result, fen
    return result

def hasFairyElements(current):
    if model.hasFairyElements(current):
        # print current['options']
        return True
    return False
        
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
        # long verification, simplify this
        if not CHESTSTIPULATION.match(self.Mainframe.model.cur()['stipulation']) \
        or not isOrthodox(self.Mainframe.model.board.toFen()) \
        or hasFairyElements(self.Mainframe.model.cur()):
            return
        self.setActionEnabled(False)
        self.output.clear()
        
        handle, self.temp_filename = tempfile.mkstemp()
        
        input = self.input.toPlainText().toAscii()
        
        os.write(handle, input)
        os.close(handle)
        
        self.chestProc = QtCore.QProcess()
        self.chestProc.readyReadStandardOutput.connect(self.onOut)
        self.chestProc.readyReadStandardError.connect(self.onError)
        self.chestProc.finished.connect(self.onFinished)
        
        chest_exe = self.Conf.value('chest-executable')[os.name]
        params = ["-r", "-LS", "-M " + str(CHESTCONF['hash'])]
        params.append(self.temp_filename)
        
        self.chestProc.error.connect(self.onFailed)
        self.chestProc.start(chest_exe, params)
                
    def onOut(self):
        data = self.chestProc.readAllStandardOutput()
        self.output.insertPlainText(QtCore.QString(data))
        # TODO #1: add break for big output
        
    def onError(self):
        self.output.setTextColor(QtGui.QColor(255,0,0))
        self.output.insertPlainText(QtCore.QString(self.chestProc.readAllStandardError()))
        self.output.setTextColor(QtGui.QColor(0,0,0))
    
    def onFailed(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.setActionEnabled(True)
        # if not self.stop_requested:
        # msgBox("failed " + self.chestProc.error)
        
    def onFinished(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.setActionEnabled(True)
        
    def onStop(self):
        self.chestProc.kill()
        self.setActionEnabled(True)

    def onModelChanged(self):
        # TODO #2: translate messages
        # self.input.setText(self.Mainframe.model.board.toFen() + " " + self.Mainframe.model.cur()['stipulation'])
        self.output.clear()
        if not CHESTSTIPULATION.match(self.Mainframe.model.cur()['stipulation']):            
            self.output.insertPlainText('Stipulation is not suported by Chest')
            return
        
        if isOrthodox(self.Mainframe.model.board.toFen()) == False:
            self.output.insertPlainText('Chest can solve only orthodox problems')
            return
        
        if hasFairyElements(self.Mainframe.model.cur()):            
            self.output.insertPlainText('Chest dont support fairy conditions')
            return
        
        input_str = "LE\nf " + self.Mainframe.model.board.toFen().replace("S", "N").replace("s", "n") + "\n"
        
        # stip preparing
        # better to wrap into a method?
        stip, stipulation, move = self.Mainframe.model.cur()['stipulation'], {}, 'w'
        if '#' in stip:
            stipulation = stip.split('#')
            if stipulation[0] != '':
                input_str += "j" + stipulation[0] + "\n"
        elif '=' in stip:
            stipulation = stip.split('=')
            if stipulation[0] != '':
                input_str += "j" + stipulation[0].upper() + "\n"
            else:
                stipulation[0] = 'O'
        
        if stipulation[0] == 'h' or stipulation[0] == 'H':
            if '.' in stipulation[1]:
                # stipulation[1] = stipulation[1].split('.')[0]
                self.output.insertPlainText('Chest cant solve helpmates with halfmoves')
                return
            else:
                move = 'b'
        input_str += "z" + stipulation[1] + move + "\n"
        
        self.input.setText(input_str)
          
    def checkCurrentEntry(self):
        if model.hasFairyElements(self.Mainframe.model.cur()):
            return None
        m = CHESTSTIPULATION.match(self.Mainframe.model.cur()['stipulation'])
        if not m:
            return None
        retval = {
            'type-of-play':m.group(1), #                                                '', s or h
            'goal':m.group(2), #                                                        # or =
            'full-moves': int(m.group(3)) + [1, 0][m.group(4) is None], #               integer
            'side-to-play':['b', 'w'][(m.group(1) == 'h') != (m.group(4) is None)]} #   w or b
        return retval
    
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
