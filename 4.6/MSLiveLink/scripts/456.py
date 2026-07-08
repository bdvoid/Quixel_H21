try:
    from MSPlugin.InitializePlugin import initializePlugin

    initializePlugin(start_ui=False)
except Exception as exc:
    print("Megascans startup initialization failed: {0}".format(exc))
