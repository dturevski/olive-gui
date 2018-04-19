# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets

from gui import *

class Demoframe(Commonframe):


    def __init__(self, app):
        super(Demoframe, self).__init__()
        Mainframe.model = model.Model()

        fontSize = (app.desktop().screenGeometry().height() - 400) >> 3

        Mainframe.fonts = { 'd': QtGui.QFont(
                'GC2004D', fontSize), 'y': QtGui.QFont(
                'GC2004Y', fontSize), 'x': QtGui.QFont(
                'GC2004X', fontSize)}

        self.initLayout()
        self.initFrame()
        self.showFullScreen()

    def initLayout(self):

        # left pane
        widgetLeftPane = QtWidgets.QWidget()
        vboxLeftPane = QtWidgets.QVBoxLayout()
        vboxLeftPane.setSpacing(0)
        vboxLeftPane.setContentsMargins(0, 0, 0, 0)
        self.fenView = FenView(self)
        self.boardView = BoardView(self)

        vboxLeftPane.addWidget(self.fenView)
        vboxLeftPane.addWidget(self.boardView)
        widgetLeftPane.setLayout(vboxLeftPane)

        # right pane
        vboxRightPane = QtWidgets.QVBoxLayout()
        self.chessBox = ChessBox()
        vboxRightPane.addWidget(self.chessBox)
        vboxRightPane.addWidget(Toolbar())
        widgetRightPane = QtWidgets.QWidget()
        widgetRightPane.setLayout(vboxRightPane)

        # putting panes together
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(widgetLeftPane)
        hbox.addWidget(widgetRightPane)

        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        self.centralWidget().setLayout(hbox)

    def initFrame(self):
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap('resources/icons/olive.png')))
        self.setWindowTitle("Demo board")

    def factoryDraggableLabel(self, id):
        return DraggableLabelWithHoverEffect(id)


class DraggableLabelWithHoverEffect(DraggableLabel):

    color1 = QtGui.QColor('#112233')
    color2 = QtGui.QColor('#332211')


    def __init__(self, id):
        super(DraggableLabelWithHoverEffect, self).__init__(id)
        self.setMouseTracking(True)

    def enterEvent(self,event):
        self.setStyleSheet('QLabel { background-color: #42bff4; }')

    def leaveEvent(self,event):
        self.setStyleSheet('QLabel { background-color: #ffffff; }')


class Toolbar(QtWidgets.QWidget):

    def __init__(self):
        super(Toolbar, self).__init__()

        hl =  QtWidgets.QHBoxLayout()
        self.setLayout(hl)

        btnClear = QtWidgets.QPushButton(Lang.value('MI_Clear'))
        btnClear.clicked.connect(self.onClear)
        hl.addWidget(btnClear)

        btnPrev = QtWidgets.QPushButton("<<<")
        btnPrev.clicked.connect(self.onPrev)
        hl.addWidget(btnPrev)

        btnNext = QtWidgets.QPushButton(">>>")
        btnNext.clicked.connect(self.onNext)
        hl.addWidget(btnNext)

    def onClear(self):
        Mainframe.model.board.clear()
        Mainframe.sigWrapper.sigModelChanged.emit()

    def onNext(self):
        c = len(Mainframe.model.entries)
        Mainframe.model.setNewCurrent((Mainframe.model.current+1)%c)
        Mainframe.sigWrapper.sigModelChanged.emit()

    def onPrev(self):
        c = len(Mainframe.model.entries)
        Mainframe.model.setNewCurrent((Mainframe.model.current+c-1)%c)
        Mainframe.sigWrapper.sigModelChanged.emit()