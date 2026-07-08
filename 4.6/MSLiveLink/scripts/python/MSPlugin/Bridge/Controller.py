import json
import os
import shutil
import time
import uuid

from PySide6 import QtCore

from .CommandRunner import BridgeCommandRunner


class BridgeController(QtCore.QObject):
    _instance = None

    def __init__(self):
        super().__init__()
        self.queue_dir = os.getenv(
            "MS_HOUDINI_BRIDGE_QUEUE_DIR",
            os.path.join(os.getenv("TEMP", os.getcwd()), "ms_houdini_bridge"),
        )
        self.inbox_dir = os.path.join(self.queue_dir, "inbox")
        self.outbox_dir = os.path.join(self.queue_dir, "outbox")
        self.processed_dir = os.path.join(self.queue_dir, "processed")
        self.failed_dir = os.path.join(self.queue_dir, "failed")
        self.runner = BridgeCommandRunner(self.queue_dir)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.process_pending_requests)

    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = BridgeController()
        return cls._instance

    def start(self):
        self._ensure_queue_dirs()
        if not self.timer.isActive():
            self.timer.start()

    def _ensure_queue_dirs(self):
        for path in (self.queue_dir, self.inbox_dir, self.outbox_dir, self.processed_dir, self.failed_dir):
            os.makedirs(path, exist_ok=True)

    def process_pending_requests(self):
        self._ensure_queue_dirs()
        for file_name in sorted(os.listdir(self.inbox_dir)):
            if not file_name.lower().endswith(".json"):
                continue

            request_path = os.path.join(self.inbox_dir, file_name)
            processing_path = request_path + ".processing"
            try:
                os.replace(request_path, processing_path)
            except OSError:
                continue

            self._process_request_file(processing_path)

    def _process_request_file(self, processing_path):
        payload = None
        try:
            with open(processing_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            payload.setdefault("request_id", payload.get("request_id") or str(uuid.uuid4()))
            payload.setdefault("timestamp", time.time())
            result = self.runner.run_safe(payload)
            self._write_result(result)
            shutil.move(processing_path, os.path.join(self.processed_dir, os.path.basename(processing_path).replace(".processing", "")))
        except Exception as exc:
            result = {
                "status": "error",
                "request_id": payload.get("request_id") if isinstance(payload, dict) else None,
                "error": str(exc),
            }
            self._write_result(result)
            shutil.move(processing_path, os.path.join(self.failed_dir, os.path.basename(processing_path).replace(".processing", "")))

    def _write_result(self, result):
        request_id = result.get("request_id") or str(uuid.uuid4())
        result_path = os.path.join(self.outbox_dir, "{0}.json".format(request_id))
        with open(result_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
