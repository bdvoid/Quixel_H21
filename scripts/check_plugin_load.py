import json
import os
import sys


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "4.6", "MSLiveLink")
PYTHON_ROOT = os.path.join(PLUGIN_ROOT, "scripts", "python")

if PYTHON_ROOT not in sys.path:
    sys.path.insert(0, PYTHON_ROOT)

os.environ.setdefault("MS_HOUDINI_PATH", os.path.join(REPO_ROOT, ".tmp", "ms_settings"))
os.environ.setdefault("MS_HOUDINI_BRIDGE_QUEUE_DIR", os.path.join(REPO_ROOT, ".tmp", "bridge_queue"))

from MSPlugin.InitializePlugin import initializePlugin
from MSPlugin.Bridge.Controller import BridgeController
from MSPlugin.Bridge.CommandRunner import BridgeCommandRunner
from MSPlugin.MaterialsSetup.MaterialsCreator import MaterialsCreator
from MSPlugin.MSImporter import MSImporter
from MSPlugin.Utilities.SettingsManager import SettingsManager


def assert_ok(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    import hou

    initializePlugin(start_ui=False)

    settings = SettingsManager().getSettings()
    assert_ok("UI" in settings and "USDOptions" in settings["UI"], "settings missing migrated UI/USDOptions")

    snapshot = MaterialsCreator().getRegistrationSnapshot()
    assert_ok("Mantra" in snapshot, "Mantra materials not registered")
    assert_ok("Karma" in snapshot, "Karma materials not registered")
    assert_ok("Redshift" in snapshot, "Redshift materials not registered")

    runner = BridgeCommandRunner(os.environ["MS_HOUDINI_BRIDGE_QUEUE_DIR"])
    ping = runner.run_safe({"request_id": "ping-001", "command": "ping", "args": {}})
    assert_ok(ping["status"] == "ok", "bridge ping failed")

    controller = BridgeController.getInstance()
    queue_request_path = os.path.join(controller.inbox_dir, "queue-ping.json")
    with open(queue_request_path, "w", encoding="utf-8") as handle:
        json.dump({"request_id": "queue-ping-001", "command": "ping", "args": {}}, handle)
    controller.process_pending_requests()
    queue_result_path = os.path.join(controller.outbox_dir, "queue-ping-001.json")
    assert_ok(os.path.isfile(queue_result_path), "queue bridge did not write ping result")
    with open(queue_result_path, "r", encoding="utf-8") as handle:
        queue_ping = json.load(handle)
    assert_ok(queue_ping["status"] == "ok", "queue bridge ping failed")

    importer = MSImporter.getInstance()
    dummy_surface = {
        "guid": "smoke-guid-001",
        "id": "smoke-asset-001",
        "name": "smoke_surface",
        "type": "surface",
        "meta": [{"key": "height", "value": "0.02 m"}],
        "components": [
            {"type": "albedo", "path": "C:/tmp/albedo.jpg"},
            {"type": "roughness", "path": "C:/tmp/roughness.jpg"},
            {"type": "displacement", "path": "C:/tmp/displacement.exr"},
        ],
    }

    classic_settings = json.loads(json.dumps(settings))
    classic_settings["UI"]["ImportOptions"]["EnableUSD"] = False
    classic_settings["UI"]["ImportOptions"]["Renderer"] = "Mantra"
    classic_settings["UI"]["ImportOptions"]["Material"] = "Principled Shader"
    classic_surface = importer.importAsset(dummy_surface, classic_settings)
    assert_ok(classic_surface is not None, "classic surface import returned None")

    usd_settings = json.loads(json.dumps(settings))
    usd_settings["UI"]["ImportOptions"]["EnableUSD"] = True
    usd_settings["UI"]["USDOptions"]["USDMaterial"] = "Karma"
    usd_surface = importer.importAsset(dummy_surface, usd_settings)
    assert_ok(usd_surface is not None, "USD Karma surface import returned None")

    obj = hou.node("/obj")
    geo_name = "ms_bridge_smoke"
    if hou.node("/obj/" + geo_name) is not None:
        hou.node("/obj/" + geo_name).destroy()

    create_result = runner.run_safe(
        {
            "request_id": "create-001",
            "command": "create_node",
            "args": {"parent_path": "/obj", "node_type": "geo", "node_name": geo_name},
        }
    )
    assert_ok(create_result["status"] == "ok", "bridge create_node failed")

    set_result = runner.run_safe(
        {
            "request_id": "set-001",
            "command": "set_param",
            "args": {"node_path": "/obj/" + geo_name, "parm_name": "shop_materialpath", "value": "/mat/test"},
        }
    )
    assert_ok(set_result["status"] == "ok", "bridge set_param failed")

    print(
        json.dumps(
            {
                "settings_ok": True,
                "registered_renderers": sorted(snapshot.keys()),
                "ping": ping,
                "queue_ping": queue_ping,
                "classic_surface_path": classic_surface.path(),
                "usd_surface_path": usd_surface.path(),
                "create_node": create_result,
                "set_param": set_result,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
