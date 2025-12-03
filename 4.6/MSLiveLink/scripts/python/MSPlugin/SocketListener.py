from PySide6.QtCore import QThread, Signal
import time
import socket

from .MSImporter import MSImporter


class QLiveLinkMonitor(QThread):

    Bridge_Call = Signal(str)
    Instance = []

    def __init__(self):
        super().__init__()
        self.TotalData = b""
        QLiveLinkMonitor.Instance.append(self)
        self.socketPort = 13290

    def __del__(self):
        self.quit()
        self.wait()

    def stop(self):
        self.terminate()

    def run(self):

        time.sleep(0.025)

        try:
            host = 'localhost'
            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_.bind((host, self.socketPort))

            while True:
                socket_.listen(5)
                client, address = socket_.accept()

                data = client.recv(4096 * 2)

                if data != b"":
                    self.TotalData = b""
                    self.TotalData += data

                    while True:
                        data = client.recv(4096 * 2)
                        if data:
                            self.TotalData += data
                        else:
                            break

                    time.sleep(0.05)
                    self.Bridge_Call.emit(self.TotalData.decode("ascii"))
                    time.sleep(0.05)

        except Exception as e:
            print(f"Error connecting to socket at port {self.socketPort}: {e}")
