from .SingletonBase import Singleton
import os
import json

from six import with_metaclass


class SettingsManager(with_metaclass(Singleton)):
    DEFAULT_SETTINGS = {
        "UI": {
            "ImportOptions": {
                "Renderer": "Mantra",
                "Material": "Principled Shader",
                "UseScattering": False,
                "UseExrDisplacement": False,
                "UseAtlasSplitter": False,
                "EnableLods": False,
                "ApplyMotion": False,
                "EnableUSD": False,
                "ConvertToRAT": True,
            },
            "USDOptions": {
                "USDMaterial": "Karma",
                "RefPath3D": "/Megascans/_3D_Assets/",
                "RefPath3DPlant": "/Megascans/_3D_Plants/",
                "RefPathSurface": "/Megascans/Surfaces",
                "ImportLods": False,
            },
        },
        "Misc": {},
    }

    def __init_(self):
        pass

    def getSettings(self):
        self.settings = self.__loadSettings()
        return self.settings

    def __loadSettings(self):
        settingsFilePath = self.getSettingsPath()

        if settingsFilePath is None:
            return json.loads(json.dumps(self.DEFAULT_SETTINGS))

        try:
            with open(settingsFilePath, "r") as fl_:
                settings = json.load(fl_)
                settings, changed = self.migrateSettings(settings)
                if self.checkSettingsValidity(settings):
                    if changed:
                        self.saveSettings(settings)
                    return settings

                defaultSettings = self.createDefaultSettings(settingsFilePath)
                self.saveSettings(defaultSettings)
                return defaultSettings
        except Exception:
            print("Error reading json file")
            defaultSettings = self.createDefaultSettings(settingsFilePath)
            return defaultSettings

    def createDefaultSettings(self, settingsFilePath):
        defaultSettings = json.loads(json.dumps(self.DEFAULT_SETTINGS))
        try:
            with open(settingsFilePath, "w") as outfile:
                json.dump(defaultSettings, outfile)
        except Exception:
            pass
        return defaultSettings

    def getSettingsPath(self):
        settingsPath = self.getEnvironmentPath()
        if settingsPath is None:
            settingsFilename = "Settings.json"
            settingsPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            if os.access(settingsPath, os.W_OK):
                settingsFilePath = os.path.join(settingsPath, settingsFilename)
                if os.path.isfile(settingsFilePath):
                    if not os.access(settingsFilePath, os.W_OK):
                        return None
                    return settingsFilePath

                try:
                    settingsFile = open(settingsFilePath, "w+")
                    settingsFile.close()
                    return settingsFilePath
                except Exception:
                    return None

            return None

        return settingsPath

    def getEnvironmentPath(self):
        fileName = "Settings.json"
        savePath = os.getenv("MS_HOUDINI_PATH")

        if savePath is not None:
            settingsPath = os.path.join(savePath, fileName)
            if os.path.exists(savePath):
                if os.access(savePath, os.W_OK) is False:
                    return None

                if os.path.isfile(settingsPath):
                    if os.access(settingsPath, os.W_OK) is False:
                        return None
                    return settingsPath

                try:
                    settingsFile = open(settingsPath, "w+")
                    settingsFile.close()
                    return settingsPath
                except Exception:
                    return None

            try:
                os.makedirs(savePath)
                settingsFile = open(settingsPath, "w+")
                settingsFile.close()
                return settingsPath
            except Exception:
                return None

        return None

    def saveSettings(self, settings):
        try:
            self.settings = settings
            settingsFilePath = self.getSettingsPath()
            if settingsFilePath is None:
                return

            with open(settingsFilePath, "w") as outfile:
                json.dump(settings, outfile)
        except Exception:
            pass

    def updateSetting(self, setting_key, setting_value):
        pass

    def updateSettings(self, settings):
        pass

    def migrateSettings(self, settings):
        changed = False
        merged = json.loads(json.dumps(self.DEFAULT_SETTINGS))
        if not isinstance(settings, dict):
            return merged, True

        for section_name, section_value in settings.items():
            if isinstance(section_value, dict) and section_name in merged:
                merged[section_name].update(section_value)
            else:
                merged[section_name] = section_value

        ui_settings = merged.setdefault("UI", {})
        import_options = ui_settings.setdefault("ImportOptions", {})
        usd_options = ui_settings.setdefault("USDOptions", {})

        source_usd = settings.get("UI", {}).get("USDOptions", {})
        alias_pairs = {
            "3DrefPath": "RefPath3D",
            "3DPlantRefPath": "RefPath3DPlant",
            "SurfaceRefPath": "RefPathSurface",
            "RefPath3D": "RefPath3D",
            "RefPath3DPlant": "RefPath3DPlant",
            "RefPathSurface": "RefPathSurface",
        }
        for source_key, target_key in alias_pairs.items():
            if source_key in source_usd and usd_options.get(target_key) != source_usd[source_key]:
                usd_options[target_key] = source_usd[source_key]
                changed = True

        for section_name, defaults in self.DEFAULT_SETTINGS["UI"].items():
            target_section = ui_settings.setdefault(section_name, {})
            for key, value in defaults.items():
                if key not in target_section:
                    target_section[key] = value
                    changed = True

        if import_options.get("Renderer") == "Karma" and import_options.get("Material") == "Principled Shader":
            import_options["Material"] = "Karma"
            changed = True

        return merged, changed

    def checkSettingsValidity(self, settings):
        return (
            isinstance(settings, dict)
            and "UI" in settings
            and "ImportOptions" in settings["UI"]
            and "USDOptions" in settings["UI"]
        )
