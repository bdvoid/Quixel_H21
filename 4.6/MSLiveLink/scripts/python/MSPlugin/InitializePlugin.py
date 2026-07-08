from .Bridge.Controller import BridgeController
from .MSImporter import MSImporter
from .SocketListener import QLiveLinkMonitor


def ensureLiveLinkMonitor():
    if len(QLiveLinkMonitor.Instance) == 0:
        bridge_monitor = QLiveLinkMonitor()
        bridge_monitor.Bridge_Call.connect(MSImporter.getInstance().importController)
        bridge_monitor.start()


def ensureBridgeController():
    BridgeController.getInstance().start()


def initializePlugin(start_ui=False):
    ensureLiveLinkMonitor()
    ensureBridgeController()
