# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets


class PlainTextEdit(QtWidgets.QTextEdit):
    """A QTextEdit that inserts plain text only from MIME data."""

    def __init__(self, *__args):
        super().__init__(*__args)

    def insertFromMimeData(self, data):
        """Override to insert only plain text from clipboard."""
        self.insertPlainText(data.text())
