import traceback

import hou

from ..MSImporter import MSImporter


class BridgeCommandRunner:
    def __init__(self, queue_dir):
        self.queue_dir = queue_dir

    def run(self, command_payload):
        command = command_payload.get("command")
        args = command_payload.get("args", {}) or {}

        if command == "ping":
            return {
                "status": "ok",
                "result": {
                    "message": "pong",
                    "houdini": True,
                    "version": hou.applicationVersionString(),
                },
            }

        if command == "get_scene_info":
            hip_path = ""
            try:
                hip_path = hou.hipFile.path()
            except Exception:
                hip_path = ""

            return {
                "status": "ok",
                "result": {
                    "hip": hip_path,
                    "fps": hou.fps(),
                    "selected_nodes": [node.path() for node in hou.selectedNodes()],
                },
            }

        if command == "create_node":
            parent_path = args["parent_path"]
            node_type = args["node_type"]
            node_name = args.get("node_name")

            parent = hou.node(parent_path)
            if parent is None:
                raise RuntimeError("Parent node does not exist: {0}".format(parent_path))

            node = parent.createNode(node_type, node_name) if node_name else parent.createNode(node_type)
            node.moveToGoodPosition()
            return {"status": "ok", "result": {"path": node.path(), "type": node.type().name()}}

        if command == "set_param":
            node_path = args["node_path"]
            parm_name = args["parm_name"]
            value = args["value"]

            node = hou.node(node_path)
            if node is None:
                raise RuntimeError("Node does not exist: {0}".format(node_path))

            parm = node.parm(parm_name)
            if parm is None:
                raise RuntimeError("Parameter does not exist: {0}".format(parm_name))

            parm.set(value)
            return {"status": "ok", "result": {"node_path": node_path, "parm_name": parm_name}}

        if command == "import_megascans_asset":
            asset_data = args.get("asset")
            if asset_data is None:
                raise RuntimeError("Missing args.asset payload")

            importer = MSImporter.getInstance()
            result = importer.importAsset(asset_data)
            return {"status": "ok", "result": result}

        raise RuntimeError("Unsupported command: {0}".format(command))

    def run_safe(self, command_payload):
        request_id = command_payload.get("request_id")
        try:
            result = self.run(command_payload)
            result["request_id"] = request_id
            return result
        except Exception as exc:
            return {
                "status": "error",
                "request_id": request_id,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
