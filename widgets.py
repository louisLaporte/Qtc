import curses
#import locale
#locale.setlocale(locale.LC_ALL, '')

from event import *
from ctypes import WindowType, MouseButton
import core
from utils.log import *
from multimethods import multimethod
from utils import colored_traceback

import sys
import types
import re
import abc
import collections
from functools import wraps

from PyQt5.QtCore import (  Qt,
                            QObject,
                            pyqtSlot,
                            pyqtSignal,
                            QTimerEvent,
                            QEvent)

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
################################################################################
#                               Widget
################################################################################
class CWidgetData:
    windid              = None
    widget_attributes   = None
    window_flags        = None
    window_state        = None
    focus_policy        = None
    sizehint_forced     = None
    is_closing          = None
    in_show             = None
    in_set_window_state = None
    fstrut_dirty        = None
    context_menu_policy = None
    window_modality     = None
    in_destructor       = None
    unused              = None
    crect               = core.CRect()
    pal                 = None #QPalette
    fnt                 = None #QFont
    wrect               = core.CRect;

class __CWidget(core.CObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if not core.CApplication.instance():
            ERROR("Cannot create a CWidget without CApplication")
            sys.exit()

class CWidget(__CWidget):

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
        self.data =  CWidgetData()
        self.setBoxed(False)
        self.setEnabled(True)
        self._visible = False
        self.setBaseSize(10, 10)
        self.setGeometry(0, 0, *self.baseSize)
        self._win = _Window(*self.geometry)

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

    @multimethod(core.CSize)
    def setFixedSize(self, size):
        self._w, self._h = size.width(), size.height()

    @multimethod(int, int)
    def setFixedSize(self, w, h):
        self._w, self._h = w, h

    @property
    def minimized(self):
        """Whether this widget is minimized (iconified)

        This property is only relevant for windows.

        By default, this property is False.

        Access function:
        :func:`isMinimized()`

        :rtype: bool

        .. seealso:: showMinimized(), visible, show(), hide(), showNormal(), maximized
        """
        return self.isMinimized()

    def isMinimized(self):
        return self.data.window_state & Qt.WindowMinimized

    def showMinimized(self):
        """ Shows the widget minimized, as an icon.

        Calling this function only affects windows.

        .. seealso:: showNormal(), showMaximized(), show(), hide(), isVisible(),
        isMinimized()
        """
        isMin = self.isMinimized()
        if isMin and self.isVisible:
            return
        if not isMin:
            self.setWindowState((self.windowState() & ~Qt.WindowActive)
                                | Qt.WindowMinimized)
        self.setVisible(True)

    @property
    def maximized(self):
        """whether this widget is maximized

        This property is only relevant for windows.

        By default, this property is False.

        :rtype: bool

        .. seealso:: windowState(), showMaximized(), visible, show(), hide(),
        showNormal(), minimized
        """
        return self.isMaximized()

    def isMaximized(self):
        return self.data.window_state & Qt.WindowMaximized

    def windowState(self):
        """ Returns the current window state. The window state is a OR'ed
        combination of Qt.WindowState: Qt.WindowMinimized,
        Qt.WindowMaximized, Qt.WindowFullScreen, and Qt.WindowActive.

        .. seealso:: Qt.WindowState, setWindowState()
        """
        return Qt.WindowStates(self.data.window_state)

    def _overrideWindowState(self, new_state):
        # TODO: implement QWindowStateChangeEvent
        raise NotImplementedError

    def setWindowState(self, new_state):
        raise NotImplementedError
        old_state = self.window_state()
        if old_state == new_state:
            return

    @property
    def fullScreen(self):
        """whether the widget is shown in full screen mode

        A widget in full screen mode occupies the whole screen area and does not
        display window decorations, such as a title bar.

        By default, this property is False.

        :rtype: bool

        .. seealso:: windowState(), minimized, maximized
        """
        return self.isFullScreen()

    def isFullScreen(self):
        return self.data.window_state & Qt.WindowFullScreen

    def showFullScreen(self):
        """Shows the widget in full-screen mode.

        Calling this function only affects windows.

        To return from full-screen mode, call showNormal().

        .. seealso:: showNormal(), showMaximized(), show(), hide(), isVisible()

        """
        self.setWindowState(
            (self.windowState() & ~(Qt.WindowMinimized | Qt.WindowMaximized))
            | Qt.WindowFullScreen
        )
        self.setVisible(True)

    def showMaximized(self):
        """Shows the widget maximized.

        Calling this function only affects windows.

        .. seealso:: setWindowState(), showNormal(), showMinimized(),
        show(), hide(), isVisible()
        """
        self.setWindowState(
            (self.windowState() & ~(Qt.WindowMinimized | Qt.WindowFullScreen))
               | Qt.WindowMaximized
        )
        self.setVisible(True)

    def showNormal(self):
        """Restores the widget after it has been maximized or minimized.

        Calling this function only affects windows.

        .. seealso:: setWindowState(), showMinimized(), showMaximized(),
        show(), hide(), isVisible()
        """
        self.setWindowState(self.windowState() & ~(Qt.WindowMinimized
                                                 | Qt.WindowMaximized
                                                 | Qt.WindowFullScreen)
        )
        self.setVisible(True)

    def isEnabledTo(self, ancestor):
        """Returns \c true if this widget would become enabled if  ancestor is
        enabled; otherwise returns False.

        This is the case if neither the widget itself nor every parent up
        to but excluding ancestor has been explicitly disabled.

        isEnabledTo(0) returns false if this widget or any if its ancestors
        was explicitly disabled.

        The word ancestor here means a parent widget within the same window.

        Therefore isEnabledTo(0) stops at this widget's window, unlike
        isEnabled() which also takes parent windows into considerations.

        .. seealso:: setEnabled(), enabled
        """
        if not isinstance(ancestor, CWidget):
            raise TypeError("ancestor must be a CWidget")
        w = self
        while (not w.testAttribute(Qt.WA_ForceDisabled)
                and not w.isWindow()
                and w.parentWidget()
                and w.parentWidget() != ancestor):
            w = w.parentWidget()
        return not self.testAttribute(Qt.WA_ForceDisabled)

    def addAction(self, action):
        #TODO: implement CAction
        raise NotImplementedError

    def addActions(self, actions):
        #TODO: implement CAction
        raise NotImplementedError

    def insertAction(self, action_before, action_after):
        #TODO: implement CAction
        raise NotImplementedError

    def insertActions(self, actions_before, actions_after):
        #TODO: implement CAction
        raise NotImplementedError

    def removeAction(self, action):
        #TODO: implement CAction
        raise NotImplementedError

    def actions(self, action):
        #TODO: implement CAction
        raise NotImplementedError

    def setMinimumSize(self, minw, minh):
        self._minw, self._minh = minw, minh

    def setMaximumSize(self, maxw, maxh):
        self._maxw, self._maxh = maxw, maxh

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

    @multimethod(int, int)
    def childAt(self, x, y):
        #TODO: 
        self._childAt = self._win.findChild()
        return self._childAt

    @multimethod(core.CPoint)
    def childAt(self, point):
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

class CWidgetItem(): pass

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


class __CLayout(core.CObject):
    __metaclass__ = CLayoutItem
    def __init__(self, parent=None):
        super().__init__(parent=parent)

class CLayout(__CLayout):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if parent:
            parent.setLayout(self)

    def parentWidget(self):
        """parent = self.parent()"""
        parent = self.parent()
        if not self.topLevel:
            if parent:
                if not isinstance(parent, CLayout):
                    WARNING("A layout can only have another layout as a parent.")
                    return 0
                return parent.parentWidget()
            else:
                return 0
        else:
            parent

    def isEmpty(self):
        i = 0
        item = itemAt(i)
        while item:
            if not item.isEmpty():
                return False
            i += 1
            item = itemAt(i)
        return True

    def controlTypes(self):
        if self.count() == 0:
            return CSizePolicy.DefaultType
        _types = CSizePolicy.ControlTypes
        for i in reversed(self.count()):
            _types |= self.itemAt(i).controlTypes()
        return _types

    def setGeometry(self, x, y, w, h):
        self._rect = (x, y, w, h)

    @property
    def geometry(self):
        return self._rect

    def replaceWidget(self, from_, to, options=None):
        idx = -1
        item = 0
        for i in self.count():
            item = self.itemAt(i)
            if not item:
                continue
            if item.widget() and (options & Qt.FindChildrenRecursively):
                r = item.layout().replaceWidget(from_, to, options)
                if r:
                    return r
        if idx == -1:
            return 0
        self.addChildWidget(to)
        newitem = CWidgetItem(to)
        newitem.setAlignment(item.alignment())
        r = self.replaceAt(index, newitem)
        if not r:
            del newitem
        return r

    def count(self):
        ...

    def itemAt(self, index):
        ...

    def indexOf(self, widget):
        i = 0
        item = self.itemAt(i)
        while item:
            if item.widget() == widget:
                return i
            i += 1
            item = self.itemAt(i)
        return -1

    def invalidate(self):
        self._rect = CRect()
        self.update()

    def removeWidgetRecursively(layout_item, widget):
        li = layout_item
        w = widget
        lay = li.layout()
        i = 0
        if not lay:
            return False
        child = lay.itemAt(i)
        while (child):
            if child.widget() == w:
                item = lay.takeAt(i)
                del item
                lay.invalidate()
                return True
            elif self.removeWidgetRecursively(child, w):
                return True
            else:
                i += 1
                child = lay.itemAt(i)
        return False

    def _widgetEvent(self, event):
        raise NotImplemented

    def childEvent(self, event):
        raise NotImplemented

    def _totalHeightForWidth(self, width):
        w = widget
        raise NotImplemented

    def _totalMinimumSize(self):
        raise NotImplemented

    def _totalSizeHint(self):
        raise NotImplemented

    def _totalMaximumSize(self):
        raise NotImplemented

    def addChildLayout(self, layout):
        if layout.parent():
            WARNING("QLayout.addChildLayout: layout {} already has a parent"
                    .format(layout.objectName()))
            return
        layout.setParent(self)
        # TODO: use private class
        if self.parentWidget():
            pass
            # l->d_func()->reparentChildWidgets(mw);

    def _adoptLayout(self, layout):
        self.addChildLayout(layout)
        return not layout.parent()


class CSizePolicy:
    class ControlType(Enum):
        DefaultType = 0x00000001 # The default type, when none is specified.
        ButtonBox   = 0x00000002 # A QDialogButtonBox instance.
        CheckBox    = 0x00000004 # A QCheckBox instance.
        ComboBox    = 0x00000008 # A QComboBox instance.
        Frame       = 0x00000010 # A QFrame instance.
        GroupBox    = 0x00000020 # A QGroupBox instance.
        Label       = 0x00000040 # A QLabel instance.
        Line        = 0x00000080 # A QFrame instance with QFrame::HLine or QFrame::VLine.
        LineEdit    = 0x00000100 # A QLineEdit instance.
        PushButton  = 0x00000200 # A QPushButton instance.
        RadioButton = 0x00000400 # A QRadioButton instance.
        Slider      = 0x00000800 # A QAbstractSlider instance.
        SpinBox     = 0x00001000 # A QAbstractSpinBox instance.
        TabWidget   = 0x00002000 # A QTabWidget instance.
        ToolButton  = 0x00004000 # A QToolButton instance.

class CRect(): pass
class Cpoint(): pass
#vim: foldmethod=indent
