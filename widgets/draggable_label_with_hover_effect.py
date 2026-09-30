# -*- coding: utf-8 -*-

from .draggable_label import DraggableLabel


class DraggableLabelWithHoverEffect(DraggableLabel):

    def __init__(self, id):
        super(DraggableLabelWithHoverEffect, self).__init__(id)
        self.setMouseTracking(True)

    def enterEvent(self, a0):
        self.setStyleSheet('QLabel { background-color: #42bff4; }')

    def leaveEvent(self, a0):
        self.setStyleSheet('QLabel { background-color: #ffffff; }')
