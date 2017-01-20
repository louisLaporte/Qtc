import curses
import curses.ascii
from PyQt5.QtCore import (QCoreApplication,
                            QObject,
                            pyqtSlot,
                            pyqtSignal,
                            QTimerEvent,
                            QSocketNotifier,
                            QMetaType,
                            QEvent)
from PyQt5.QtWidgets import QAction
from event import *
from ctypes import MouseAction,  MouseButton

import widgets
import sys
sys.path.append('/home/louis/project')
from Qc.Extra import *
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class CApplication(QCoreApplication):
    focusChanged = pyqtSignal(widgets.CWidget, widgets.CWidget)
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.notifier = QSocketNotifier(0, QSocketNotifier.Read)
        self.notifier.activated.connect(self.readyRead)
# >>> DEBUG
        if 1:
            DEBUG("self: {} instance: {}".format(self, QCoreApplication.instance()))
        stdscr = curses.initscr()

        # convenience method
        def wrap(stdscr):
            return stdscr
        # 1
        self._stdscr = curses.wrapper(wrap)
        self._stdscr.keypad(True)
        self._stdscr.nodelay(True)
        self._stdscr.scrollok(True)

        # 2
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)

        self.__curses_event = -1

        QEvent.registerEventType(Type.cKeyPress.value)

        QEvent.registerEventType(Type.cMouseButtonClicked.value)
        QEvent.registerEventType(Type.cMouseButtonPressed.value)
        QEvent.registerEventType(Type.cMouseButtonReleased.value)
        QEvent.registerEventType(Type.cMouseButtonDoubleClicked.value)
        QEvent.registerEventType(Type.cMouseButtonTripleClicked.value)

        self.timer = self.startTimer(1000)
        self.i = 0
        self._focus_widget = 0

    def __cursesStdscr(self):
        return self._stdscr

    def __cursesStdscrRefresh(self):
        self._stdscr.refresh()

    def focusWidget(self):
        return self._focus_widget

    #@staticmethod
    def allWidgets(self):
        return widgets.CWidget._instances

    @staticmethod
    def font(widget):
        return widget.font

    def topLevelAt(self, x, y):
        return self.top_level_widget

    def widgetAt(self, x, y):
        tmp_y = tmp_x = sys.maxsize
        widget = 0
        for w in self.allWidgets():
            maxy = w.y + w.height
            maxx = w.x + w.width
            if ((w.x <= x <= maxx) and (w.y <= y <= maxy)
                and maxx <= tmp_x and maxy <= tmp_y):

                tmp_x = maxx
                tmp_y = maxy
                widget = w

        return widget

    @pyqtSlot()
    def readyRead(self):
        curses.doupdate()
        self._stdscr.refresh()
        INFO("STDSCR w,h: {}".format(tuple(reversed(self._stdscr.getmaxyx()))))
        self.__curses_event = self._stdscr.getch()

        if self.__curses_event == curses.ERR:
            return
        if self.__curses_event == curses.KEY_MOUSE:
            try:
                id_, x, y, z, bstate = curses.getmouse()
            except curses.error as err:
                # Error are like right click or back wheel movment
                return
            else:
                it = 0
                val = 0
                button = None
                action = None
                attr = None
                # Find which button it comes from
                for i, b in enumerate(MouseButton):
                    if bstate & b.value:
                        button = b.name
                        val = int(b.value)
                        it = i
                        WARNING("i= {} MOUSE KEY {} val {} = {}".format(i, b.name, val,bin(val)))
                        break
                # Find button action and send the appropriate event
                for a in MouseAction:
                    if ((val & bstate ) >> (it * 6)) == a.value:
                        attr = getattr(Type, "cMouseButton" + a.name)
                        break

                QCoreApplication.sendEvent(self, CMouseEvent(attr.value,
                                                             QPoint(x, y),
                                                             button))

        elif self.__curses_event == curses.KEY_RESIZE:
            ERROR("RESIZE")
        else:
            ERROR(" curses KEY {}".format(self.__curses_event))
            QCoreApplication.sendEvent(self, CKeyEvent(Type.cKeyPress.value,
                                                        self.__curses_event))

    def childEvent(self, ev):
# >>> DEBUG
        if 0:
            ERROR("CHILD EVENT {}".format(ev.type()))
        pass

    def timerEvent(self, ev):
# >>> DEBUG
        if 0:
            INFO("TIMER EVENT ev {}, self.timer {}".format(ev.timerId(), self.timer))
        if ev.timerId() != self.timer:
            return

    def customEvent(self, event):
        if event.type() == Type.cKeyPress.value:
            DEBUG("key press text {} | key {}".format(event.text(), event.key()))
        elif event.type() == Type.cMouseButtonClicked.value:
            DEBUG("Button {} | type {}".format(event.button(), event.type()))
        elif event.type() == Type.cMouseButtonPressed.value:
            DEBUG("Button {} | type {}".format(event.button(), event.type()))
        elif event.type() == Type.cMouseButtonReleased.value:
            DEBUG("Button {} | type {}".format(event.button(), event.type()))
        elif event.type() == Type.cMouseButtonDoubleClicked.value:
            DEBUG("Button {} | type {}".format(event.button(), event.type()))
        elif event.type() == Type.cMouseButtonTripleClicked.value:
            DEBUG("Button {} | type {}".format(event.button(), event.type()))

################################################################################
class CScreen(QObject):
    def __init__(self):
        super().__init__()

    @staticmethod
    def size():
        return tuple(reversed(CApplication.instance()._stdscr.getmaxyx()))

    @staticmethod
    def geometry():
        pos = tuple(reversed(CApplication.instance()._stdscr.getbegyx()))
        return pos + CScreen.size()

class E(Exception):pass
class CAction(QObject):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)

    def __getattribute__(self, name):
        INFO(name)

        if name == any(['setIcon', 'setIconText','menu', 'setCheckable']):
            raise E("This method can not be call")

