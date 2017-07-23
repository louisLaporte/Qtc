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

import types
import sys
import re
import abc
import collections
from functools import wraps
import inspect


def iterfy(iterable):
    if isinstance(iterable, str):
        iterable = [iterable]
    try:
        iter(iterable)
    except TypeError:
        iterable = [iterable]
    return iterable

class _Curses():
    def refresh(self):
        """Recursively mark current widget and his children to refresh but wait.
        """
        DEBUG("")
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

    def setWindow(self):
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

    def clearWindow(self):
        self._win.clear()
        self.__cursesRefresh()

    #CMenu
    def titleWidget(self):
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
    def titleWindow(self):
        DEBUG("")
        self._win.addstr(self.y,
                        self.width // 2 - len(self.window_title) // 2,
                        self.window_title)
        self._win.noutrefresh()

    def findWindow(self, x, y):
        DEBUG("")
        #TODO: TEST FUNCTION
        if not self._win.enclose(y, x):
            return
        self._childAt = self
        for child in self.children():
            child.__cursesFindWindow(x, y)

class _Window():

    side_char                = '│' # '|'
    line_char                = '─' # '-'
    top_left_corner_char     = '┌' # '+'
    top_right_corner_char    = '┐' # '+'
    bottom_left_corner_char  = '└' # '+'
    bottom_right_corner_char = '┘' # '+'
    crossing_four_widget     = '╬' # '+'

    def __init__(self, x=10, y=10, width=10, height=10, boxed=True):
        self._x, self._y = x, y
        self._w, self._h = width, height
        self.win = curses.newwin(height, width, y, x)
        self.win.noutrefresh()
        self.boxed = True

    def __getattr__(self, name):
        ERROR("Unknown attribute {}".format(name))
        core.CApplication.instance().exit(return_code=1)
        curses.endwin()

    def setGeometry(self, x, y, width, height):
        self.resize(width, height)
        self.move(x, y)

    def resize(self, width, height):
        self._w , self._h = width, height
        self.win.resize(height, width)
        self.win.noutrefresh()

    def update(self):
        if self.boxed: self.win.box()
        self.win.noutrefresh()

    def move(self, x, y):
        self._x, self._y = x, y
        self.win.mvwin(y, x)
        self.win.noutrefresh()

    def move_cursor(self, x, y):
        self.win.move(y, x)
        self.win.noutrefresh()

    def title(self, title):
        DEBUG("{} {} {}".format(title, self._y, self._w))
        self.win.addstr(self._y, self._w // 2 - len(title) // 2, title)
        self.win.noutrefresh()

    def box(self):
        self.win.addstr(0, 1, self.line_char*(self._w-2)) # top line
        self.win.addstr(self._h-1, 1, self.line_char*(self._w-2)) # bottom line

        for i in range(1, self._h-1):
            self.win.addstr(i, 0, self.side_char) # Left side
            self.win.addstr(i, self._w-1, self.side_char) # Right side

        self.win.addstr(0, 0, self.top_left_corner_char) # Top Left corner
        self.win.addstr(0, self._w-1, self.top_right_corner_char) # Top Right corner
        self.win.addstr(self._h-1, 0, self.bottom_left_corner_char) # Bottom Left corner
        try:
            #NOTE:
            # If we try to wrap at the lower-right corner of a window,
            # we cannot move the cursor (since that wouldn't be legal)
            self.win.addstr(self._h-1, self._w-1, self.bottom_right_corner_char) # Bottom Right corner
        except curses.error:
            pass

    def findChild(self, x, y):
        if not self.win.enclose(y, x): return
        return self

    def clear(self):
        self.win.clear()
        self.win.noutrefresh()

class CWidget(QObject):

    windowTitleChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        """When initialize a CWidget it is always enabled, not boxed(framed) and
        not visible. Moreover the attribute _win is created, it is a binding to 
        the class _Window, it must only be access in CApplication."""
        super().__init__(parent=parent)
        DEBUG("{}".format(self))
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
        self._win = _Window(*self.geometry)

    def __getattr__(self, name):
        WARNING("{} --> unknown attribute {}".format(self.objectName(), name))
        self.__dict__[name] = 0
        return 0

    def __getattribute__(self, name):
        """Reimplemented method for debugging purpose."""
        try:
            attr = super().__getattribute__(name)
        except Exception as err:
            ERROR("{}".format(err))
            raise AttributeError
            core.CApplication.instance().exit()
        else:
            if (isinstance(attr, types.FunctionType)
                or isinstance(attr, types.MethodType)):
                keys = inspect.getargspec(attr).args
                keys.remove('self')
                def wrapper(func):
                    def _(*args, **kwargs):
                        # TODO: This is where all self._win(...) method must be called
                        # they must have the same name (ex: move, resize, etc...)
                        #getattr(self._win, func)(*args, **kwargs)
                        val = locals()['args']
                        DEBUG("{} {} {}".format(self.objectName(), name, {k:v for k,v in zip(keys, val)}))
                        return func(*args, **kwargs)
                    return _
                return wrapper(attr)
            else:
                return attr

    @property
    def geometry(self):
        """This property return (x, y, width, height)"""
        return (self._x, self._y, self._w, self._h)

    def setGeometry(self, x, y, w, h):
        self._x , self._y = x, y
        self._w, self._h = w, h

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
        self._basew, self._baseh = basew, baseh

    @property
    def size(self):
        return (self._w, self._h)

    def setSize(self, w, h):
        self._w, self._h = w, h

    def setFixedSize(self, w, h):
        self._w, self._h = w, h

    def setMaximumSize(self, maxw, maxh):
        self._maxw, self._maxh = maxw, maxh

    def setMinimumSize(self, minw, minh):
        self._minw, self._minh = minw, minh

    def resize(self, w, h):
        self._w, self._h = w, h
        core.CApplication.instance().sendEvent(self, CResizeEvent())

    @property
    def pos(self):
        """Property of move(x, y)"""
        return (self._x , self._y)

    def move(self, x, y):
        self._x, self._y = x, y
        self._win.move(x, y)
        core.CApplication.instance().sendEvent(self, CMoveEvent())

    @property
    def font(self):
        return self._font

    def setFont(self, font):
        self._font = font

    def isWindow(self):
        return self.windowType() == WindowType.Window

    def window(self):
        #TODO: TEST
        # Must return the widget ancestor that has a window system frame
        if self is core.CApplication.instance():
            raise StopIteration

        if self.windowType() == WindowType.Window:
            return self
        self.parent().window()

    def setWindowType(self, window_type):
        """Setup the widget's WindowType. If WindowType is WindowType.Window
        the parent is automatically set to CApplication.instance().
        """
        self.window_type = window_type
        if window_type is WindowType.Window:
            self.setParent(core.CApplication.instance())

    def windowType(self):
        return self.window_type

    @pyqtSlot(str)
    def setWindowTitle(self, title):
        if self.windowType() != WindowType.Window:
            raise TypeError
        self.window_title = title
        # Ensure if show() is called before setWindowTitle() to display 
        # the widget's title
        if self.isVisible():
            core.CApplication.instance().sendEvent(self, CShowEvent())

    def windowTitle(self):
        return self.window_title if hasattr(self, 'window_title') else None

    def layout(self):
        return self._layout

    def setLayout(self, layout):
        self._layout = layout

    @property
    def boxed(self):
        return self._boxed

    @pyqtSlot(bool)
    def setBoxed(self, boxed):
        self._boxed = boxed

    @pyqtSlot()
    def update(self, x=0, y=0, w=0, h=0):
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
        self.setEnabled(not disable)

    @pyqtSlot(bool)
    def setEnabled(self, enable):
        self._enable = enable

    def childAt(self, x, y):
        #TODO: 
        self._childAt = self._win.findChild()
        return self._childAt

    def hasFocus(self):
        return core.CApplication.instance().focusWidget() == self

    @pyqtSlot()
    def setFocus(self):
        core.CApplication.instance()._focus_widget = self

    def isVisible(self):
        return self._visible

    @pyqtSlot(bool)
    def setVisible(self, visible):
        self._visible = visible
        for child in self.findChildren(CWidget):
            child.setVisible(visible)
        self.update(*self.geometry)
        self.setBoxed(visible)
        if visible:
            self._win.setGeometry(*self.geometry)
            self._win.update()
            title = self.windowTitle()
            if title:
                self._win.title(title)
        else:
            self._win.clear()

        if self.isWindow():
            core.CApplication.instance()._stdscr.update()

    @pyqtSlot()
    def hide(self):
        self.setVisible(False)

    @pyqtSlot(bool)
    def setHidden(self, hidden):
        self.setVisible(not hidden)

    @pyqtSlot()
    def show(self):
        """Show current widget and notify all widgets children to show."""
        self.setVisible(True)

    def customEvent(self, ev):
        WARNING("CSHOWEVENT {} | {}".format(ev.type(),self.objectName()))
        if ev.type() == CShowEvent().type():
            self.showEvent(ev)
        elif ev.type() == CHideEvent().type():
            self.hideEvent(ev)
        elif ev.type() == CResizeEvent().type():
            self.resizeEvent(ev)

    def resizeEvent(self, event):
        ...

    def moveEvent(self, event):
        ...

    def hideEvent(self, event):
        ...

    def showEvent(self, event):
        ...

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
        self.setObjectName('MainWindow')
        self.setGeometry(*core.CScreen().geometry)
        self.setBoxed(False)

    def setCentralWidget(self, widget):
        """ by default x is 0 and the width is the parent width """
        widget.setParent(self)
        self._centralWidget = widget
        self._centralWidget.setObjectName('centralWidget')
        self._centralWidget.setBaseSize(self._centralWidget.parent().width - 2,
                                         self._centralWidget.parent().height - 8)

        self._centralWidget.setGeometry(self.x + 1, 4, *self._centralWidget.baseSize)
        self._centralWidget.setBoxed(True)

    def centralWidget(self):
        if hasattr(self, '_centralWidget'):
            return self._centralWidget
        raise AttributeError

    def setMenuBar(self, menuBar):
        if not isinstance(menuBar, CMenuBar):
            raise TypeError
        menuBar.setParent(self)
        self._menuBar = menuBar
        self._menuBar.setObjectName('menuBar')
        self._menuBar.setBoxed(True)
        if menuBar.baseSize == menuBar.size:
            self._menuBar.setGeometry(self.x + 1, self.y + 1, self.width - 2, 3)

    def menuBar(self):
        if hasattr(self, '_menuBar'):
            return self._menuBar
        raise AttributeError

    def setStatusBar(self, statusBar):
        if not isinstance(statusBar, CStatusBar):
            raise TypeError
        statusBar.setParent(self)
        self._statusBar = statusBar
        self._statusBar.setObjectName('statusBar')
        self._statusBar.setBoxed(True)
        if statusBar.baseSize == statusBar.size:
            self._statusBar.setGeometry(self.x + 1, self.height - 4,
                                        self.width - 2, 3)

    def statusBar(self):
        if hasattr(self, '_statusBar'):
            return self._statusBar
        raise AttributeError

    def addToolBar(self): raise NotImplemented

    def eventFilter(self, obj, ev):
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


################################################################################
#                                   BUTTON
################################################################################
class CAbstractButton(CWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

class CPushButton(CAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

################################################################################
#                                   LAYOUT
################################################################################
class CLayoutItem(metaclass=abc.ABCMeta):
    def __init__(self, alignment=None):
        self._alignment = None

    @abc.abstractmethod
    def alignment(self):
        ...

    @abc.abstractmethod
    def controlTypes(self):
        ...

    @abc.abstractmethod
    def expandingDirections(self):
        ...

    @abc.abstractmethod
    def geometry(self):
        ...

    @abc.abstractmethod
    def hasHeightForWidth(self):
        ...

    @abc.abstractmethod
    def heightForWidth(self, w):
        ...

    @abc.abstractmethod
    def invalidate(self):
        ...

    @abc.abstractmethod
    def isEmpty(self):
        ...

    @abc.abstractmethod
    def layout(self):
        ...

    @abc.abstractmethod
    def maximumSize(self):
        ...

    @abc.abstractmethod
    def minimumHeightForWidth(self, w):
        ...

    @abc.abstractmethod
    def minimumSize(self):
        ...

    def setAlignment(self, alignment):
        ...

    @abc.abstractmethod
    def setGeometry(self):
        ...

    @abc.abstractmethod
    def sizeHint(self):
        ...

    @abc.abstractmethod
    def spacerItem(self):
        ...

    @abc.abstractmethod
    def widget(self):
        ...

class CLayout(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)


#vim: foldmethod=indent
