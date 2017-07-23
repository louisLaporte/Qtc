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
import event
from event import *

from ctypes import MouseAction, MouseButton
import types
import widgets
from utils.log import *
from utils import colored_traceback
import sys
import functools
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class Screen(object):
    def __init__(self):
        self.scr = curses.initscr()
        self.scr.keypad(True)
        self.scr.nodelay(1)
        self.scr.scrollok(True)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)

    def __setattr__(self, name, value):
        INFO("name {} value {}".format(name, value))
        return super().__setattr__(name, value)

    def __getattribute__(self, name):
        att = super().__getattribute__(name)

        if (isinstance(att, types.FunctionType) or isinstance(att, types.MethodType)):
            INFO("Screen {}".format(name))
        return att

    @staticmethod
    def update():
        """Refresh marked windows."""
        curses.doupdate()

    def exit(self):
        """Same as curses.wrapper finally."""
        self.scr.keypad(0)
        curses.echo()
        curses.nocbreak()
        #curses.curs_set(1)
        curses.endwin()

    def __getattr__(self, name):
        ERROR("{}".format(name))
        if hasattr(self, name):
            return getattr(self, name)
        else:
            raise AttributeError
            self.exit()

    @staticmethod
    def beep():
        curses.beep()

    @property
    def size(self):
        return tuple(reversed(self.scr.getmaxyx()))

    @property
    def geometry(self):
        pos = tuple(reversed(self.scr.getbegyx()))
        return pos + self.size

    def event_manager(self):
        self.event = self.scr.getch()

        if self.event == curses.ERR:
            return
        elif self.event == curses.KEY_RESIZE:
            # NOTE: Does not work with tmux virtual window split, only with
            # a single physical  window terminal
            DEBUG("RESIZE")
            return
        elif self.event == curses.KEY_MOUSE:
            try:
                id_, x, y, z, bstate = curses.getmouse()
            except curses.error:
                # Error are like right click or back wheel movment
                return
            else:
                it = 0
                val = 0
                button = None
                action = None
                attr = None
                # Find which button event comes from
                for i, b in enumerate(MouseButton):
                    if bstate & b.value:
                        button = b.name
                        val = int(b.value)
                        it = i
                        #WARNING("i= {} MOUSE KEY {} val {} = {}".format(i, b.name, val, bin(val)))
                        break
                else:
                    return
                # Find button action and send the appropriate event
                for action in MouseAction:
                    if ((val & bstate ) >> (it * 6)) == action.value:
                        attr = getattr(Type, "cMouseButton"+action.name)
                        return CMouseEvent(attr.value, QPoint(x, y), button)

        else:
            #DEBUG("\033[31;1m curses KEY {} \033[0m".format(self.event))
            return CKeyEvent(Type.cKeyPress.value, self.event)

class CApplication(QCoreApplication):

    focusChanged = pyqtSignal(widgets.CWidget, widgets.CWidget)

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        INFO("------------------------------------")
        self._stdscr = Screen()

        for event_type in event.Type:
            QEvent.registerEventType(getattr(event_type, 'value'))

        self._focus_widget = None

        #self.timer = self.startTimer(1000)
        self.notifier = QSocketNotifier(0, QSocketNotifier.Read)
        self.notifier.activated.connect(self.readyRead)

    #def exec_(self):
    #    try:
    #        super().exec_()
    #    except Exception as err:
    #        self._stdscr.exit()
    #        print(err)

    def beep(self):
        self._stdscr.beep()

    @pyqtSlot()
    def quit(self):
        """Quit application after restore curses cooked mode."""
        self.exit()

    def exit(self, return_code=0):
        """Exit application after restore curses cooked mode."""
        if self.notifier.isEnabled():
            self.notifier.setEnabled(False)
        super().exit(return_code)
        self._stdscr.exit(return_code)

    def focusWidget(self):
        return self._focus_widget

    def allWidgets(self):
        return self.findChildren(widgets.CWidget)

    @staticmethod
    def font(widget):
        return widget.font

    def topLevelAt(self, x, y):
        return self.top_level_widget

    def widgetAt(self, x, y):
        #DEBUG("x: {} y: {}".format(x, y))
        tmp_y = tmp_x = sys.maxsize
        widget = None
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
        """Read all input from keyboard and mouse.
        Note:
            This method call curses window.getch() so the whole window must be redrawn.
        """
        ret = self._stdscr.event_manager()
        if ret is None:
            return

        QCoreApplication.sendEvent(self, ret)
        for widget in self.allWidgets():
            if widget.isVisible():
                widget.show()
        Screen.update()

    def childEvent(self, ev):
        #DEBUG("")
        if 1:
            DEBUG("CHILD EVENT {} {}".format(ev.type(), ev))
        pass

    def timerEvent(self, ev):
        if 1:
            INFO("TIMER EVENT ev {}, self.timer {}".format(ev.timerId(), self.timer))
        if ev.timerId() != self.timer:
            return

    def customEvent(self, event):
        #DEBUG("\033[35;5m{} \033[0m".format(event))
        if event.type() == Type.cKeyPress.value:
            DEBUG("key press text {} | key {}".format(event.text(), event.key()))
        elif (event.type() == Type.cMouseButtonClicked.value ):#      or
              #event.type() == Type.cMouseButtonDoubleClicked.value or
              #event.type() == Type.cMouseButtonTripleClicked.value or
              #event.type() == Type.cMouseButtonPressed.value       or
              #event.type() == Type.cMouseButtonReleaseded.value):

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

    @property
    def size(self):
        return CApplication.instance()._stdscr.size

    @property
    def geometry(self):
        return CApplication.instance()._stdscr.geometry

class E(Exception): pass
class CAction(QObject):
    def __init__(self, text=None, parent=None):
        super().__init__(parent)

    def __getattribute__(self, name):
        INFO(name)
        if name == any(['setIcon', 'setIconText', 'menu', 'setCheckable']):
            raise E("This method can not be call")
