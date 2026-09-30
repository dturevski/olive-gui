# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from lang import Lang


class YesNoCancelDialog(QtWidgets.QDialog):
    """A dialog with Yes, No, and Cancel buttons."""

    def __init__(self, msg):
        super(YesNoCancelDialog, self).__init__()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(QtWidgets.QLabel(msg))
        vbox.addStretch(1)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        buttonYes = QtWidgets.QPushButton(Lang.value('CO_Yes'), self)
        buttonYes.clicked.connect(self.yes)
        buttonNo = QtWidgets.QPushButton(Lang.value('CO_No'), self)
        buttonNo.clicked.connect(self.no)
        buttonCancel = QtWidgets.QPushButton(Lang.value('CO_Cancel'), self)
        buttonCancel.clicked.connect(self.cancel)

        hbox.addWidget(buttonYes)
        hbox.addWidget(buttonNo)
        hbox.addWidget(buttonCancel)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(':/icons/info.svg')))

        self.choice = 'Yes'

    def yes(self):
        self.outcome = 'Yes'
        self.accept()

    def no(self):
        self.outcome = 'No'
        self.accept()

    def cancel(self):
        self.outcome = 'Cancel'
        self.reject()
