# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import model


class DraggableLabel(QtWidgets.QLabel):

    def __init__(self, id):
        super(DraggableLabel, self).__init__()
        self.id = id

    def setTextAndFont(self, text, font):
        # Import Mainframe locally to avoid circular import
        from gui import Mainframe
        self.setText(text)
        self.setFont(Mainframe.fontset()[font])

    # mouseMoveEvent works as well but with slightly different mechanics
    def mousePressEvent(self, e):
        # Import Mainframe locally to avoid circular import
        from gui import Mainframe
        
        Mainframe.sigWrapper.sigFocusOnPieces.emit()
        if e.buttons() != QtCore.Qt.LeftButton:
            # On right click
            # if the square is empty, add the selected piece
            # if the square is non-empty, remove it
            if Mainframe.model.board.board[self.id] is None:
                if Mainframe.selectedPiece is not None:
                    Mainframe.model.board.add(model.Piece(Mainframe.selectedPiece.name,
                                                          Mainframe.selectedPiece.color,
                                                          Mainframe.selectedPiece.specs),
                                              self.id)
                else:
                    return
            else:
                Mainframe.selectedPiece = Mainframe.model.board.board[self.id]
                Mainframe.model.board.drop(self.id)
            Mainframe.model.onBoardChanged()
            Mainframe.sigWrapper.sigModelChanged.emit()
            return
        if Mainframe.model.board.board[self.id] is None:
            return

        # ctrl-drag copies existing piece
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        Mainframe.currentlyDragged = Mainframe.model.board.board[self.id]
        if not (modifiers & QtCore.Qt.ControlModifier):
            Mainframe.model.board.drop(self.id)
            Mainframe.model.onBoardChanged()
            Mainframe.sigWrapper.sigModelChanged.emit()

        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        dropAction = drag.exec_(QtCore.Qt.MoveAction)
        Mainframe.currentlyDragged = None

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        # Import Mainframe locally to avoid circular import
        from gui import Mainframe
        
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

        if Mainframe.currentlyDragged is None:
            return
        Mainframe.model.board.add(
            model.Piece(
                Mainframe.currentlyDragged.name,
                Mainframe.currentlyDragged.color,
                Mainframe.currentlyDragged.specs),
            self.id)
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()
