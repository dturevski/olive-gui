# -*- coding: utf-8 -*-

# standard
import os
import tempfile
import re

# 3rd party
from PyQt5 import QtCore, QtWidgets

# local
import model
import options

CHESTSTIPULATION = re.compile('^([sh]?)([#=])(\d+)(\.5)?$', re.IGNORECASE)


def isOrthodox(fen):
    result = True
    for chr in fen:
        if chr.lower() not in 'kqrbsp12345678/':
            result = False
    # print result, fen
    return result


def checkOption(pbm, option):
    if 'options' not in pbm:
        return False
    for opt in pbm['options']:
        if option in opt:
            return opt
    return False


class ChestView(QtWidgets.QSplitter):

    def __init__(self, Conf, Lang, Mainframe):
        self.Conf, self.Lang, self.Mainframe = Conf, Lang, Mainframe
        super(ChestView, self).__init__(QtCore.Qt.Horizontal)

        self.input = InputWidget()
        self.input.setReadOnly(True)
        self.output = OutputWidget(self)
        self.output.setReadOnly(True)

        self.btnRun = QtWidgets.QPushButton('')
        self.btnRun.clicked.connect(self.onRun)
        self.btnStop = QtWidgets.QPushButton('')
        self.btnStop.clicked.connect(self.onStop)

        self.btnCompact = QtWidgets.QPushButton('')
        self.btnCompact.clicked.connect(self.onCompact)

        self.initLayout()

        self.Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)

        self.setActionEnabled(True)
        self.onLangChanged()

    def initLayout(self):
        w = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout()

        row = 0
        self.labelChest = QtWidgets.QLabel()
        grid.addWidget(self.labelChest, row, 0, 1, 2)
        row += 1

        pathWidget = options.SelectFileWidget(
                self.Lang.value('TC_Chest'),
                self.Conf.chest['path'],
                self.onPathChanged)
        grid.addWidget(pathWidget, row, 0, 1, 2)
        row += 1

        self.labelOptions = QtWidgets.QLabel()
        grid.addWidget(self.labelOptions, row, 0)
        self.inputOptions = QtWidgets.QLineEdit()
        self.inputOptions.setText(str(self.Conf.chest['options']))
        self.inputOptions.textChanged.connect(self.onSettingsChanged)
        grid.addWidget(self.inputOptions, row, 1)
        row += 1

        grid.addWidget(self.input, row, 0, 1, 2)
        row += 1

        grid.addWidget(self.btnRun, row, 0)
        grid.addWidget(self.btnStop, row, 1)
        row += 1

        grid.addWidget(self.btnCompact, row, 0)
        row += 1

        # stretcher
        grid.addWidget(QtWidgets.QWidget(), row, 2)
        grid.setRowStretch(row, 1)
        grid.setColumnStretch(2, 1)

        w.setLayout(grid)
        self.addWidget(self.output)
        self.addWidget(w)
        self.setStretchFactor(0, 1)

    def onRun(self):
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

        chest_exe = self.Conf.chest['path']
        params = self.Conf.chest['options'].split()
        params.append(self.temp_filename)

        self.chestProc.error.connect(self.onFailed)
        self.chestProc.start(chest_exe, params)

    def onOut(self):
        data = self.chestProc.readAllStandardOutput()
        self.output.insertPlainText(QtCore.QString(data))
        # TODO #1: add break for big output

    def onError(self):
        self.output.setTextColor(QtWidgets.QColor(255, 0, 0))
        self.output.insertPlainText(QtCore.QString(
            self.chestProc.readAllStandardError()))
        self.output.setTextColor(QtWidgets.QColor(0, 0, 0))

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
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.output.insertPlainText(self.Lang.value('MSG_Terminated'))
        self.setActionEnabled(True)

    def onModelChanged(self):
        e = self.Mainframe.model.cur()
        brd = self.Mainframe.model.board
        # TODO #2: translate messages
        # self.input.setText(self.Mainframe.model.board.toFen() + " " + self.Mainframe.model.cur()['stipulation'])
        if not CHESTSTIPULATION.match(e['stipulation'].lower()):
            self.input.setText('Stipulation is not supported by Chest')
            self.btnRun.setEnabled(False)
            return

        if not isOrthodox(brd.toFen()):
            self.input.setText('Chest can only solve orthodox problems')
            self.btnRun.setEnabled(False)
            return

        if model.hasFairyElements(e):
            self.input.setText("Chest doesn't support fairy elements")
            self.btnRun.setEnabled(False)
            return

        self.btnRun.setEnabled(True)
        input_str = "LE\nf " + brd.toFen().replace("S", "N").replace("s", "n") + "\n"
        # input_str += "cws\ncwl\ncbs\ncbl\n" #castling

        option = checkOption(e, 'NoCastling')
        if str(
                brd.board[56]) == 'white rook' and str(
                brd.board[60]) == 'white king':
            if not option or 'a1' not in option:
                input_str += 'cwl\n'
        if str(
                brd.board[63]) == 'white rook' and str(
                brd.board[60]) == 'white king':
            if not option or 'h1' not in option:
                input_str += 'cws\n'
        if str(
                brd.board[0]) == 'black rook' and str(
                brd.board[4]) == 'black king':
            if not option or 'a8' not in option:
                input_str += 'cbl\n'
        if str(
                brd.board[7]) == 'black rook' and str(
                brd.board[4]) == 'black king':
            if not option or 'h8' not in option:
                input_str += 'cbs\n'

        option = checkOption(e, 'EnPassant')

        if option:
            aux = option.replace('EnPassant ', '')
            enp = 'e' + aux[0] + ('4' if aux[1] == '3' else '5')
            # print enp
            input_str += enp + "\n"

        # stip preparing
        # better to wrap into a method?
        stip, stipulation, move = e['stipulation'].lower(), {}, 'w'
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
                self.input.setText('Chest cant solve helpmates with halfmoves')
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
            'type-of-play': m.group(1),  # '', s or h
            'goal': m.group(2),  # or =
            # integer
            'full-moves': int(m.group(3)) + [1, 0][m.group(4) is None],
            'side-to-play': ['b', 'w'][(m.group(1) == 'h') != (m.group(4) is None)]}  # w or b
        return retval

    def onLangChanged(self):
        self.labelChest.setText(self.Lang.value('TC_Chest') + ':')
        self.labelOptions.setText(self.Lang.value('Chest_Options') + ':')
        self.btnRun.setText(self.Lang.value('CHEST_Run'))
        self.btnStop.setText(self.Lang.value('CHEST_Stop'))
        self.btnCompact.setText('compact')  # (self.Lang.value('CHEST_Stop'))

    def onCompact(self):
        out = str(self.output.toPlainText())
        out = out.replace("=*=", str("~"))
        aux = out.split('\n')[8:-3]
        # print aux
        self.output.setText('\n'.join(aux))
        pass

    def setActionEnabled(self, status):
        self.btnRun.setEnabled(status)
        self.btnStop.setEnabled(not status)

    def onPathChanged(self, newPath):
        self.Conf.chest['path'] = newPath

    def onSettingsChanged(self):
        try:
            self.Conf.chest['options'] = str(self.inputOptions.text())
        except Exception as e:
            print(e)

class OutputWidget(QtWidgets.QTextEdit):

    def __init__(self, parentView):
        self.parentView = parentView
        super(OutputWidget, self).__init__()


class InputWidget(QtWidgets.QTextEdit):

    def __init__(self):
        super(InputWidget, self).__init__()
