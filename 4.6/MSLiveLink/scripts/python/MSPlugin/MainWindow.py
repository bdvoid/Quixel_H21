from PySide6 import QtGui, QtCore
from PySide6.QtWidgets import (
    QLabel,
    QWidget,
    QApplication,
    QVBoxLayout,
    QMainWindow
)

import hou

from .OptionsUI import UIOptions
from .USDUI import USDOptions
from .SocketListener import QLiveLinkMonitor
from .MSImporter import MSImporter
from .Utilities.AssetData import *
from .Utilities.SettingsManager import SettingsManager


def GetHostApp():
    """
    Houdini ana Qt penceresini bulur.
    PySide6 için değişiklik gerekmiyor.
    """
    try:
        mainWindow = hou.ui.mainQtWindow()
        while True:
            lastWin = mainWindow.parent()
            if lastWin:
                mainWindow = lastWin
            else:
                break
        return mainWindow
    except:
        return None


class MSMainWindow(QMainWindow):
    __instance = None  # Singleton

    def __init__(self):
        if MSMainWindow.__instance is not None:
            return
        else:
            MSMainWindow.__instance = self

        super(MSMainWindow, self).__init__(GetHostApp())

        self.settingsManager = SettingsManager()
        self.uiSettings = self.settingsManager.getSettings()

        self.SetupMainWindow()
        self.setWindowTitle(
            "MS Plugin " + MSImporter.HOUDINI_PLUGIN_VERSION + " - Houdini"
        )
        self.setFixedWidth(600)

    def getStylesheet(self):
        stylesheet_ = """
        QCheckBox { background: transparent; color: #E6E6E6; font-family: Source Sans Pro; font-size: 14px; }
        QCheckBox::indicator:hover { border: 2px solid #2B98F0; background-color: transparent; }
        QCheckBox::indicator:checked:hover { background-color: #2B98F0; border: 2px solid #73a5ce; }
        QCheckBox:indicator { color: #67696a; background-color: transparent; border: 2px solid #67696a;
        width: 14px; height: 14px; border-radius: 2px; }
        QCheckBox::indicator:checked { border: 2px solid #18191b;
        background-color: #2B98F0; color: #ffffff; }

        QComboBox { color: #FFFFFF; font-size: 14px; padding: 2px 2px 2px 8px; 
        font-family: Source Sans Pro; selection-background-color: #1d1e1f; background-color: #1d1e1f; }

        QListView { padding: 4px; }
        QListView::item { margin: 4px; }

        QComboBox:hover { color: #c9c9c9; selection-background-color: #232426; background-color: #232426; }
        """
        return stylesheet_

    def SetupMainWindow(self):
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        # Import Options UI
        self.optionsUI = UIOptions(
            self.uiSettings["UI"]["ImportOptions"], self.uiSettingsChanged
        )

        self.windowLayout = QVBoxLayout()
        self.mainWidget.setLayout(self.windowLayout)
        self.windowLayout.addWidget(self.optionsUI)

        # USD UI
        self.usdUI = USDOptions(
            self.uiSettings["UI"]["USDOptions"], self.uiSettingsChanged
        )
        self.windowLayout.addWidget(self.usdUI)

        if EnableUSD():
            self.usdUI.setEnabled(self.uiSettings["UI"]["ImportOptions"]["EnableUSD"])
            self.usdEnabled = self.uiSettings["UI"]["ImportOptions"]["EnableUSD"]

            # Hook USD checkbox
            self.optionsUI.usdCheck.stateChanged.connect(self.SettingsChanged)
        else:
            self.usdUI.setEnabled(False)
            self.setStyleSheet(" QWidget { background-color: #353535; } ")

    def SettingsChanged(self):
        self.usdEnabled = not self.usdEnabled
        self.usdUI.setEnabled(self.usdEnabled)

    @staticmethod
    def getInstance():
        if MSMainWindow.__instance is None:
            MSMainWindow()
        return MSMainWindow.__instance

    def uiSettingsChanged(self, settingsKey, uiSettings):
        self.uiSettings["UI"][settingsKey] = uiSettings
        self.settingsManager.saveSettings(self.uiSettings)


def initializeWindow():
    mWindow = MSMainWindow.getInstance()
    mWindow.show()

    # LiveLink socket listener start
    if len(QLiveLinkMonitor.Instance) == 0:
        bridge_monitor = QLiveLinkMonitor()
        bridge_monitor.Bridge_Call.connect(MSImporter.getInstance().importController)
        bridge_monitor.start()
