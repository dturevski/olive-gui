# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from lang import Lang


class YesNoDialog(QtWidgets.QDialog):
    """A dialog with Yes and No buttons."""

    def __init__(self, msg):
        super(YesNoDialog, self).__init__()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(QtWidgets.QLabel(msg))
        vbox.addStretch(1)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        buttonYes = QtWidgets.QPushButton(Lang.value('CO_Yes'), self)
        buttonYes.clicked.connect(self.accept)
        buttonNo = QtWidgets.QPushButton(Lang.value('CO_No'), self)
        buttonNo.clicked.connect(self.reject)

        hbox.addWidget(buttonYes)
        hbox.addWidget(buttonNo)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(':/icons/info.svg')))
