#!/usr/bin/env python3
import unittest
from core import *
from widgets import *
from ctypes import *
import sys
import random

class SimpleCApplicationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = CApplication(sys.argv)

    def tearDown(self):
        self.app.exit()

    def test_default_allWidget_from_object(self):
        """ allWidget() return list is empty."""
        self.assertFalse(self.app.allWidgets())

    def test_default_allWidget_from_class_instance(self):
        """ allWidget() return list is empty."""
        self.assertFalse(CApplication.instance().allWidgets())

    def test_default_widgetAt(self):
        """Do not find a widget at a random point."""
        x, y = reversed(CApplication.instance()._stdscr.getmaxyx())
        for i in range(0, 10):
            with self.subTest(i=i):
                self.assertIsNone(self.app.widgetAt(
                    random.randint(0,x),
                    random.randint(0,y)),
                )
    @unittest.expectedFailure
    def test_default_widgetAt_failure(self):
        """Find a widget at a random point."""
        x, y = reversed(CApplication.instance()._stdscr.getmaxyx())
        for i in range(0, 10):
            with self.subTest(i=i):
                self.assertIsNotNone(self.app.widgetAt(
                    random.randint(0, x),
                    random.randint(0, y)),
                )

    def test_default_focusWidget(self):
        """Do not find focus on a widget."""
        self.assertIsNone(self.app.focusWidget(),)

    @unittest.expectedFailure
    def test_default_focusWidget_failure(self):
        """Find focus on a widget."""
        self.assertIsNotNone(self.app.focusWidget(),)

class SimpleCMainWindowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = CApplication(sys.argv)
        self.win = CMainWindow()
        #self.win.show()

    def tearDown(self):
        self.app.exit()

    def test_default_allWidget_len(self):
        """allWidgets() return  length is one."""
        self.assertEqual(len(self.app.allWidgets()), 1)

    def test_default_allWidget_is_CMainWindow(self):
        """allWidgets() return CMainWindow object."""
        self.assertIs(self.app.allWidgets()[0], self.win)

    def test_default_CMainWindow_geometry(self):
        """Default geometry is CScreen geometry."""
        self.assertEqual(self.win.geometry, core.CScreen().geometry)

    def test_default_CMainWindow_centralWidget(self):
        """centralWidget() raise AttributeError if no centralWidget exists."""
        self.assertRaises(AttributeError, self.win.centralWidget)

    def test_default_CMainWindow_statusBar(self):
        """statusBar() raise AttributeError if no statusBar exists."""
        self.assertRaises(AttributeError, self.win.statusBar)

    def test_default_CMainWindow_menuBar(self):
        """menuBar() raise AttributeError if no menuBar exists."""
        self.assertRaises(AttributeError, self.win.menuBar)

    def test_default_CMainWindow_type(self):
        """CMainWindow is a WindowType.Window"""
        self.assertEqual(self.win.windowType(), WindowType.Window)

    def test_default_CMainWindow_type(self):
        """CMainWindow is not WindowType.Widget"""
        self.assertNotEqual(self.win.windowType(), WindowType.Widget)

    def test_default_CMainWindow_isVisible(self):
        """CMainWindow is not visible by default"""
        self.assertFalse(self.win.isVisible())

    def test_CMainWindow_isVisible_when_show(self):
        """CMainWindow is visible when show() is called"""
        self.win.show()
        self.assertTrue(self.win.isVisible())

    def test_CMainWindow_isVisible_when_hide(self):
        """CMainWindow is not visible when hide is called"""
        self.win.show()
        self.win.hide()
        self.assertFalse(self.win.isVisible())

    def test_default_hasFocus(self):
        """CMainWindow does not have the focus by default when show"""
        self.win.show()
        self.assertFalse(self.win.hasFocus())

    def test_default_parent(self):
        """CMainWindow does not have by default parent"""
        self.assertIs(self.win.parent(), self.app.instance())

if __name__ == '__main__':
    f = open('result', 'w')
    test_application = unittest.TestLoader().loadTestsFromTestCase(SimpleCApplicationTestCase)
    test_mainwindow = unittest.TestLoader().loadTestsFromTestCase(SimpleCMainWindowTestCase)
    unittest.TextTestRunner(stream=f, verbosity=1).run(test_application)
    unittest.TextTestRunner(stream=f, verbosity=1).run(test_mainwindow)
    f.close()
