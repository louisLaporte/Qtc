import curses
from PyQt5.QtCore import QEvent, QPoint
from ctypes import FocusReason, Key, MouseButton
from utils import *
import string
from enum import Enum
import time

class Type(Enum):
    cMouseButtonClicked       = QEvent.User + 1
    cMouseButtonPressed       = QEvent.User + 2
    cMouseButtonReleased      = QEvent.User + 3
    cMouseButtonDoubleClicked = QEvent.User + 4
    cMouseButtonTripleClicked = QEvent.User + 5
    cKeyPress                 = QEvent.User + 6
    cFocusIn                  = QEvent.User + 8
    cFocusout                 = QEvent.User + 9
    cEnter                    = QEvent.User + 10
    cLeave                    = QEvent.User + 11
    cMove                     = QEvent.User + 13
    cResize                   = QEvent.User + 14
    cShow                     = QEvent.User + 17
    cHide                     = QEvent.User + 18
    cClose                    = QEvent.User + 19
    cParentChange             = QEvent.User + 21
    cActivate                 = QEvent.User + 24
    cDeactivate               = QEvent.User + 25
#    cShowToParent             = QEvent.User + 26
    cWheel                    = QEvent.User + 31
    cWindowTitleChange        = QEvent.User + 33
#    cChildAdded               = QEvent.User + 68
#    cChildRemoved             = QEvent.User + 71

class CMouseEvent(QEvent):
    def __init__(self, type_, point, button):
        super().__init__(type_)
        self._x = point.x()
        self._y = point.x()
        self._button = button

    def globalX(self):
        return self._x

    def globalY(self):
        return self._y

    def button(self):
        return  self._button

class CInputEvent(QEvent):
    def __init__(self):
        super().__init__(QEvent.User + 3)

    def timestamp():
        return time.time()

class CKeyEvent(QEvent):
    def __init__(self, type_, key):
        super().__init__(type_)
        #DEBUG("KEY {}".format(key))
        self._key = None
        for k in Key:
            if key == k.value:
                self._key = k
                break

    def text(self):
        return self._key

    def key(self):
        if hasattr(self._key, 'value'):
            return self._key.value
        return self._key

class CShowEvent(QEvent):
    def __init__(self):
        super().__init__(Type.cShow.value)

class CHideEvent(QEvent):
    def __init__(self):
        super().__init__(Type.cHide.value)

class CMoveEvent(QEvent):
    def __init__(self):
        super().__init__(Type.cMove.value)

class CResizeEvent(QEvent):
    def __init__(self):
        super().__init__(Type.cResize.value)

class CFocusEvent(QEvent):
    def __init__(self, type_, reason=FocusReason.Other):
        super().__init__(type_)
        self._type = type_
        self._reason = reason

    def gotFocus(self):
        return True if self._type is Type.cFocusIn.value else False

    def lostFocus(self):
        return True if self._type is Type.cFocusOut.value else False

    def reason(self):
        return self._reason

class CFocusIn(CFocusEvent):
    def __init__(self):
        super().__init__(Type.cFocusIn.value)

class CFocusOut(CFocusEvent):
    def __init__(self):
        super().__init__(Type.cFocusOut.value)
