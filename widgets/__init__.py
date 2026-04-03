# -*- coding: utf-8 -*-

"""
Widgets package for Olive GUI application.

This package contains reusable UI components extracted from the main GUI module.
"""

from .plain_text_edit import PlainTextEdit
from .clickable_label import ClickableLabel
from .yes_no_dialog import YesNoDialog
from .yes_no_cancel_dialog import YesNoCancelDialog
from .draggable_label import DraggableLabel
from .draggable_label_with_hover_effect import DraggableLabelWithHoverEffect

__all__ = [
    'PlainTextEdit',
    'ClickableLabel', 
    'YesNoDialog',
    'YesNoCancelDialog',
    'DraggableLabel',
    'DraggableLabelWithHoverEffect'
]
