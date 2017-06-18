#!/usr/bin/env python3
import sys
import os
#sys.path.insert(0, os.path.dirname(__file__))

from core import CApplication, CAction
from widgets import CMainWindow, CWidget, CMenuBar, CMenu
from utils.log import *
from utils import colored_traceback
test_mainWindow    = 0
test_centralWidget = 1

class MainWindow(CMainWindow):
    def __init__(self):
        super().__init__()
        self.setMenuBar(CMenuBar())
        self.setCentralWidget(CWidget())

        self.menuBar().addMenu("&File")
        #self.menuBar().addMenu("Edit")
        #self.menuBar().addMenu("View")
        #self.menuBar().addMenu("Search")
        #self.menuBar().addMenu("Term&inal")
        #self.menuBar().addMenu(["Help", "Help2"])


def main():
    app = CApplication(sys.argv)
    mainWin = MainWindow()
    #widget = CWidget()
    #widget.show()
    mainWin.show()
    if test_mainWindow:
        mainWin = MainWindow()
        mainWin.setObjectName("mainWindow")

        mainWin.show()
        mainWin.setWindowTitle("|__Main Menu__|")

    #DEBUG("{}".format(app.allWidgets()))
    #DEBUG("{}".format(app.widgetAt(3,3)))

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
