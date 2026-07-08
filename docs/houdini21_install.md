# Houdini 21.0 Quixel + Bridge Install

1. Copy or clone this repo somewhere permanent.
2. Copy [Quixel.json](D:/HOU_TOOLS/Quixel_H21/4.6/MSLiveLink/Quixel.json) into `Documents/houdini21.0/packages/Quixel.json`.
3. Edit `MSLIVELINK_ROOT` in that package file so it points to your local `.../4.6/MSLiveLink` folder.
4. Launch Houdini `21.0.x`. The Megascans menu should appear, and the local queue bridge will auto-start from `scripts/456.py`.

## Queue Bridge

- Queue root defaults to `$HOUDINI_TEMP_DIR/ms_houdini_bridge`.
- Requests go into `inbox/*.json`.
- Results appear in `outbox/<request_id>.json`.

### Request shape

```json
{
  "request_id": "example-001",
  "command": "ping",
  "args": {}
}
```

### Supported commands

- `ping`
- `get_scene_info`
- `create_node`
- `set_param`
- `import_megascans_asset`

### `import_megascans_asset`

Pass the original Quixel asset payload under `args.asset`. The bridge routes it through the same repaired `MSImporter` path used by the socket-based Bridge export flow.
