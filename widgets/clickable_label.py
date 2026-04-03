# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets


class ClickableLabel(QtWidgets.QLabel):
    """A QLabel that opens external links when clicked."""

    def __init__(self, str):
        super(ClickableLabel, self).__init__(str)
        self.setOpenExternalLinks(True)
