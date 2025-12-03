from PySide6.QtCore import Slot
import json, sys
from .Utilities.AssetData import *
from .AssetImporters.Import3D import Import3DAsset
from .AssetImporters.ImportSurface import ImportSurface
from .AssetImporters.ImportPlant import ImportPlant

from .Utilities.SettingsManager import SettingsManager
from .Utilities.AtlasSplitter import AtlasSplitter
from .Utilities.MSAnalytics import MSAnalytics

import hou

class MSImporter:
    
    HOUDINI_PLUGIN_VERSION  = "4.6"
    
    assetImporters = {}
    __instance = None
    def __init__(self):
        if MSImporter.__instance != None:
            return
        MSImporter.__instance = self

    @Slot(str)
    def importController(self, jsondata):
        assetsdata = json.loads(jsondata)    
        importOptions = SettingsManager().getSettings()
        
        for assetData in assetsdata:

            if ("darwin" not in sys.platform.lower()):
                MSAnalytics(importOptions, assetData, MSImporter.HOUDINI_PLUGIN_VERSION).sendAnalytics()
                            
            importParams = getImportParams(assetData, importOptions)

            asset_type = assetData.get("type", "")
            if asset_type == "3d":       
                import3d = Import3DAsset()
                import3d.importAsset(assetData, importOptions, importParams)

            elif asset_type in ("surface", "brush", "decal"):
                importsurface = ImportSurface()
                importsurface.importAsset(assetData, importOptions, importParams)

            elif asset_type == "3dplant":
                ImportPlant().importAsset(assetData, importOptions, importParams)

            ##########################################
            #
            #      Modified section
            #
            ##########################################

            elif asset_type == "atlas":
                # Use .get(...) defensive access for nested dicts if you prefer; here we assume UI/ImportOptions exists.
                use_atlas_splitter = importOptions.get("UI", {}).get("ImportOptions", {}).get("UseAtlasSplitter", False)
                enable_usd = importOptions.get("UI", {}).get("ImportOptions", {}).get("EnableUSD", False)

                if not use_atlas_splitter and not enable_usd:
                    ImportSurface().importAsset(assetData, importOptions, importParams)

                elif enable_usd and not use_atlas_splitter:
                    ImportSurface().importAsset(assetData, importOptions, importParams)

                elif use_atlas_splitter and not enable_usd:
                    materialContainer = hou.node(importParams["assetPath"]).createNode("matnet", "Asset_Material")
                    importParams["materialPath"] = materialContainer.path()
                    atlasMaterial = ImportSurface().importAsset(assetData, importOptions, importParams)
                    AtlasSplitter().splitAtlas(assetData, importOptions, importParams, atlasMaterial.path())

                elif use_atlas_splitter and enable_usd:
                    materialContainer = hou.node(importParams["assetPath"]).createNode("matnet", "Asset_Material")
                    importParams["materialPath"] = materialContainer.path()
                    atlasMaterial = ImportSurface().importAsset(assetData, importOptions, importParams)
                    AtlasSplitter().splitAtlas(assetData, importOptions, importParams, atlasMaterial.path())

                else:
                    materialContainer = hou.node(importParams["assetPath"]).createNode("matnet", "Asset_Material")
                    importParams["materialPath"] = materialContainer.path()
                    atlasMaterial = ImportSurface().importAsset(assetData, importOptions, importParams)
                    AtlasSplitter().splitAtlas(assetData, importOptions, importParams, atlasMaterial.path())

    def registerAssetImporter(self, importerType, importer):
        MSImporter.assetImporters[importerType] = importer


        
    @staticmethod
    def getInstance():        
        if MSImporter.__instance == None:
            MSImporter()
        return MSImporter.__instance
