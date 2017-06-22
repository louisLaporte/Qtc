import curses
#import locale
#locale.setlocale(locale.LC_ALL, '')

from PyQt5.QtCore import (QObject,
                            pyqtSlot,
                            pyqtSignal,
                            QTimerEvent,
                            QEvent)
from event import *
from ctypes import WindowType, MouseButton
import core
from utils.log import *
from utils import colored_traceback

import sys
import re
import collections
from functools import wraps


def iterfy(iterable):
    if isinstance(iterable, str):
        iterable = [iterable]
    try:
        iter(iterable)
    except TypeError:
        iterable = [iterable]
    return iterable

def dec(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        try:
            return f(*args, **kwds)
        except KeyboardInterrupt:
            curses.endwin()
            sys.exit()
    return wrapper

class CWidget(QObject):

    windowTitleChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        DEBUG("{}".format(self))
        self.setObjectName(self.__class__.__name__)
        self.setParent(parent)
        # By default it is WindowType.Window if CWidget has no parent
        # else it is WindowType.Widget
        if parent is None:
            self.setWindowType(WindowType.Window)
        else:
            self.setWindowType(WindowType.Widget)

        self.setBoxed(False)
        self.setEnabled(True)
        self._visible = False
        self.setBaseSize(10, 10)
        self.setGeometry(0, 0, *self.baseSize)

    def __cursesRefresh(self):
        """
        """
        DEBUG("")
# >>> DEBUG
        if 1:
            ERROR("{} boxed {} geo {}| parent {} ".format(self.objectName(),
                                                        self.boxed,
                                                        self.geometry,
                                                        self.parent().objectName()))
            pos = tuple(reversed(self._win.getparyx()))
            size = tuple(reversed(self._win.getmaxyx()))
            DEBUG("curses: x {} y {} w {} h {}".format(*(pos + size)))

        if self.parent() is core.CApplication.instance():
            return
        if self.isVisible():
            if self.boxed:
                self.__cursesDrawWindow()
                self._win.noutrefresh()

            if self.windowTitle() != None:
                self.__cursesTitleWindow()
            if isinstance(self, CMenu):
                self.__cursesTitleWidget()
        self._win.noutrefresh()

        self.parent()._CWidget__cursesRefresh()

    def __cursesDrawWindow(self):
        side_char                = '│' # '|'
        line_char                = '─' # '-'
        top_left_corner_char     = '┌' # '+'
        top_right_corner_char    = '┐' # '+'
        bottom_left_corner_char  = '└' # '+'
        bottom_right_corner_char = '┘' # '+'
        crossing_four_widget     = '╬' # '+'
        # top line
        self._win.addstr(0, 1, line_char * (self.width - 2))
        # bottom line
        self._win.addstr(self.height - 1, 1, line_char * (self.width - 2))

        for i in range(1, self.height - 1):
            # Left side
            self._win.addstr(i, 0, side_char)
            # Right side
            self._win.addstr(i, self.width - 1, side_char)

        # Top Left corner
        self._win.addstr(0, 0, top_left_corner_char)
        # Top Right corner
        self._win.addstr(0, self.width - 1, top_right_corner_char)
        ## Bottom Left corner
        self._win.addstr(self.height - 1, 0, bottom_left_corner_char)
        ## Bottom Right corner
        try:
            #NOTE:
            # If we try to wrap at the lower-right corner of a window,
            # we cannot move the cursor (since that wouldn't be legal)
            self._win.addstr(self.height - 1, self.width - 1, bottom_right_corner_char)
        except curses.error:
            pass

    def __cursesSetWindow(self):
        DEBUG("")
        # TODO: Must be change for newpad
        self._visible = True
        if self.parent() is core.CApplication.instance():
            self._win = curses.newwin(self.height, self.width, self.y, self.x)
            if (self.parent().children()[0] == self
                and not core.CApplication.instance().focusWidget()):
                self.setFocus()
        else:
            ERROR("self {} {}".format(self, self.geometry))
            ERROR("parent {} {}".format(self.parent(), self.parent().geometry))
            self._win = self.parent()._win.subwin(self.height, self.width,
                                                    self.y, self.x)
            # 2 lines below are default (test curses.A_BLINK)
            self._win.overwrite(self.parent()._win)
        self._win.immedok(True)
        self.__cursesRefresh()

    def __cursesHasWindow(self):
        DEBUG("{}".format(hasattr(self,'_win')))
        return hasattr(self, '_win')

    def __cursesWindow(self):
        DEBUG("")
        return self._win

    def __cursesClearWindow(self):
        DEBUG("")
        self._win.clear()
        self.__cursesRefresh()

    def __cursesMoveWindow(self):
        DEBUG("")
        self._win.mvwin(self.y, self.x)

    #CMenu
    def __cursesTitleWidget(self):
        DEBUG("")
        #TODO: This is not a good position for opt_key parsing
        # Maybe CAction can move this part of code
        opt_key_pos = str(self.title).find('&')
        if opt_key_pos != -1:
            opt_key = str(self.title)[opt_key_pos + 1]
            before = str(self.title)[:opt_key_pos]
            after = str(self.title)[opt_key_pos + 2:]
            self._win.addstr(1, 1, before)
            self._win.addstr(1, len(before) + 1, opt_key,
                                curses.A_REVERSE | curses.A_UNDERLINE | curses.A_BOLD)
            self._win.addstr(1, len(before) + len(opt_key) + 1, after)
        else:
            self._win.addstr(1, 1, self.title)

    #CMainWindow
    def __cursesTitleWindow(self):
        DEBUG("")
        self._win.noutrefresh()
        self._win.addstr(self.y,
                        self.width // 2 - len(self.window_title) // 2,
                        self.window_title)
        self._win.noutrefresh()

    def __cursesFindWindow(self, x, y):
        DEBUG("")
        #TODO: TEST FUNCTION
        if not self._win.enclose(y, x):
            return
        self._childAt = self
        for child in self.children():
            child.__cursesFindWindow(x, y)

    @property
    def geometry(self):
        return (self._x, self._y, self._w, self._h)

    def setGeometry(self, x, y, w, h):
        DEBUG("")
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def height(self):
        return self._h

    def setFixedHeight(self, h):
        self._h = h

    @property
    def width(self):
        return self._w

    def setFixedWidth(self, w):
        self._w = w

    @property
    def baseSize(self):
        return (self._basew, self._baseh)

    def setBaseSize(self, basew, baseh):
        DEBUG("")
        self._basew = basew
        self._baseh = baseh

    @property
    def size(self):
        DEBUG("")
        return (self._w, self._h)

    def setSize(self, w, h):
        DEBUG("")
        self._w = w
        self._h = h

    def setFixedSize(self, w, h):
        DEBUG("")
        self._w = w
        self._h = h

    def setMaximumSize(self, maxw, maxh):
        DEBUG("")
        self._maxw = maxw
        self._maxh = maxh

    def setMinimumSize(self, minw, minh):
        DEBUG("")
        self._minw = minw
        self._minh = minh

    def resize(self, w, h):
        DEBUG("")
        self._w = w
        self._h = h
        core.CApplication.instance().sendEvent(self, CResizeEvent())

    @property
    def pos(self):
        DEBUG("")
        """Property of move(x, y) setter."""
        return self._x , self._y

    def move(self, x, y):
        """Setter for pos property."""
        DEBUG("")
        self._x = x
        self._y = y
        self.__cursesMoveWindow()
        if self._visible:
            self.show()

    @property
    def font(self):
        DEBUG("")
        return self._font

    def setFont(self, font):
        DEBUG("")
        self._font = font

    def isWindow(self):
        DEBUG("")
        return True if self.windowType() == WindowType.Window else False

    def window(self):
        DEBUG("")
        #TODO: TEST
        # Must return the widget ancestor that has a window system frame
        if self is core.CApplication.instance():
            raise StopIteration

        if self.windowType() == WindowType.Window:
            return self
        self.parent().window()

    def setWindowType(self, window_type):
        DEBUG("")
        self.window_type = window_type
        if window_type is WindowType.Window:
            self.setParent(core.CApplication.instance())

    def windowType(self):
        DEBUG("")
        return self.window_type

    @pyqtSlot(str)
    def setWindowTitle(self, title):
        DEBUG("")

        if self.windowType() != WindowType.Window:
            raise TypeError
        self.window_title = title
# >>> DEBUG
        if 1:
            WARNING("{} ISVISIBLE {} TITLE {}".format(self.objectName(),
                                                        self.isVisible(),
                                                        self.windowTitle()))
        if self._visible:
            self.show()

    def windowTitle(self):
        DEBUG("")
        return self.window_title if hasattr(self, 'window_title') else None

    @property
    def layout(self):
        DEBUG("")
        return self._layout

    def setLayout(self, layout):
        DEBUG("")
        self._layout = layout

    @property
    def boxed(self):
        DEBUG("")
        return self._boxed

    @pyqtSlot(bool)
    def setBoxed(self, boxed):
        DEBUG("")
        self._boxed = boxed

    @pyqtSlot()
    def update(self, x=0, y=0, w=0, h=0):
        DEBUG("")
        #TODO: Update geometry inside Widget if update(x=..., y=...)
        # else update() the whole widget
        if x > 0 or y > 0 or w > 0 or h > 0: self.setGeometry(x, y, w, h)

    @pyqtSlot()
    def close(self): raise NotImplemented

    @pyqtSlot()
    def lower(self): raise NotImplemented

    @pyqtSlot()
    def raise_(self): raise NotImplemented

    @pyqtSlot()
    def repaint(self): raise NotImplemented

    @pyqtSlot(bool)
    def setDisabled(self, disable):
        self._enable = not disable

    @pyqtSlot(bool)
    def setEnabled(self, enable):
        DEBUG("")
        self._enable = enable

    def childAt(self, x, y):
        DEBUG("")
        self._childAt = self.__cursesFindWindow()
        return self._childAt

    def hasFocus(self):
        DEBUG("")
        return core.CApplication.instance().focusWidget() == self

    @pyqtSlot()
    def setFocus(self):
        DEBUG("")
        core.CApplication.instance()._focus_widget = self

    def isVisible(self):
        DEBUG("{}".format(self._visible))
        return self._visible

    @pyqtSlot(bool)
    def setVisible(self, visible):
        DEBUG("")
        self._visible = visible
        if self._visible:
            self.show()
        else:
            self.hide()

    @pyqtSlot()
    def hide(self):
        DEBUG("")
        self._visible = False
        self.setBoxed(False)
        self.update(*self.geometry)

        self.__cursesClearWindow()
        self._win.touchwin()

        for child in self.children():
            if isinstance(child, CWidget):
                core.CApplication.instance().sendEvent(child, CHideEvent())

    @pyqtSlot(bool)
    def setHidden(self, hidden):
        DEBUG("")
        self._visible = not hidden
        if self._visible:
            self.show()
        else:
            self.hide()

    @pyqtSlot()
    def show(self):
        """Show current widget and notify all widgets children to show"""
        DEBUG("")
        self._visible = True
        self.update(*self.geometry)

        if self.__cursesHasWindow():
            self.__cursesRefresh()
        else:
            self.__cursesSetWindow()
        self._win.touchwin()

        for child in self.children():
            if ((isinstance(child, CWidget) and child.isVisible())
                or not child.__cursesHasWindow()):
                child.show()
                core.CApplication.instance().sendEvent(child, CShowEvent())

    def customEvent(self, ev):
        #DEBUG("CSHOWEVENT {} | {}".format(ev.type(),self.objectName()))
        DEBUG("")
        if ev.type() == CShowEvent().type():
            self.showEvent(ev)
        elif ev.type() == CHideEvent().type():
            self.hideEvent(ev)
        elif ev.type() == CResizeEvent().type():
            self.resizeEvent(ev)

    def resizeEvent(self, event):
        self._win.clear()
        self.__cursesRefresh()

    def moveEvent(self, event): raise NotImplemented
    def hideEvent(self, event):
        DEBUG("{}".format(self))
        if not self.isVisible():
            self.hide()

    def showEvent(self, event):
        DEBUG("")
        #return
        if self.isVisible():
            #DEBUG("> {}".format(self.objectName()))
            self.show()

    def mousePressEvent(self, ev): raise NotImplemented
    def mouseReleaseEvent(self, ev): raise NotImplemented
    def mouseClickEvent(self, ev): raise NotImplemented
    def mouseDoubleClickEvent(self, ev): raise NotImplemented
    def mouseTripleClickEvent(self, ev): raise NotImplemented
    def focusInEvent(self, event): raise NotImplemented
    def focusOutEvent(self, event): raise NotImplemented

class CMainWindow(CWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        # This function update parent as core.CApplication.instance()
        self.setWindowType(WindowType.Window)
        self.setObjectName(self.__class__.__name__)
# >>> DEBUG
        if 1:
            DEBUG("parent {}".format(self.parent()))

        self.setGeometry(*core.CScreen.geometry())
        self.setBoxed(False)

    def setCentralWidget(self, widget):
        """ by default x is 0 and the width is the parent width """
        DEBUG("")
        widget.setParent(self)
        self._centralWidget = widget
        self._centralWidget.setBaseSize(self._centralWidget.parent().width,
                                         self._centralWidget.parent().height - 4)

        self._centralWidget.setGeometry(0, 3, *self._centralWidget.baseSize)
        self._centralWidget.setBoxed(True)

    def centralWidget(self):
        DEBUG("")
        if hasattr(self, '_centralWidget'):
            return self._centralWidget
        raise AttributeError

    def setMenuBar(self, menuBar):
        DEBUG("")
        if not isinstance(menuBar, CMenuBar):
            raise TypeError
        menuBar.setParent(self)
        self._menuBar = menuBar
        if menuBar.baseSize == menuBar.size:
            ERROR("")
            self._menuBar.setGeometry(self.x, self.y + 1, self.width, 3)
# >>> DEBUG
        if 1:
            DEBUG("MENU BAR CHILDREN ARE {}".format(menuBar.children()))
        self._menuBar.setBoxed(True)

    def menuBar(self):
        DEBUG("")
        if hasattr(self, '_menuBar'):
            return self._menuBar
        raise AttributeError

    def statusBar(self):
        if hasattr(self, '_statusBar'):
            return self._statusBar
        raise AttributeError

    def setStatusBar(self, statusBar):
        if not isinstance(statusBar, CStatusBar):
            raise TypeError
        statusBar.setParent(self)
        self._statusBar = statusBar
        if statusBar.baseSize == statusBar.size:
            ERROR("")
            self._statusBar.setGeometry(self.x, self.height - self._statusBar.height,
                                        self.width, 1)
        #self._statusBar.setBoxed(True)

    def addToolBar(self): raise NotImplemented

    def eventFilter(self, obj, ev):
        DEBUG("")
        return
        DEBUG("obj {} ev {}".format(obj, ev))

class CDesktopWidget(CWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

class CMenu(CWidget):
    def __init__(self, title=None, parent=None):
        super().__init__(parent=parent)

        self._title = title
        self.setBaseSize(len(title) + 2, 3)
        self.setGeometry(0, 0, *self.baseSize)
        self.setBoxed(True)
        self.menu = []
        self._length = 0

    @property
    def title(self):
        return self._title

    def clear(self):
        self.menu.clear()

    def addMenu(self, menu):
        # Y menu
        menu = iterfy(menu)
        for m in menu:
            if isinstance(m, str):
                m = CMenu(title=m)
            elif isinstance(m, CMenu):
                pass
            else:
                raise TypeError
            m.setParent(self)
            m.setGeometry(self.x, self.y + self._length, m.width, m.height)
            self.menu.append(m)
            self._length += m.width

class CMenuBar(CWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.menu = []
        self.setBaseSize(2, 2)
        self.setGeometry(0, 0, *self.baseSize)
        self.setBoxed(True)
        self._length = 0

    def addMenu(self, menu):
        # X menu
        menu = iterfy(menu)
        for m in menu:
            if isinstance(m, str):
                m = CMenu(title=m)
            elif isinstance(m, CMenu):
                pass
            else:
                raise TypeError
            m.setParent(self)
            m.setGeometry(self.x + self._length, self.y, m.width, m.height)
            self.menu.append(m)
            self._length += m.width
        #self.menu.append(menu)
# >>> DEBUG
        if 0:
            WARNING("MENU is {}".format(self.menu))
        #self.setGeometry(0, 0, self.width + menu.width, menu.height)
        # TODO: change to move(x, y)

    def clear(self):
        self.menu.clear()

class CStatusBar(CWidget):

    messageChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.setBaseSize(2, 2)
        self.setGeometry(0, 0, *self.baseSize)
        self._widgets = []
        self._message = None

    def addWidget(self, widget, stretch=0):
        widget.setParent(self)
        self._widgets.append(widget)

    def addPermanentWidget(self, widget, stretch = 0): raise NotImplemented

    def removeWidget(self, widget):
        self._widgets.remove(widget)

    def currentMessage(self):
        return self._message

    def insertWidget(self, index, widget, stretch=0):
        widget.setParent(self)
        self._widgets.insert(i, widget)

    def insertPermanentWidget(self, index, widget, stretch = 0): raise NotImplemented
    def isSizeGripEnabled(self): raise NotImplemented
    def setSizeGripEnabled(self, enable): raise NotImplemented

    @pyqtSlot()
    def clearMessage(self):
        self._message

    @pyqtSlot(str, int)
    def showMessage(self, message, timeout=0):
        self._message = message
        self._win.addstr(self.x, self.y, self._message)
        self._win.refresh()

    def paintEvent(self, event): raise NotImplemented
    def resizeEvent(self, event): raise NotImplemented
    #def showEvent(self, event): raise NotImplemented

#vim: foldmethod=indent
